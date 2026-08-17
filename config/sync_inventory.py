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
    """CJ's stock for one SKU, across both row shapes CJ returns.

    Some SKUs carry nested per-warehouse entries in a `stock` array, where the
    quantity is `inventory + factoryInventory` summed over the entries and
    `totalInventoryNum` undercounts (the Slicker Brush reads 2097 that way
    against a real 13505). Others carry only `totalInventoryNum`, with an empty
    or null `stock` array; summing those two fields returns 0.

    AN EMPTY `stock` ARRAY IS NOT A SHIPPING BLOCK. Between 2026-08-17 and
    2026-08-18 this function returned 0 in that case, on the theory that only a
    concrete `stockId` proved CJ could ship. That theory was WRONG and it zeroed
    ten healthy variants across five products. What actually disproved it, in
    CJ's own UI: the Bouncy Egg Squeaker (the item blamed for order #1002) shows
    "Inventory: 46587 (CJ: 0, Factory: 46587)" with carrier "LuWei Ordinary US ·
    Available" and 1 to 3 day processing. Supporting evidence from the API: all
    five products return status 3, are listed by 48 to 86 other sellers, and
    quote 27 carrier options each; CJ flags no line of order #1002 abnormal, and
    CJ's Abnormal Orders tab reads 0.

    So: fall back to `totalInventoryNum` when there is no stock record. That is
    the number CJ's own product page displays.

    Whether a variant can be FULFILLED is a separate question from how many
    units exist, and it is answered by asking CJ for a carrier, not by reading
    this field. `config/guard_unshippable.py` does that.
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
    if has_record:
        return total
    return sum(int(w.get('totalInventoryNum') or 0) for w in rows)


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
