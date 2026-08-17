#!/usr/bin/env python3
"""Nothing CJ cannot ship may be orderable on the storefront. Enforced, not hoped.

Order #1002 (CJ DP2608121816000646700) sold a Bouncy Egg Squeaker inside the
Enrichment Kit that CJ then could not send. Every audit at the time passed,
because they all asked whether Shopify MATCHED CJ's number and never whether
that number meant shippable.

WHAT COUNTS AS UNSHIPPABLE, AND HOW SURE WE ARE

CJ reports a quantity in `totalInventoryNum` / `factoryInventoryNum` (a supplier
claim) and, separately, a `stock` array of concrete records each carrying a
`stockId`. The ten variants that carry NO stock record include the exact item
that failed, and the nine that shipped fine all carry one.

That correlation is the whole basis of this check, and it is worth being honest
about its strength: on 2026-08-17 the five affected products were ALSO found to
be active at CJ (status 3), listed by 48 to 86 other sellers, and quotable for
freight (27 carrier options each). So `stock: []` is NOT proven to mean
"discontinued". It is one stable, reproducible signal that happens to separate
the one item that actually failed from the ones that did not, n=1.

The posture here is therefore deliberately conservative: hold these at zero and
lose the sales, because a second unfulfillable order costs more than a few days
of a minor SKU being off sale. If CJ later confirms these are fine, change
`unshippable()` and nothing else.

NEVER ACT ON A SINGLE EMPTY ANSWER. One run returned empty rows for seven
healthy SKUs at once, including live kit components. All seven came back with
real stock records on retry. An unreachable SKU is UNKNOWN and is left alone;
zeroing on a flaky read would take good products, and their kits, offline.

    python config/guard_unshippable.py            # report
    python config/guard_unshippable.py --apply    # zero anything still on sale
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
LOCATION_ID = 113363058977          # Shop location: the only one that can sell


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


def cj_rows(sku, tries=3):
    """(rows, reachable). An empty answer is retried before it is believed."""
    for attempt in range(tries):
        try:
            rows = cj_api.call('/product/stock/queryBySku', {'sku': sku}).get('data')
            if isinstance(rows, list) and rows:
                return rows, True
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return [], False


def unshippable(rows):
    """True when no row carries a concrete stock record. The single predicate."""
    return not any((r.get('stock') or []) for r in rows)


def storefront_available(handles):
    """{handle: {variant_id: available}} straight from the live storefront.

    Admin inventory numbers lag and have read 0 immediately after a correct
    write. `available` on /products/<handle>.js is what a customer actually
    experiences, so that is what this asserts against.
    """
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

    bad, unknown, checked = [], [], 0
    for p in sorted(singles, key=lambda x: x['title']):
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            checked += 1
            rows, reachable = cj_rows(sku)
            if not reachable:
                unknown.append((p['title'], v['title'], sku))
                continue
            if unshippable(rows):
                bad.append({'product': p['title'], 'handle': p['handle'],
                            'variant': v['title'], 'sku': sku,
                            'variant_id': v['id'],
                            'item_id': v['inventory_item_id'],
                            'qty': v['inventory_quantity']})

    print(f'{checked} SKU-carrying variant(s) checked')
    if unknown:
        print(f'\n{len(unknown)} UNKNOWN (CJ would not answer after retries). '
              f'Left untouched on purpose:')
        for t, vt, s in unknown:
            print(f'  ? {t} / {vt}  {s}')

    if not bad:
        print('\nEvery variant CJ can ship. Nothing to hold back.')
        return 0

    on_sale = [b for b in bad if b['qty'] > 0]
    print(f'\n{len(bad)} variant(s) CJ cannot ship. '
          f'{len(on_sale)} of them still carry stock in Shopify:')
    for b in bad:
        flag = '!!' if b['qty'] > 0 else '  '
        print(f"  {flag} {b['product']} / {b['variant']}  {b['sku']}  qty={b['qty']}")

    if on_sale and apply:
        print(f'\nzeroing {len(on_sale)} variant(s)...')
        for b in on_sale:
            api('inventory_levels/set.json', 'POST',
                {'location_id': LOCATION_ID, 'inventory_item_id': b['item_id'],
                 'available': 0})
            print(f"  zeroed {b['sku']}")
    elif on_sale:
        print('\nRun with --apply to zero them.')

    # The real assertion: not the admin number, the customer's experience.
    print('\nstorefront check...')
    live = storefront_available({b['handle'] for b in bad})
    still_buyable = []
    for b in bad:
        state = live.get(b['handle'], {})
        if 'error' in state:
            print(f"  ? {b['handle']}: {state['error']}")
            continue
        if state.get(b['variant_id']):
            still_buyable.append(b)
    for b in bad:
        st = live.get(b['handle'], {})
        if 'error' not in st:
            print(f"  {'BUYABLE' if st.get(b['variant_id']) else 'off sale'}  "
                  f"{b['product']} / {b['variant']}")

    if still_buyable:
        print(f'\n{len(still_buyable)} UNSHIPPABLE VARIANT(S) ARE STILL ORDERABLE.')
        return 1
    print('\nNothing CJ cannot ship is orderable on the storefront.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
