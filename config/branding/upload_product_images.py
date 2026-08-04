#!/usr/bin/env python3
"""Attach the generated Wagvive illustrations to their Shopify products."""
import base64, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG_DIR = os.path.join(ROOT, 'config', 'branding', 'products')

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v

DOMAIN = env['SHOPIFY_STORE_DOMAIN']
TOKEN = env['SHOPIFY_ADMIN_API_TOKEN']
VERSION = env['SHOPIFY_API_VERSION']

# file stem -> (product id, alt text)
MAPPING = [
    ('product-slicker-brush',   10456336990497, 'Wagvive Self-Cleaning Slicker Brush'),
    ('product-shedding-gloves', 10456337056033, 'Wagvive Grooming & Shedding Gloves'),
    ('product-cleaning-wipes',  10456337154337, 'Wagvive Ear & Teeth Cleaning Wipes'),
    ('product-nail-grinder',    10456337318177, 'Wagvive Quiet Electric Nail Grinder'),
    ('product-cooling-mat',     10456337383713, 'Wagvive Cooling Comfort Mat'),
    ('product-water-bowl',      10456337547553, 'Wagvive Anti-Spill Floating Water Bowl'),
    ('product-slow-feeder',     10456337613089, 'Wagvive Slow Feeder Bowl'),
    ('product-comfort-bed',     10456337711393, 'Wagvive Calming Comfort Bed'),
    ('bundle-grooming-kit',     10458197819681, 'Wagvive Grooming Essentials Kit - four piece set'),
    ('bundle-comfort-kit',      10458198081825, 'Wagvive Comfort & Health Kit - four piece set'),
]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN,
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())


def main():
    for stem, pid, alt in MAPPING:
        path = os.path.join(IMG_DIR, stem + '.png')
        if not os.path.exists(path):
            print(f'SKIP  {stem}: file missing')
            continue

        # Remove any images already on the product so re-runs stay idempotent.
        existing = api('GET', f'products/{pid}/images.json').get('images', [])
        for img in existing:
            api('DELETE', f'products/{pid}/images/{img["id"]}.json')

        with open(path, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()

        res = api('POST', f'products/{pid}/images.json', {
            'image': {'attachment': b64, 'filename': stem + '.png', 'alt': alt}
        })
        img = res['image']
        print(f'OK    {stem:26} -> product {pid}  image {img["id"]}  {img["width"]}x{img["height"]}')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        print('HTTP ERROR', e.code, e.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
