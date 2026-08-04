#!/usr/bin/env python3
"""
Archive the two SKUs that freight made unviable, plus the kit that contains them.

Cooling Comfort Mat  2,020g -> $46.42 freight -> landed $48.31 against $34 retail
Orthopedic Comfort Bed 3,750g -> $108.63 freight -> landed $126.54 against $54 retail
Comfort & Health Kit  contains both; bed + mat together (5,770g) is refused by every carrier

Archived rather than deleted so the listings, images and copy stay recoverable.
The kit is archived only until it is rebuilt around the ice silk pad.
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# archive the kit first so the two products are no longer in-use components
TARGETS = [
    (10458198081825, 'Comfort & Health Kit', 'contains bed + mat; unshippable, rebuild pending'),
    (10456337383713, 'Cooling Comfort Mat', 'freight $46.42 on 2,020g'),
    (10456337711393, 'Orthopedic Comfort Bed', 'freight $108.63 on 3,750g'),
]

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
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode() or '{}')


def main():
    for pid, label, why in TARGETS:
        try:
            before = api('GET', f'products/{pid}.json')['product']['status']
            res = api('PUT', f'products/{pid}.json',
                      {'product': {'id': pid, 'status': 'archived'}})['product']
            print(f'{label:26} {before} -> {res["status"]:9} ({why})')
        except urllib.error.HTTPError as exc:
            print(f'{label:26} FAILED HTTP {exc.code}: {exc.read().decode()[:200]}')

    print('\nRemaining active products:')
    for p in api('GET', 'products.json?limit=250&status=active')['products']:
        t = p['title'].encode('ascii', 'replace').decode()
        print(f'  {p["id"]}  {t[:40]:42} ${p["variants"][0]["price"]}')


if __name__ == '__main__':
    main()
