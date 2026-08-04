#!/usr/bin/env python3
"""
Fill the two imagery gaps.

Water bowl had one photo against eight colour/capacity variants, so a customer
picking Pink or Blue couldn't see what they were buying. Now carries a shot per
colourway plus a lifestyle image. The supplier's "e / els pet" mark was removed
from the pink, grey and lifestyle shots (b02 and b23 are shot from an angle where
it isn't visible).

Both kits had a single image. They now show their actual components, pulled from
the component products' own galleries by CDN URL.
"""
import base64, json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOWL_DIR = os.path.join(ROOT, 'config', 'branding', 'cj-raw', 'bowl2')

BOWL = 10456337547553
COMFORT_KIT = 10464745718049
GROOMING_KIT = 10458197819681

BOWL_IMAGES = [
    ('b02.img',        'Wagvive Anti-Spill Floating Water Bowl'),
    ('b03_clean.jpg',  'Wagvive Anti-Spill Floating Water Bowl in use'),
    ('b34_clean.jpg',  'Wagvive Anti-Spill Floating Water Bowl - grey'),
    ('b16_clean.jpg',  'Wagvive Anti-Spill Floating Water Bowl - pink'),
    ('b23.img',        'Wagvive Anti-Spill Floating Water Bowl - blue'),
]

# kit id -> component product ids, in gallery order
KIT_COMPONENTS = {
    COMFORT_KIT: [10464689881377, 10456337547553, 10456337613089],
    GROOMING_KIT: [10456336990497, 10456337056033, 10456337154337, 10456337318177],
}

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


def clear_images(pid):
    for img in api('GET', f'products/{pid}/images.json').get('images', []):
        api('DELETE', f'products/{pid}/images/{img["id"]}.json')


def main():
    print('Water bowl gallery:')
    clear_images(BOWL)
    for n, (fname, alt) in enumerate(BOWL_IMAGES, 1):
        p = os.path.join(BOWL_DIR, fname)
        if not os.path.exists(p):
            print(f'   MISSING {fname}'); continue
        with open(p, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()
        img = api('POST', f'products/{BOWL}/images.json', {'image': {
            'attachment': b64, 'filename': fname.replace('.img', '.jpg'),
            'alt': alt, 'position': n}})['image']
        print(f'   {fname:16} -> {img["width"]}x{img["height"]}')

    for kit, comps in KIT_COMPONENTS.items():
        title = api('GET', f'products/{kit}.json')['product']['title']
        print(f'\n{title} gallery:')
        clear_images(kit)
        pos = 1
        for cpid in comps:
            cp = api('GET', f'products/{cpid}.json')['product']
            if not cp['images']:
                print(f'   {cp["title"][:34]:36} no images to borrow'); continue
            src = cp['images'][0]['src']
            img = api('POST', f'products/{kit}/images.json', {'image': {
                'src': src, 'alt': cp['title'], 'position': pos}})['image']
            pos += 1
            print(f'   {cp["title"][:34]:36} -> {img["width"]}x{img["height"]}')

    print('\nfinal image counts:')
    for pid in (BOWL, COMFORT_KIT, GROOMING_KIT):
        p = api('GET', f'products/{pid}.json')['product']
        t = p['title'].encode('ascii', 'replace').decode()
        print(f'   {t[:40]:42} {len(p["images"])} images, {len(p["variants"])} variants')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
