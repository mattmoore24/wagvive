#!/usr/bin/env python3
"""Two merchandising corrections on top of the margin guard's raw output.

1. Colour must not change the price. White ships dearer than Pink/Blue/Grey on
   the Water Bowl, so pricing each variant to its own cost produced $44 for three
   colours and $48 for the fourth in the same size. Shoppers read that as a
   mistake. Each size band is levelled UP to the highest price any colour in it
   needs, so nothing drops below the floor.

2. The Furniture Cover is priced off an ESTIMATE, not a quote - CJ returns $0.00
   for it on every carrier. Stress-proofing an estimate compounds guesswork, so
   it is set to the price that clears 50% on the estimate itself ($76) rather
   than the stress-proof $84. Revisit once a real order shows the true freight.
"""
import json, os, re, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WATER_BOWL = 10456337547553
FURNITURE_COVER = 10464690143521
COVER_PRICE = 76.00

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


def size_of(title):
    """Variant titles are 'Colour / Size'; the size is the band we level within."""
    parts = [p.strip() for p in str(title).split('/')]
    return parts[-1] if len(parts) > 1 else str(title)


def main():
    p = api('GET', f'products/{WATER_BOWL}.json')['product']
    bands = {}
    for v in p['variants']:
        bands.setdefault(size_of(v['title']), []).append(v)

    print(p['title'].encode('ascii', 'replace').decode())
    for size, vs in bands.items():
        top = max(float(v['price']) for v in vs)
        for v in vs:
            cur = float(v['price'])
            if abs(cur - top) > 0.005:
                api('PUT', f'variants/{v["id"]}.json',
                    {'variant': {'id': v['id'], 'price': f'{top:.2f}'}})
                print(f'   {str(v["title"])[:24]:26} ${cur:.2f} -> ${top:.2f}  '
                      f'(levelled to {size})')
            else:
                print(f'   {str(v["title"])[:24]:26} ${cur:.2f}')

    c = api('GET', f'products/{FURNITURE_COVER}.json')['product']
    v = c['variants'][0]
    cur = float(v['price'])
    if abs(cur - COVER_PRICE) > 0.005:
        api('PUT', f'variants/{v["id"]}.json',
            {'variant': {'id': v['id'], 'price': f'{COVER_PRICE:.2f}'}})
    print(f'\n{c["title"].encode("ascii", "replace").decode()}')
    print(f'   ${cur:.2f} -> ${COVER_PRICE:.2f}  (freight is an estimate, not a quote)')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
