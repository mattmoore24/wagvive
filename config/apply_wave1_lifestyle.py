#!/usr/bin/env python3
"""Upload the wave-1 lifestyle shots and the reshot Travel Kit covers.

TWO JOBS, DELIBERATELY IN ONE SCRIPT because they were caused by the same
change: the Travel Kit gained the 3-in-1 Travel Bowl as a sixth component, so
every Travel Kit cover was showing a kit that no longer exists, and the two new
products had studio shots but no lifestyle shot.

MATCH THE COVER BY ALT TEXT, NEVER BY POSITION. `apply_kit_covers.py` used to
replace "position 1" and ate two component photos doing it: once the old cover
is deleted, position 1 is a COMPONENT, not the cover. Every replacement here
finds its target by alt text, deletes that specific image, and re-uploads with
the same alt so the next run finds it again.

COLORWAY COVERS DRIVE THE SWATCH. Each Travel Kit variant carries an image_id
pointing at its colorway cover, so deleting and re-uploading orphans nine
variants until they are re-wired. That re-wiring is not optional and is
verified at the end by re-reading the product.

Lifestyle shots are appended and deliberately NOT wired to any variant: they
show the product in use rather than a specific colourway, and wiring one to a
variant would make the swatch show a dog instead of the colour chosen.

    python config/apply_wave1_lifestyle.py            # plan
    python config/apply_wave1_lifestyle.py --apply
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = (r'C:\Users\mattm\AppData\Local\Temp\claude'
           r'\C--Users-mattm-OneDrive-Claude-Code-Pet-Store'
           r'\040c7b44-775a-401d-a2fd-6844cb38bb7f\scratchpad\wave1')

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

# handle -> (filename, alt) appended, not wired to any variant
LIFESTYLE = {
 'wagvive-led-safety-halo-collar':
    ('halo-lifestyle.png', 'A dog wearing the Wagvive LED Safety Halo Collar, lit at dusk'),
 'wagvive-3-in-1-travel-bowl':
    ('bowl-lifestyle.png', 'A dog drinking from the Wagvive 3-in-1 Travel Bowl outdoors'),
}

# Travel Kit covers, matched and replaced by ALT TEXT.
KIT_HANDLE = 'travel-kit'
COVERS = [
 ('travel-kit-flatlay.png', 'Travel Kit - everything included', None),
 ('travel-kit-blue.png',    'Travel Kit - Blue',    'Blue'),
 ('travel-kit-natural.png', 'Travel Kit - Natural', 'Natural'),
 ('travel-kit-pink.png',    'Travel Kit - Pink',    'Pink'),
]


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                b = r.read().decode()
            time.sleep(0.7)
            return json.loads(b) if b.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409, 500, 502, 503) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit(f'{method} {path}: {exc.code} '
                             f'{exc.read().decode()[:300]}')
    return {}


def product(handle):
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] == handle:
            return p
    return None


def upload(pid, filename, alt, position=None):
    with open(os.path.join(SCRATCH, filename), 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode()
    body = {'image': {'attachment': b64, 'alt': alt}}
    if position:
        body['image']['position'] = position
    return api('POST', f'products/{pid}/images.json', body)['image']


def main():
    apply = '--apply' in sys.argv
    missing = [f for f, _ in LIFESTYLE.values()
               if not os.path.exists(os.path.join(SCRATCH, f))]
    missing += [f for f, _, _ in COVERS
                if not os.path.exists(os.path.join(SCRATCH, f))]
    if missing:
        print('MISSING renders, nothing written:')
        for m in missing:
            print('  ! ' + m)
        return 1

    for handle, (fn, alt) in LIFESTYLE.items():
        p = product(handle)
        have = any(i.get('alt') == alt for i in p['images'])
        print(f"{p['title'][:40]:42} {len(p['images'])} images  "
              f"{'lifestyle already present' if have else 'will append ' + fn}")

    kit = product(KIT_HANDLE)
    print(f"\n{kit['title']}  {len(kit['images'])} images, "
          f"{len(kit['variants'])} variants")
    for fn, alt, cw in COVERS:
        match = [i for i in kit['images'] if i.get('alt') == alt]
        print(f"   {alt:36} {len(match)} existing -> replace with {fn}")

    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    # ---- lifestyle -------------------------------------------------------
    for handle, (fn, alt) in LIFESTYLE.items():
        p = product(handle)
        if any(i.get('alt') == alt for i in p['images']):
            print(f'  {handle}: lifestyle already there, skipped')
            continue
        img = upload(p['id'], fn, alt)
        print(f"  {p['title'][:38]:40} + lifestyle image {img['id']}")

    # ---- kit covers ------------------------------------------------------
    kit = product(KIT_HANDLE)
    pid = kit['id']
    new_ids = {}
    for fn, alt, cw in COVERS:
        for old in [i for i in kit['images'] if i.get('alt') == alt]:
            api('DELETE', f"products/{pid}/images/{old['id']}.json")
            print(f"  deleted old {alt}")
        img = upload(pid, fn, alt, position=1 if cw is None else None)
        new_ids[cw] = img['id']
        print(f"  uploaded {alt} -> {img['id']}")

    # ---- re-wire the colorway swatches, from a RE-READ --------------------
    fresh = api('GET', f'products/{pid}.json')['product']
    wired = 0
    for v in fresh['variants']:
        cw = next((o for o in (v.get('option1'), v.get('option2'))
                   if o in new_ids), None)
        if not cw:
            print(f"  ! no colorway image for variant {v['title']}")
            continue
        api('PUT', f"variants/{v['id']}.json",
            {'variant': {'id': v['id'], 'image_id': new_ids[cw]}})
        wired += 1
    print(f"  re-wired {wired}/{len(fresh['variants'])} kit variants")

    # ---- verify ----------------------------------------------------------
    print('\n--- verify (re-fetched) ---')
    bad = 0
    for handle, (fn, alt) in LIFESTYLE.items():
        p = product(handle)
        ok = any(i.get('alt') == alt for i in p['images'])
        print(f"  {p['title'][:38]:40} lifestyle {'present' if ok else 'MISSING'}")
        bad += not ok
    kit = product(KIT_HANDLE)
    unwired = [v['title'] for v in kit['variants'] if not v.get('image_id')]
    covers = {i.get('alt') for i in kit['images']}
    for _fn, alt, _cw in COVERS:
        ok = alt in covers
        print(f"  {alt:38} {'present' if ok else 'MISSING'}")
        bad += not ok
    print(f"  Travel Kit unwired variants: {len(unwired)}")
    bad += len(unwired)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
