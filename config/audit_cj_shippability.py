#!/usr/bin/env python3
"""Which SKUs can CJ ACTUALLY ship, as opposed to merely claim stock for?

WHY THIS EXISTS. Order #1002 (CJ DP2608121816000646700) shipped short: the
Bouncy Egg Squeaker Green was out of stock at CJ while Shopify showed 44,838
available. Every prior audit passed, because they all asked the wrong question.
`sync_inventory.py` proves Shopify MATCHES the number CJ reports, and
`verify_kit_inventory.py` proves kits derive correctly from components. Neither
asks whether CJ's number means anything.

WHAT THE ORDER TAUGHT US, measured across the SKUs from orders 1001/1002/1003:

  * `cjInventoryNum` is 0 for EVERY SKU in the catalogue. CJ warehouses none of
    it; everything is sourced from the factory when an order lands. So a big
    "in stock" figure is a SUPPLIER CLAIM, never CJ on-hand stock.
  * `totalInventoryNum` == `factoryInventoryNum` on every row. The number we
    sync is factory inventory, full stop.
  * The one observable difference between the SKU that failed and the nine that
    shipped: the failed one had **`stock: null`**, while every successful one had
    a populated `stock` array carrying a real `stockId`. A stockId is an
    addressable warehouse record; null means there is nothing to draw against,
    however large factoryInventoryNum looks.

So `stock: null` is treated here as NOT SHIPPABLE regardless of the headline
number, and this audit flags every SKU in that state before a customer finds it.

    python config/audit_cj_shippability.py
    python config/audit_cj_shippability.py --json   # machine-readable log
"""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api  # noqa: E402

import urllib.request  # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
D, T, V = (env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'],
           env['SHOPIFY_API_VERSION'])


def api(path):
    rq = urllib.request.Request(f'https://{D}/admin/api/{V}/{path}',
                                headers={'X-Shopify-Access-Token': T})
    with urllib.request.urlopen(rq, timeout=120) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


def classify(rows):
    """(shippable_qty, factory_qty, cj_on_hand, verdict) for one SKU's rows."""
    if not isinstance(rows, list) or not rows:
        return 0, 0, 0, 'NO ROWS'
    factory = cj_hand = shippable = 0
    has_record = False
    for row in rows:
        factory += int(row.get('factoryInventoryNum') or 0)
        cj_hand += int(row.get('cjInventoryNum') or 0)
        entries = row.get('stock')
        if isinstance(entries, list) and entries:
            has_record = True
            for e in entries:
                shippable += (int(e.get('inventory') or 0)
                              + int(e.get('factoryInventory') or 0))
    if not has_record:
        return 0, factory, cj_hand, 'NO STOCK RECORD'
    return shippable, factory, cj_hand, 'ok'


def main():
    prods = api('products.json?limit=250&status=active')['products']
    singles = [p for p in prods
               if p.get('product_type') not in ('Bundles & Kits', 'Kit Bundle')]

    print('CJ shippability audit. "NO STOCK RECORD" means stock:null, which is '
          'what\nthe Bouncy Egg Squeaker showed when order #1002 shipped '
          'short.\n')
    bad, checked, log = [], 0, []
    for p in sorted(singles, key=lambda x: x['title']):
        lines = []
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            checked += 1
            rows = cj_api.call('/product/stock/queryBySku',
                               {'sku': sku}).get('data')
            ship, factory, hand, verdict = classify(rows)
            shopify_qty = v['inventory_quantity']
            entry = {'product': p['title'], 'variant': v['title'], 'sku': sku,
                     'shopify': shopify_qty, 'shippable': ship,
                     'factory': factory, 'cj_on_hand': hand,
                     'verdict': verdict}
            log.append(entry)
            if verdict != 'ok':
                bad.append(entry)
                lines.append(f"    !! {v['title']:22} {sku:18} "
                             f"shopify={shopify_qty:>7}  factory={factory:>7}  "
                             f"{verdict}")
        if lines:
            print(f"{p['title']}")
            print('\n'.join(lines))

    print('\n' + '=' * 72)
    print(f'{checked} SKU-carrying variants checked across {len(singles)} '
          f'products')
    print(f'CJ on-hand (cjInventoryNum) across the catalogue: '
          f'{sum(e["cj_on_hand"] for e in log)} units -> everything is '
          f'factory-sourced on demand')
    if '--json' in sys.argv:
        out = os.path.join(ROOT, 'docs', 'qa',
                           f'cj-shippability-{time.strftime("%Y-%m-%d")}.json')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(log, fh, indent=2)
        print(f'log -> {os.path.relpath(out, ROOT)}')

    # Having no CJ stock record is not by itself an incident. It only becomes
    # one when Shopify is still offering the thing for sale. Failing on every
    # unshippable SKU regardless of its Shopify quantity would mean this audit
    # could never go green while those products exist, and an audit that always
    # fails is one that stops being read.
    exposed = [e for e in bad if e['shopify'] > 0]
    contained = [e for e in bad if e['shopify'] <= 0]

    if contained:
        print(f'\n{len(contained)} variant(s) CJ cannot ship, correctly held at '
              f'0 in Shopify so they cannot be ordered:')
        for e in contained:
            print(f"  - {e['product']} / {e['variant']}  {e['sku']}")

    if exposed:
        print(f'\n{len(exposed)} VARIANT(S) CJ CANNOT SHIP but Shopify SELLS:')
        for e in exposed:
            print(f"  ! {e['product']} / {e['variant']}  {e['sku']}  "
                  f"shopify={e['shopify']}  {e['verdict']}")
        print('\nZero these in Shopify now: they will fail at fulfilment.')
        return 1
    if contained:
        print('\nNothing unshippable is on sale.')
        return 0
    print('\nEvery SKU-carrying variant has a real CJ stock record.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
