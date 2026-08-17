#!/usr/bin/env python3
"""Mirror CJ stock into the Shopify location that can actually sell it.

This script was briefly made read-only on the theory that CJ's webhook made it
redundant. That was wrong, and worth writing down so it is not repeated:

  * CJ's webhook does sync, reliably, to its own `cjdropshipping` location.
  * That location is a THIRD_PARTY fulfilment service. Our variants are
    `fulfillment_service: manual`, because they were created through the Admin
    API rather than imported by the CJ app - and REST silently ignores attempts
    to reassign a variant's fulfilment service.
  * Shopify will not sell a manual variant from a service location, so CJ's
    stock figures are inert as far as the storefront is concerned.

So availability is governed by `Shop location`, and something has to copy CJ's
numbers there. That is this script. Without it, stock never decrements from
supply-side changes and a sold-out CJ item stays buyable.

Writes only to the canonical sellable location - never `inventory_levels[0]`,
which is whatever Shopify happens to return first and was the original source of
the double-counted figures.

    python config/sync_inventory.py            # report drift
    python config/sync_inventory.py --apply    # write CJ's numbers in
"""
import json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL = 'Shop location'

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
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def cj_stock(sku):
    """What CJ can actually SHIP, which is not the same as what it advertises.

    Sum `inventory + factoryInventory` over the entries of each row's `stock`
    array. A populated `stock` array carries a real `stockId`, i.e. an
    addressable warehouse record CJ can draw against.

    WHEN `stock` IS null, RETURN 0. Do not fall back to `totalInventoryNum`.
    That fallback is what caused order #1002 (CJ DP2608121816000646700) to ship
    short: the Bouncy Egg Squeaker Green advertised
    totalInventoryNum/factoryInventoryNum of 44,838 with `stock: null`, we wrote
    44,838 into Shopify, and CJ then had nothing to send. Ten variants across
    five products were in that state. `totalInventoryNum` mirrors
    `factoryInventoryNum` on every row we have ever seen, so it is a SUPPLIER
    CLAIM, not CJ stock; `cjInventoryNum` is 0 across the entire catalogue
    because CJ warehouses none of it and sources per order.

    The older docstring here claimed totalInventoryNum "understates" the truth
    and cited the Slicker Brush at 2097 vs 13505. That comparison was between
    the warehouse row and the factory total; it never established that the
    factory total is shippable, and #1002 proved it is not.

    `config/audit_cj_shippability.py` reports every SKU in the null state.
    """
    res = cj_api.call('/product/stock/queryBySku', {'sku': sku})
    rows = res.get('data')
    if not rows:
        return None
    total, has_record = 0, False
    for w in rows:
        entries = w.get('stock') or []
        if entries:
            has_record = True
            for s in entries:
                total += (s.get('inventory') or 0) + (s.get('factoryInventory') or 0)
    return total if has_record else 0


def main():
    apply_fix = '--apply' in sys.argv
    locs = api('GET', 'locations.json')['locations']
    canon = next((l for l in locs if l['name'] == CANONICAL), None)
    if not canon:
        print(f'no {CANONICAL!r} location'); sys.exit(1)

    drift = []
    for p in api('GET', 'products.json?limit=250&status=active')['products']:
        printed = False
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            item = v['inventory_item_id']
            levels = api('GET', f'inventory_levels.json?inventory_item_ids={item}'
                         )['inventory_levels']
            here = next((l['available'] for l in levels
                         if str(l['location_id']) == str(canon['id'])), None)
            theirs = cj_stock(sku)
            off = theirs is not None and here != theirs
            if not printed:
                print(p['title'].encode('ascii', 'replace').decode()); printed = True
            note = f'  <-- CJ says {theirs}' if off else ''
            print(f'   {str(v["title"])[:28]:30} {sku:22} shopify {str(here):>8}{note}')
            if off:
                drift.append((p['title'], v['title'], sku, here, theirs))
                if apply_fix:
                    api('POST', 'inventory_levels/set.json',
                        {'location_id': canon['id'], 'inventory_item_id': item,
                         'available': int(theirs)})
        if printed:
            print()

    if not drift:
        print(f'Shopify matches CJ on every variant at {CANONICAL}.')
    elif apply_fix:
        print(f'{len(drift)} variant(s) updated from CJ.')
    else:
        print(f'{len(drift)} variant(s) out of step with CJ. Run with --apply.')
        for t, vt, sku, here, theirs in drift[:12]:
            print(f'  {t[:30]:32} {str(vt)[:18]:20} {here} -> {theirs}')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
