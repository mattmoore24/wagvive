#!/usr/bin/env python3
"""Nothing CJ refuses to carry may be orderable on the storefront.

The point of this guard is the one the owner asked for: scan continuously so a
product that cannot be fulfilled is never available to order. What changed on
2026-08-18 is the TEST, not the goal.

THE TEST THAT WAS WRONG. The first version treated an empty `stock` array from
/product/stock/queryBySku as proof CJ could not ship, and held ten variants
across five products at zero. CJ's own UI disproved it: the Bouncy Egg Squeaker,
the item blamed for order #1002, displays "Inventory: 46587 (CJ: 0, Factory:
46587)" with carrier "LuWei Ordinary US · Available" and 1 to 3 day processing.
The API agreed all along and I misread it: those products return status 3, carry
48 to 86 other sellers' listings, and quote 27 carrier options each, while CJ
flags no line of #1002 abnormal and its Abnormal Orders tab reads 0.

THE TEST NOW. Ask CJ to quote carriage for the actual variant, and require at
least one carrier inside the delivery promise. That is the same question
fulfilment asks, so a failure here is a real inability to ship rather than an
inference from a field whose meaning we guessed at. It is also what the
storefront promise depends on: a carrier that misses 12 business days is no
better than no carrier.

NEVER ACT ON A SINGLE BAD ANSWER. Quotes are retried, and a SKU CJ will not
answer for is UNKNOWN and left alone. An earlier sweep returned empty rows for
seven healthy SKUs at once, including live kit components; zeroing on that would
have taken good products, and their kits, offline.

    python config/guard_unshippable.py            # report
    python config/guard_unshippable.py --apply    # zero anything unfulfillable
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                            # noqa: E402
import freight_floor                                    # noqa: E402
from freight_floor import upper_days                     # noqa: E402

MAX_DAYS = 12                       # the promise made site-wide and in email
LOCATION_ID = 113363058977          # Shop location: the only one that can sell

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
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')


def api(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data,
        method=method, headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read().decode()
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def cj_vids():
    """{variant sku: vid} for the catalogue, from CJ's product records."""
    out = {}
    prods = api('products.json?limit=250&status=active')['products']
    spus = {v['sku'][:11] for p in prods for v in p['variants'] if v.get('sku')}
    for spu in sorted(spus):
        try:
            d = cj_api.call('/product/query', {'productSku': spu}) or {}
            data = d.get('data')
            if isinstance(data, list):
                data = data[0] if data else {}
            for cv in ((data or {}).get('variants') or []):
                out[cv.get('variantSku')] = cv.get('vid')
        except Exception:
            pass
        time.sleep(0.25)
    return out


def carriers(vid, sku, tries=3):
    """(options inside the promise, reachable). Retried before it is believed."""
    # Origin from the stock rows, not the SKU prefix: a US-warehoused item
    # quoted from China returns no carrier at all and reads as unshippable.
    start = freight_floor.origin_for(sku)
    for attempt in range(tries):
        try:
            r = cj_api.call('/logistic/freightCalculate', payload={
                'startCountryCode': start, 'endCountryCode': 'US',
                'products': [{'quantity': 1, 'vid': vid}]})
            opts = r.get('data')
            if isinstance(opts, list) and opts:
                inside = [o for o in opts if o.get('logisticPrice') is not None
                          and upper_days(o.get('logisticAging')) <= MAX_DAYS]
                return inside, True
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return [], False


def storefront(handles):
    out = {}
    for h in sorted(handles):
        url = f'https://{SHOP}/products/{h}.js?nocache={int(time.time()*1000)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            out[h] = {v['id']: v['available'] for v in d['variants']}
        except Exception as e:
            out[h] = {'error': str(e)}
        time.sleep(0.3)
    return out


def main():
    apply = '--apply' in sys.argv
    prods = api('products.json?limit=250&status=active')['products']
    singles = [p for p in prods
               if p.get('product_type') not in ('Bundles & Kits', 'Kit Bundle')]
    vids = cj_vids()

    bad, unknown, checked = [], [], 0
    for p in sorted(singles, key=lambda x: x['title']):
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            checked += 1
            vid = vids.get(sku)
            if not vid:
                unknown.append((p['title'], v['title'], sku, 'no CJ vid'))
                continue
            inside, reachable = carriers(vid, sku)
            if not reachable:
                unknown.append((p['title'], v['title'], sku, 'CJ did not answer'))
                continue
            if not inside:
                bad.append({'product': p['title'], 'handle': p['handle'],
                            'variant': v['title'], 'sku': sku,
                            'variant_id': v['id'],
                            'item_id': v['inventory_item_id'],
                            'qty': v['inventory_quantity']})

    print(f'{checked} SKU-carrying variant(s) checked against a live CJ freight '
          f'quote, {MAX_DAYS} business day ceiling')
    if unknown:
        print(f'\n{len(unknown)} UNKNOWN, left untouched on purpose:')
        for t, vt, s, why in unknown:
            print(f'  ? {t} / {vt}  {s}  ({why})')

    if not bad:
        print('\nEvery variant has a carrier inside the promise.')
        return 0

    on_sale = [b for b in bad if b['qty'] > 0]
    print(f'\n{len(bad)} variant(s) have NO carrier inside {MAX_DAYS} days. '
          f'{len(on_sale)} still carry stock:')
    for b in bad:
        print(f"  {'!!' if b['qty'] > 0 else '  '} {b['product']} / "
              f"{b['variant']}  {b['sku']}  qty={b['qty']}")

    if on_sale and apply:
        for b in on_sale:
            api('inventory_levels/set.json', 'POST',
                {'location_id': LOCATION_ID, 'inventory_item_id': b['item_id'],
                 'available': 0})
            print(f"  zeroed {b['sku']}")
    elif on_sale:
        print('\nRun with --apply to zero them.')

    print('\nstorefront check...')
    live = storefront({b['handle'] for b in bad})
    still = [b for b in bad
             if 'error' not in live.get(b['handle'], {})
             and live[b['handle']].get(b['variant_id'])]
    if still:
        print(f'\n{len(still)} UNFULFILLABLE VARIANT(S) ARE STILL ORDERABLE.')
        for b in still:
            print(f"  ! {b['product']} / {b['variant']}")
        return 1
    print('Nothing unfulfillable is orderable on the storefront.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
