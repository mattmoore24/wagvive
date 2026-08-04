#!/usr/bin/env python3
"""Keep stock at the location that can actually sell it.

This script previously did the opposite, and broke the whole catalogue. The
correction, and why it matters:

  * `cjdropshipping` is a THIRD_PARTY fulfilment-service location.
  * Our variants are `fulfillment_service: manual` - they were created through
    the Admin API, not imported by the CJ app, and REST silently ignores attempts
    to reassign a variant's fulfilment service.
  * Shopify will not sell a `manual` variant from a third-party service location.

So CJ's webhook writing stock to its own location does NOT gate storefront
availability - that stock is inert. Availability comes from `Shop location`.
Moving everything to the CJ location made all 48 variants read `available: false`
while showing thousands in stock.

Canonical location is therefore the one that fulfils online orders and is NOT a
fulfilment service. Stock is mirrored there from CJ, and levels at the CJ
location are removed so `inventory_quantity` (which SUMS across locations) does
not report double the real figure.

    python config/fix_locations.py           # report only
    python config/fix_locations.py --apply
"""
import json, os, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL = 'Shop location'
SERVICE_LOCATION = 'cjdropshipping'

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


def api(method, path, payload=None, tries=6):
    """Shopify caps REST at 2 calls/second and answers 429 past that. This walks
    the whole catalogue variant by variant, so it WILL hit the cap without a
    pause between calls plus backoff on rejection."""
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode()
                time.sleep(0.55)
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt < tries - 1:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise


def cj_stock(sku):
    """CJ's shippable quantity: warehouse + factory, summed over stock rows."""
    res = cj_api.call('/product/stock/queryBySku', {'sku': sku})
    rows = res.get('data')
    if not rows:
        return None
    total = 0
    for w in rows:
        entries = w.get('stock') or []
        if entries:
            for s in entries:
                total += (s.get('inventory') or 0) + (s.get('factoryInventory') or 0)
        else:
            total += w.get('totalInventoryNum') or w.get('storageNum') or 0
    return total


def main():
    apply_fix = '--apply' in sys.argv

    locs = api('GET', 'locations.json')['locations']
    canon = next((l for l in locs if l['name'] == CANONICAL), None)
    svc = next((l for l in locs if l['name'] == SERVICE_LOCATION), None)
    if not canon:
        print(f'no {CANONICAL!r} location'); sys.exit(1)
    print(f'sellable location : {canon["id"]}  {canon["name"]}')
    print(f'service location  : {svc["id"] if svc else "-"}  {SERVICE_LOCATION}\n')

    fixed = wrong = 0
    for p in api('GET', 'products.json?limit=250&status=active')['products']:
        rows = []
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            item = v['inventory_item_id']
            levels = api('GET', f'inventory_levels.json?inventory_item_ids={item}'
                         )['inventory_levels']
            by = {str(l['location_id']): l['available'] for l in levels}
            here = by.get(str(canon['id']))
            there = by.get(str(svc['id'])) if svc else None
            need = here is None
            if need or there is not None:
                wrong += 1
                rows.append((v, here, there))
                if apply_fix:
                    qty = cj_stock(sku)
                    if qty is None:
                        qty = there if there is not None else 0
                    api('POST', 'inventory_levels/connect.json',
                        {'inventory_item_id': item, 'location_id': canon['id']})
                    api('POST', 'inventory_levels/set.json',
                        {'location_id': canon['id'], 'inventory_item_id': item,
                         'available': int(qty)})
                    if svc and there is not None:
                        api('DELETE', f'inventory_levels.json?'
                                      f'inventory_item_id={item}&location_id={svc["id"]}')
                    fixed += 1
        if rows:
            print(p['title'].encode('ascii', 'replace').decode())
            for v, here, there in rows:
                print(f'   {str(v["title"])[:28]:30} sellable={str(here):>8}  '
                      f'service={str(there):>8}')
            print()

    if not wrong:
        print('Every variant is stocked at the sellable location only.')
    elif apply_fix:
        print(f'{fixed} variant(s) restored to {CANONICAL}.')
    else:
        print(f'{wrong} variant(s) not sellable as configured. Run with --apply.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
