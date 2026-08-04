#!/usr/bin/env python3
"""
Catalog restructure for Wagvive:
  - activate all products (storefront is still password-gated)
  - rename the two collections from bundle-style names to real category names
  - add each bundle into its matching category
  - create a dedicated "Bundles & Kits" collection
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

DOMAIN, TOKEN, VERSION = env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'], env['SHOPIFY_API_VERSION']

GROOMING_COLL = 516731339041
COMFORT_COLL = 516731371809
GROOMING_BUNDLE = 10458197819681
COMFORT_BUNDLE = 10458198081825

GROOMING_SKUS = [10456336990497, 10456337056033, 10456337154337, 10456337318177]
COMFORT_SKUS = [10456337383713, 10456337547553, 10456337613089, 10456337711393]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        print(f'  !! {method} {path} -> {e.code} {body}')
        return None


def ensure_collect(collection_id, product_id):
    existing = api('GET', f'collects.json?collection_id={collection_id}&limit=250') or {}
    if any(c['product_id'] == product_id for c in existing.get('collects', [])):
        return 'already in'
    api('POST', 'collects.json', {'collect': {'collection_id': collection_id, 'product_id': product_id}})
    return 'added'


print('== 1. Activating products ==')
prods = api('GET', 'products.json?limit=50')['products']
for p in prods:
    if p['status'] != 'active':
        api('PUT', f"products/{p['id']}.json", {'product': {'id': p['id'], 'status': 'active'}})
        print(f"  activated: {p['title']}")
    else:
        print(f"  already active: {p['title']}")

print('\n== 2. Renaming collections to category names ==')
api('PUT', f'custom_collections/{GROOMING_COLL}.json', {'custom_collection': {
    'id': GROOMING_COLL,
    'title': 'Grooming',
    'handle': 'grooming',
    'body_html': '<p>Calmer grooming days. Tools chosen to work quickly and feel gentle '
                 '&mdash; so brushing, nail trims, and ear care stop being a fight.</p>',
}})
print('  516731339041 -> "Grooming" (/collections/grooming)')

api('PUT', f'custom_collections/{COMFORT_COLL}.json', {'custom_collection': {
    'id': COMFORT_COLL,
    'title': 'Comfort & Health',
    'handle': 'comfort-health',
    'body_html': '<p>The daily basics, done properly. Rest, hydration, and mealtime gear '
                 'built around the habits that shape how your dog feels.</p>',
}})
print('  516731371809 -> "Comfort & Health" (/collections/comfort-health)')

print('\n== 3. Adding bundles into their categories ==')
print(f'  grooming bundle: {ensure_collect(GROOMING_COLL, GROOMING_BUNDLE)}')
print(f'  comfort bundle:  {ensure_collect(COMFORT_COLL, COMFORT_BUNDLE)}')

print('\n== 4. Bundles & Kits collection ==')
colls = api('GET', 'custom_collections.json?limit=50')['custom_collections']
bundle_coll = next((c for c in colls if c['handle'] == 'bundles-kits'), None)
if not bundle_coll:
    res = api('POST', 'custom_collections.json', {'custom_collection': {
        'title': 'Bundles & Kits',
        'handle': 'bundles-kits',
        'body_html': '<p>Everything for a routine, in one box &mdash; priced below buying each piece on its own.</p>',
        'published': True,
    }})
    bundle_coll = res['custom_collection']
    print(f"  created: {bundle_coll['id']}")
else:
    print(f"  exists: {bundle_coll['id']}")
for pid in (GROOMING_BUNDLE, COMFORT_BUNDLE):
    print(f'    product {pid}: {ensure_collect(bundle_coll["id"], pid)}')

print('\n== Final state ==')
for c in api('GET', 'custom_collections.json?limit=50')['custom_collections']:
    n = len((api('GET', f"collects.json?collection_id={c['id']}&limit=250") or {}).get('collects', []))
    print(f"  {c['id']} | {c['title']:22} | /{c['handle']:18} | {n} products")
