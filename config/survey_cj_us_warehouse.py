#!/usr/bin/env python3
"""Which of our CJ products can ship from a US WAREHOUSE, and how fast?

This is the "can CJ be fixed rather than replaced" question, asked of CJ
instead of of an opinion. Two real orders sat 18 days without moving, which is
what triggered the supplier search - but the store already sells at least one
US-warehoused CJ product (the Automatic Ball Launcher, CJCT25677400001, whose
US origin is documented in freight_floor.py). If a decent share of the
catalogue can be served from US stock, CJ stops being a China-transit bet and
becomes a domestic supplier we already have built, paired, priced and imaged.

WHAT DECIDES IT (and why nothing else does):

  * `countryCode == 'US'` on a stock row means CJ physically holds units in a
    US warehouse. That is the same test `freight_floor.origin_for()` uses, and
    it is the ONLY reliable one - SKU prefixes are not. Ten scripts once
    guessed origin with `sku.startswith('CJBQ')` and misread the US-warehoused
    Ball Launcher as Chinese, quoting $21.50 against a real $11.00 domestic
    rate and failing the scheduled job every three hours for a day.
  * A US row with zero units is NOT a US supply line. Warehouse rows carry
    quantities; this reports them so a "US" answer backed by 0 units cannot be
    mistaken for one backed by 4,000.
  * Carrier aging is asked per variant, because "how many units exist" and
    "how fast can it get there" are different questions (the standing lesson
    behind guard_unshippable.py).

QUOTA SAFETY. CJ enforces a daily API POINTS budget on top of the 1 req/sec
throttle, and exhaustion arrives as an ordinary HTTP 200 carrying
`result: false, code: 16900500`. Every retry loop in this repo reads that as
"nothing found". A partial read under that condition once reported a margin of
53.4% where the true figure was 27.8%. So this script ABORTS the moment it
sees that code and prints what it had, clearly marked incomplete, rather than
publishing a number computed through a brownout.

    python config/survey_cj_us_warehouse.py
    python config/survey_cj_us_warehouse.py --json out.json
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                              # noqa: E402
import freight_floor                                       # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

QUOTA_CODE = 16900500


class QuotaExhausted(RuntimeError):
    """CJ's daily points budget ran out. Nothing read after this is trustworthy."""


def shopify(path):
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


def cj(path, params):
    """cj_api.call, but a points brownout raises instead of looking like 'empty'."""
    res = cj_api.call(path, params) or {}
    if str(res.get('code')) == str(QUOTA_CODE) or 'Insufficient API points' in str(res.get('message', '')):
        raise QuotaExhausted(res.get('message') or 'code 16900500')
    return res


def warehouses(sku):
    """[(countryCode, units)] for a SKU, one entry per warehouse row."""
    rows = cj('/product/stock/queryBySku', {'sku': sku}).get('data')
    out = []
    if isinstance(rows, list):
        for w in rows:
            cc = (w.get('countryCode') or '').upper() or '?'
            entries = w.get('stock') or []
            if entries:
                n = sum((s.get('inventory') or 0) + (s.get('factoryInventory') or 0)
                        for s in entries)
            else:
                n = int(w.get('totalInventoryNum') or 0)
            out.append((cc, n))
    return out


def us_carriers(sku):
    """Carriers CJ offers to a US address, as (name, price, aging, days)."""
    res = cj('/logistic/freightCalculate',
             {'startCountryCode': 'US', 'endCountryCode': 'US',
              'products': json.dumps([{'quantity': 1, 'sku': sku}]),
              'zip': '10001'})
    data = res.get('data') or []
    rows = []
    for o in data:
        if o.get('logisticPrice') is None:
            continue
        rows.append((str(o.get('logisticName')), float(o['logisticPrice']),
                     o.get('logisticAging'),
                     freight_floor.upper_days(o.get('logisticAging'))))
    return sorted(rows, key=lambda r: r[3])


def main():
    prods = shopify('products.json?limit=250&status=active')['products']

    # One question per SPU: a warehouse is a property of the PRODUCT.
    spus, incomplete = {}, False
    for p in prods:
        for v in p['variants']:
            sku = (v.get('sku') or '').strip()
            if sku:
                spus.setdefault(sku[:11], (p['title'], sku))
                break

    print(f'{len(prods)} live products, {len(spus)} distinct CJ SPUs\n')
    print(f"{'product':40}{'origin':8}{'warehouse rows':26}{'fastest US carrier':34}")
    print('-' * 108)

    results = []
    for spu, (title, sku) in sorted(spus.items(), key=lambda kv: kv[1][0]):
        try:
            wh = warehouses(sku)
            has_us = any(cc == 'US' and n > 0 for cc, n in wh)
            car = us_carriers(sku) if has_us else []
        except QuotaExhausted as e:
            print(f'\n!! CJ POINTS QUOTA EXHAUSTED: {e}')
            print('   STOPPING. Everything above is real; nothing below was read.')
            print('   Do not retry into this - wait an hour of light use, or resume tomorrow.')
            incomplete = True
            break

        origin = 'US' if has_us else 'CN'
        wtxt = ', '.join(f'{cc}:{n}' for cc, n in wh) or 'no rows'
        ctxt = (f'{car[0][0][:22]} {car[0][3]}d ${car[0][1]:.2f}'
                if car else ('-' if origin == 'CN' else 'none quoted'))
        print(f'{title[:38]:40}{origin:8}{wtxt[:24]:26}{ctxt[:32]:34}')
        results.append(dict(spu=spu, title=title, sku=sku, origin=origin,
                            warehouses=wh, carriers=car[:5]))

    us = [r for r in results if r['origin'] == 'US']
    print(f'\n{len(us)} of {len(results)} surveyed SPUs hold US warehouse stock')
    if us:
        fast = [r for r in us if r['carriers'] and r['carriers'][0][3] <= 7]
        print(f'{len(fast)} of those quote a US carrier delivering within 7 days')
        for r in us:
            c = r['carriers'][0] if r['carriers'] else None
            print(f"   {r['title'][:44]:46} "
                  f"{(c[0][:24] + f'  {c[3]}d  ${c[1]:.2f}') if c else 'no carrier quoted'}")
    if incomplete:
        print('\nINCOMPLETE RUN - the counts above cover only what was read.')

    if '--json' in sys.argv:
        path = sys.argv[sys.argv.index('--json') + 1]
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(dict(complete=not incomplete, results=results), fh, indent=1)
        print(f'\nwrote {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
