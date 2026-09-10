#!/usr/bin/env python3
"""Reshoot the Calm & Comfort Kit covers after the anxiety vest swap.

FOUR IMAGES: the "everything included" flatlay and one cover per colorway. All
four were showing the Calming Thunder Wrap, a folded grey minky BLANKET, which
CJ has delisted and which is no longer in the kit. The replacement is a worn
vest, so this is a change of subject and not a retouch.

WHILE IN THERE, a second error was fixed that predates this work: every one of
the four covers also showed a small orange Talk Button, which belongs to the
Dog Enrichment Kit and has never been part of Calm & Comfort. So the covers
advertised six items for a five item kit, one of them unbuyable and one of them
not in the box at all. `audit_kits.py` cannot catch that, because it checks
gallery ALT TEXT and there is no way to count objects inside a flattened JPEG.
The covers are edits of the originals, so the four components that ARE correct
stay pixel-accurate.

WHY NOT apply_colorway_covers.py. That script is idempotent BY FILENAME and
skips a colorway it has already uploaded, so reshot art under the same name is
silently ignored. Deleting the Shopify image first is the documented fix, and
the delete has to match by ALT TEXT: with the cover gone, "position 1" is a
component still, which is how apply_kit_covers.py once ate two of them.

COLORWAY COVERS DRIVE THE SWATCH AND THE CART THUMBNAIL. Each colorway variant
carries an image_id pointing at its cover, so deleting one orphans three
variants until they are re-wired. That re-wiring is verified at the end from a
re-read, not from the write's return value.

    python config/apply_calm_kit_covers.py            # plan
    python config/apply_calm_kit_covers.py --apply
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = (r'C:\Users\mattm\AppData\Local\Temp\claude'
       r'\C--Users-mattm-OneDrive-Claude-Code-Pet-Store'
       r'\040c7b44-775a-401d-a2fd-6844cb38bb7f\scratchpad\vest')
ART_CW = os.path.join(ROOT, 'config', 'branding', 'kit-covers', 'colorway')
ART_FL = os.path.join(ROOT, 'config', 'branding', 'kit-covers', 'flatlay')
OUT_PX = 1600

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

HANDLE = 'calm-comfort-kit'
KIT = 'Calm & Comfort Kit'

# (render in the scratchpad, repo art path, image alt, colorway or None)
COVERS = [
    ('new_flatlay.png', os.path.join(ART_FL, f'{HANDLE}.jpg'),
     f'{KIT} - everything included', None),
    ('new_Grey.png', os.path.join(ART_CW, f'{HANDLE}__Grey.jpg'),
     f'{KIT} - Grey', 'Grey'),
    ('new_Blue.png', os.path.join(ART_CW, f'{HANDLE}__Blue.jpg'),
     f'{KIT} - Blue', 'Blue'),
    ('new_Pink.png', os.path.join(ART_CW, f'{HANDLE}__Pink.jpg'),
     f'{KIT} - Pink', 'Pink'),
]


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read().decode()
            time.sleep(0.7)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (429, 409, 500, 502, 503) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {body}')
    return {}


def product():
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] == HANDLE:
            return p
    return None


def to_jpg(src_png, dest_jpg):
    im = Image.open(src_png).convert('RGB')
    if max(im.size) != OUT_PX:
        im = im.resize((OUT_PX, OUT_PX), Image.LANCZOS)
    im.save(dest_jpg, 'JPEG', quality=92, optimize=True)
    return os.path.getsize(dest_jpg)


def main():
    apply = '--apply' in sys.argv
    missing = [f for f, _, _, _ in COVERS
               if not os.path.exists(os.path.join(SRC, f))]
    if missing:
        print('MISSING renders, nothing written:')
        for m in missing:
            print('  ! ' + m)
        return 1

    p = product()
    if not p:
        print(f'{HANDLE} not found')
        return 1
    print(f"{p['title']}  {len(p['images'])} images, {len(p['variants'])} variants")
    for fn, art, alt, cw in COVERS:
        have = [i for i in p['images'] if (i.get('alt') or '') == alt]
        wired = sum(len(i.get('variant_ids') or []) for i in have)
        print(f"  {alt:44} {len(have)} live ({wired} variants wired) <- {fn}")
    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    print('\n--- writing the repo art files ---')
    for fn, art, alt, _cw in COVERS:
        n = to_jpg(os.path.join(SRC, fn), art)
        print(f'  {os.path.relpath(art, ROOT)}  {n // 1024} KB')

    print('\n--- replacing the live images, matched by ALT ---')
    pid = p['id']
    new_ids = {}
    for n, (fn, art, alt, cw) in enumerate(COVERS, start=1):
        for old in [i for i in p['images'] if (i.get('alt') or '') == alt]:
            api('DELETE', f"products/{pid}/images/{old['id']}.json")
            print(f'  deleted old {alt}')
        with open(art, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()
        body = {'image': {'attachment': b64, 'alt': alt}}
        if cw is None:
            body['image']['position'] = 1
        img = api('POST', f'products/{pid}/images.json', body)['image']
        new_ids[cw] = img['id']
        print(f"  uploaded {alt} -> {img['id']}")

    print('\n--- re-wiring the colorway swatches, from a RE-READ ---')
    fresh = api('GET', f'products/{pid}.json')['product']
    wired = 0
    for v in fresh['variants']:
        cw = next((o for o in (v.get('option1'), v.get('option2'))
                   if o in new_ids), None)
        if not cw:
            print(f"  ! no colorway cover for variant {v['title']}")
            continue
        api('PUT', f"variants/{v['id']}.json",
            {'variant': {'id': v['id'], 'image_id': new_ids[cw]}})
        wired += 1
    print(f"  re-wired {wired}/{len(fresh['variants'])} variants")

    print('\n--- verify, re-fetched ---')
    again = api('GET', f'products/{pid}.json')['product']
    alts = {(i.get('alt') or ''): i['id'] for i in again['images']}
    bad = 0
    for _fn, _art, alt, cw in COVERS:
        ok = alt in alts
        print(f"  {alt:44} {'present' if ok else 'MISSING'}")
        bad += not ok
    for v in again['variants']:
        cw = next((o for o in (v.get('option1'), v.get('option2'))
                   if o in new_ids), None)
        ok = cw is not None and v.get('image_id') == new_ids[cw]
        print(f"  {v['title']:14} image_id {v.get('image_id')} "
              f"{'ok' if ok else 'WRONG'}")
        bad += not ok
    stale = [a for a in alts if 'Thunder Wrap' in a]
    print(f"  images still naming the old wrap: {stale or 'none'}")
    bad += len(stale)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
