#!/usr/bin/env python3
"""
Replace the cat-sized Calming Comfort Bed with a large-breed orthopedic bed.

The old SKU was a small raised-rim nest whose entire supplier gallery was cats.
The new one is a three-sided bolster bed on an orthopedic egg-crate foam base,
sized 71x58 / 91x68 / 105x75 cm, from the same CJ in-house supplier (id 7777)
as the rest of the catalogue.

Also re-prices the Comfort & Health Kit: swapping a $40 component for a $54 one
moves the true component total from $138 to $152, so the kit moves $89 -> $99
to hold roughly the same ~35% saving.
"""
import base64, json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'config', 'branding', 'cj-raw', 'bedcands')

BED = 10456337711393
KIT = 10458198081825

# gallery order: clean profile -> lifestyle -> front -> angle -> lifestyle wide
IMAGES = ['B02.jpg', 'B08.jpg', 'B06.jpg', 'B13.jpg', 'B01.jpg']

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
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode() or '{}')


def main():
    with open(os.path.join(ROOT, 'config', 'products', 'product_8.json'), encoding='utf-8') as fh:
        bed = json.load(fh)['product']
    with open(os.path.join(ROOT, 'config', 'products', 'bundle_comfort.json'), encoding='utf-8') as fh:
        kit = json.load(fh)['product']

    # --- bed: copy, handle, price ------------------------------------------
    current = api('GET', f'products/{BED}.json')['product']
    payload = {'product': {
        'id': BED,
        'title': bed['title'],
        'handle': bed['handle'],
        'body_html': bed['body_html'],
        'product_type': bed['product_type'],
        'tags': bed['tags'],
        'status': 'active',
        'variants': [{'id': current['variants'][0]['id'], 'price': bed['variants'][0]['price']}],
    }}
    res = api('PUT', f'products/{BED}.json', payload)['product']
    print(f"bed   -> {res['title']}  ${res['variants'][0]['price']}  /{res['handle']}")

    # --- bed images ---------------------------------------------------------
    for img in api('GET', f'products/{BED}/images.json').get('images', []):
        api('DELETE', f'products/{BED}/images/{img["id"]}.json')
    for n, f in enumerate(IMAGES, 1):
        p = os.path.join(RAW, f)
        if not os.path.exists(p):
            print(f'  MISSING {f}')
            continue
        with open(p, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()
        i = api('POST', f'products/{BED}/images.json', {'image': {
            'attachment': b64, 'filename': f,
            'alt': bed['title'] if n == 1 else f"{bed['title']} - detail",
            'position': n}})['image']
        print(f'  {f:10} -> {i["width"]}x{i["height"]}')

    # --- kit: description + price ------------------------------------------
    kcur = api('GET', f'products/{KIT}.json')['product']
    kres = api('PUT', f'products/{KIT}.json', {'product': {
        'id': KIT,
        'body_html': kit['body_html'],
        'variants': [{'id': kcur['variants'][0]['id'],
                      'price': kit['variants'][0]['price'],
                      'compare_at_price': kit['variants'][0]['compare_at_price']}],
    }})['product']
    kv = kres['variants'][0]
    print(f"kit   -> ${kv['price']} (was ${kcur['variants'][0]['price']})  "
          f"compare ${kv['compare_at_price']}")


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, e.read().decode()[:800], file=sys.stderr)
        sys.exit(1)
