#!/usr/bin/env python3
"""Hold each product's margin floor even when CJ's prices move.

The flat 50% floor was retired 2026-08-04 (owner decision): prices are now set
per product by the demand model (optimise_prices.py -> build_price_book.py),
and each product's floor lives in config/price_book.json as `floor_margin_pct`
- the worst variant margin the book accepted, minus a drift buffer. The guard's
job is no longer to police a global number but to catch COST DRIFT against
whatever the book promised.

Prices were set against a snapshot of CJ product cost and freight. Both drift -
CJ posted two shipping price adjustment notices in one week - so a price that
cleared its floor at launch can quietly fall through it. This re-quotes every
active variant against live CJ data and reports, or fixes, any breach.

Cost model comes from config/pricing.py: product + duty + freight + Shopify
Payments (2.9% + $0.30). Duty is 20% on China-origin and 0% on US-warehouse
stock, which was already imported by the supplier. Freight is the cheapest
carrier whose upper transit bound still meets the published 5-12 business day
window, matching what the CJ connections are actually set to ship by.

    python config/margin_guard.py            # report only, exits 1 on a breach
    python config/margin_guard.py --apply    # also raise prices to clear the floor
    python config/margin_guard.py --margin 55  # override: one global floor

Report mode changes nothing, so it is safe to run unattended. --apply edits live
retail prices and should only run where that is intended.
"""
import json, os, re, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import (PCT, FLAT, DUTY_PCT, DUTY_PCT_US_WAREHOUSE, SALES_TAX_AVG,
                     RETURNS_RATE, landed, retail_round)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_DAYS = 12
LOG = os.path.join(ROOT, 'config', 'margin_guard_log.json')

# Drift the stress column models: one realistic repricing step, not a worst case.
# CJ product costs move a few percent at a time; freight moves in steps when
# carriers reprice, which happened twice in the week to 2026-07-30. Both are
# proportional - a flat freight adder punishes cheap-to-ship items absurdly (+$6
# on a $5 quote is +120%) and flags the whole catalogue, which is no signal at all.
# A variant that fails this is still compliant today; it just has no room, so it
# is the first thing to break.
STRESS_COST = 0.10
STRESS_FREIGHT = 0.15

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def _fee_rate():
    # Card fee is charged on the whole order, sales tax included.
    return PCT * (1 + SALES_TAX_AVG)


def floor_price(product, freight, duty_pct, floor):
    """Lowest price clearing `floor` margin. Mirrors pricing.min_price but takes
    the floor as an argument so a stricter target can be enforced."""
    return (landed(product, freight, duty_pct) + FLAT) / (1 - _fee_rate() - floor)


def margin_at(price, product, freight, duty_pct):
    cost = landed(product, freight, duty_pct) + _fee_rate() * price + FLAT
    return (price - cost) / price if price else 0.0


def live_cj_costs(skus):
    """sku -> (vid, cost) straight from CJ rather than any cached matrix, so a
    supplier price change is picked up.

    The SPU list is derived from the SKUs actually on the store - a CJ variant SKU
    is its 11-character parent SPU plus a suffix. Reading it from a checked-in
    matrix instead meant every newly added product came back "no CJ record" and
    was silently skipped by the floor check.
    """
    out = {}
    spus = {str(s)[:11] for s in skus if s}
    for spu in sorted(spus):
        r = cj_api.call('/product/query', {'productSku': spu})
        for v in ((r.get('data') or {}).get('variants') or []):
            sku = v.get('variantSku')
            raw = str(v.get('variantSellPrice') or '').split('-')[0]
            try:
                out[sku] = (v.get('vid'), float(raw))
            except ValueError:
                continue
    return out


with open(os.path.join(ROOT, 'config', 'carriers.json'), encoding='utf-8') as _fh:
    SELECTED_CARRIER = json.load(_fh)['carriers']

# Per-product floors from the price book. Clamped at 2% so a kit-only product
# (book floor can be near zero after the drift buffer) still alerts BEFORE it
# sells at an actual loss. Products absent from the book get DEFAULT_FLOOR.
FLOOR_MIN = 0.02
DEFAULT_FLOOR = 0.25
try:
    with open(os.path.join(ROOT, 'config', 'price_book.json'), encoding='utf-8') as _fh:
        _BOOK = json.load(_fh)
    BOOK_FLOOR = {pid: max(v.get('floor_margin_pct', DEFAULT_FLOOR * 100) / 100.0,
                           FLOOR_MIN)
                  for pid, v in _BOOK.items()}
except FileNotFoundError:
    BOOK_FLOOR = {}


def best_freight(vid, start, sku=''):
    """Freight for the carrier CJ will actually book.

    Pricing against the cheapest available carrier understates cost whenever a
    faster one was deliberately selected, which quietly inflates every margin.
    Falls back to the cheapest promise-compliant option only when the selected
    carrier is unavailable for that variant.
    """
    r = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    opts = r.get('data') or []
    inside = [o for o in opts if o.get('logisticPrice') is not None
              and upper_days(o.get('logisticAging')) <= MAX_DAYS]

    want = SELECTED_CARRIER.get(str(sku)[:11])
    for o in opts:
        if want and str(o.get('logisticName')).strip() == want:
            p = o.get('logisticPrice')
            if p and p > 0:
                return {'price': float(p), 'name': want, 'aging': o.get('logisticAging'),
                        'within_promise': bool(inside), 'estimated': False}

    price, name, aging, estimated = freight_floor.resolve(opts)
    return {'price': price, 'name': f'{name} (selected carrier unavailable)',
            'aging': aging, 'within_promise': bool(inside), 'estimated': estimated}


def main():
    apply_fix = '--apply' in sys.argv
    # --headroom prices against the stress case rather than today's quote, so a
    # variant still clears the floor after a routine CJ move instead of breaching
    # the moment anything shifts.
    headroom = '--headroom' in sys.argv
    override = None
    if '--margin' in sys.argv:
        override = float(sys.argv[sys.argv.index('--margin') + 1]) / 100.0

    src = (f'global {override:.0%}' if override is not None
           else f'price_book floors ({len(BOOK_FLOOR)} products)')
    print(f'Margin guard - {src}, carriers within {MAX_DAYS} days, '
          f'{"APPLY" if apply_fix else "report only"}\n')

    products = api('GET', 'products.json?limit=250&status=active')['products']
    costs = live_cj_costs([v.get('sku') for p in products for v in p['variants']])
    breaches, unresolved, thin, checked = [], [], [], 0

    for p in products:
        title = p['title']
        floor = override if override is not None else BOOK_FLOOR.get(
            str(p['id']), DEFAULT_FLOOR)
        rows = []
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            entry = costs.get(sku)
            if not entry:
                unresolved.append((title, v['title'], sku, 'no CJ record'))
                continue
            vid, cost = entry
            # Origin from the STOCK ROWS, never the SKU prefix. The CJBQ
            # heuristic quoted the CJCT-prefixed, US-warehoused Ball Launcher
            # from China, got no carriers, substituted a ~$21.50 estimate
            # against a real $11.00 domestic rate, and failed this job every
            # three hours on a breach that did not exist.
            start = freight_floor.origin_for(sku)
            duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
            fr = best_freight(vid, start, sku)
            if not fr:
                unresolved.append((title, v['title'], sku, 'no carrier'))
                continue
            checked += 1
            price = float(v['price'])
            need = floor_price(cost, fr['price'], duty, floor)
            if headroom:
                need = floor_price(cost * (1 + STRESS_COST),
                                   fr['price'] * (1 + STRESS_FREIGHT), duty, floor)
            m = margin_at(price, cost, fr['price'], duty) * 100
            # Headroom: how far freight can rise before this price breaches the
            # floor. The real exposure is not today's quote but tomorrow's.
            slack = price * (1 - PCT - floor) - cost * (1 + duty) - FLAT
            stress = margin_at(price, cost * (1 + STRESS_COST),
                               fr['price'] * (1 + STRESS_FREIGHT), duty) * 100
            rows.append((v, sku, cost, fr, price, need, m, slack, stress))
            if price < need - 0.005:
                breaches.append((p['id'], title, v, sku, cost, fr, price, need, m))
            elif stress < floor * 100:
                thin.append((title, str(v['title']), sku, price, m, stress, slack,
                             fr['price']))

        if rows:
            safe = title.encode('ascii', 'replace').decode()
            print(f'{safe}  (floor {floor:.0%})')
            for v, sku, cost, fr, price, need, m, slack, stress in rows:
                flag = '' if price >= need - 0.005 else f'  <-- needs ${need:.2f}'
                warn = '' if fr['within_promise'] else '  (no carrier in window)'
                zero = '  (freight quoted $0 - unverified)' if fr['price'] == 0 else ''
                print(f'   {str(v["title"])[:28]:30} ${price:<7.2f} cost ${cost:<6.2f} '
                      f'frt ${fr["price"]:<6.2f} {m:5.1f}%  stress {stress:5.1f}%  '
                      f'frt headroom ${slack:5.2f}{flag}{warn}{zero}')
            print()

    print(f'{checked} variants checked')
    for t, vt, sku, why in unresolved:
        print(f'  UNRESOLVED  {t[:30]:32} {str(vt)[:20]:22} {sku}  ({why})')

    if thin:
        print(f'\n{len(thin)} variant(s) compliant today but with no room - these '
              f'break first if CJ moves\n  (stress = cost +{STRESS_COST:.0%} and '
              f'freight +{STRESS_FREIGHT:.0%}):')
        for t, vt, sku, price, m, stress, slack, frt in sorted(thin, key=lambda r: r[5]):
            print(f'  {t[:32]:34} {vt[:18]:20} ${price:.2f}  now {m:.1f}%  '
                  f'stress {stress:.1f}%  freight headroom ${slack:.2f}')

    if not breaches:
        print('\nAll variants clear their floors.')
    else:
        print(f'\n{len(breaches)} variant(s) below their floor:')
        for pid, t, v, sku, cost, fr, price, need, m in breaches:
            print(f'  {t[:32]:34} {str(v["title"])[:20]:22} '
                  f'${price:.2f} -> ${retail_round(need):.2f}  ({m:.1f}%)')
        if apply_fix:
            print()
            # One product can hold several breaching variants; Shopify wants each
            # variant PUT separately.
            for pid, t, v, sku, cost, fr, price, need, m in breaches:
                new = retail_round(need)
                api('PUT', f'variants/{v["id"]}.json',
                    {'variant': {'id': v['id'], 'price': f'{new:.2f}'}})
                print(f'  raised {t[:30]:32} {str(v["title"])[:18]:20} '
                      f'${price:.2f} -> ${new:.2f}')
        else:
            print('\nRun with --apply to raise these to clear the floor.')

    with open(LOG, 'w', encoding='utf-8') as fh:
        json.dump({'ran_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                   'floor': override if override is not None else 'price_book',
                   'applied': apply_fix, 'checked': checked,
                   'breaches': [{'product': t, 'variant': str(v['title']),
                                 'sku': sku, 'price': price,
                                 'needed': round(need, 2), 'margin': round(m, 1)}
                                for _, t, v, sku, _, _, price, need, m in breaches],
                   'unresolved': [{'product': t, 'variant': str(vt), 'sku': s,
                                   'why': w} for t, vt, s, w in unresolved],
                   'thin': [{'product': t, 'variant': vt, 'sku': s, 'price': pr,
                             'margin': round(mg, 1), 'stress_margin': round(st, 1),
                             'freight_headroom': round(sl, 2), 'freight': fr}
                            for t, vt, s, pr, mg, st, sl, fr in thin]},
                  fh, indent=1)
    print(f'\nlog -> {os.path.relpath(LOG, ROOT)}')
    return 1 if (breaches and not apply_fix) else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(2)
