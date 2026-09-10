#!/usr/bin/env python3
"""Photography for the Calming Hooded Anxiety Vest, and the variant wiring.

TWO STUDIO SHOTS AND ONE LIFESTYLE, following the house pipeline: shoot a
MASTER (Dark Blue), then RECOLOUR the approved master so the pose stays locked,
rather than shooting each colour separately and getting two different garments.

Both were eyeballed against the CJ gallery reference before upload, which is
not optional here - the model has previously invented a five-finger glove for
an oval mitt and a quilted sofa cover for a plush throw. What had to be right:
navy or charcoal soft knit, BLACK binding tape on the hem and both leg
openings, one silver-grey reflective strip per flank, black hook-and-loop belly
straps, and the tall tube snood. The first grey recolour came back warm taupe
instead of CJ's cool charcoal and was rejected and reshot.

MATCHED AND REPLACED BY ALT TEXT, NEVER BY POSITION. `apply_kit_covers.py` used
to replace "position 1" and ate two component photos doing it: once an image is
deleted, position 1 is something else.

EVERY VARIANT GETS AN image_id, INCLUDING FOR A COLOUR-ONLY PHOTO SET. All four
sizes of a colour share that colour's photo, because size does not change what
the garment looks like. Without this the colour swatch does not swap the photo
and the cart thumbnail is blank. `replace_thunder_wrap.py --finish` refuses to
publish until this has run.

The lifestyle shot is appended and deliberately NOT wired to any variant: it
shows one colour on one dog, and wiring it would make a swatch show a beagle
instead of the colour chosen.

    python config/apply_wrap_images.py            # plan
    python config/apply_wrap_images.py --apply
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
           r'\040c7b44-775a-401d-a2fd-6844cb38bb7f\scratchpad\vest')

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

HANDLE = 'wagvive-calming-hooded-anxiety-vest'
TITLE = 'Wagvive Calming Hooded Anxiety Vest'

# (filename, alt, colour this photo represents or None for the lifestyle shot)
IMAGES = [
    ('master-vest-blue.png', f'{TITLE}, Dark Blue', 'Dark Blue'),
    ('master-vest-grey.png', f'{TITLE}, Dark Grey', 'Dark Grey'),
    ('vest-lifestyle.png',   f'{TITLE} in use',     None),
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


def upload(pid, filename, alt, position=None):
    with open(os.path.join(SCRATCH, filename), 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode()
    body = {'image': {'attachment': b64, 'alt': alt}}
    if position:
        body['image']['position'] = position
    return api('POST', f'products/{pid}/images.json', body)['image']


def main():
    apply = '--apply' in sys.argv
    missing = [f for f, _, _ in IMAGES
               if not os.path.exists(os.path.join(SCRATCH, f))]
    if missing:
        print('MISSING renders, nothing written:')
        for m in missing:
            print('  ! ' + m)
        return 1

    p = product()
    if not p:
        print(f'{HANDLE} does not exist. Run replace_thunder_wrap.py --apply.')
        return 1
    print(f"{p['title']}  id={p['id']}  status={p['status']}")
    print(f"  {len(p['images'])} images, {len(p['variants'])} variants")
    for fn, alt, colour in IMAGES:
        have = [i for i in p['images'] if i.get('alt') == alt]
        print(f"   {alt[:48]:50} {len(have)} existing -> {fn}"
              f"{'  (wires ' + colour + ')' if colour else '  (not wired)'}")
    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    pid = p['id']
    by_colour = {}
    for n, (fn, alt, colour) in enumerate(IMAGES, start=1):
        for old in [i for i in p['images'] if i.get('alt') == alt]:
            api('DELETE', f"products/{pid}/images/{old['id']}.json")
            print(f'  deleted old {alt}')
        img = upload(pid, fn, alt, position=n)
        if colour:
            by_colour[colour] = img['id']
        print(f"  uploaded {alt} -> {img['id']}")

    # Wire from a RE-READ, not from the create response.
    fresh = api('GET', f'products/{pid}.json')['product']
    wired = 0
    for v in fresh['variants']:
        colour = next((o for o in (v.get('option1'), v.get('option2'))
                       if o in by_colour), None)
        if not colour:
            print(f"  ! no photo for variant {v['title']}")
            continue
        api('PUT', f"variants/{v['id']}.json",
            {'variant': {'id': v['id'], 'image_id': by_colour[colour]}})
        wired += 1
    print(f"  wired {wired}/{len(fresh['variants'])} variants")

    print('\n--- verify, re-fetched ---')
    again = api('GET', f'products/{pid}.json')['product']
    alts = {i.get('alt'): i['id'] for i in again['images']}
    bad = 0
    for _fn, alt, _c in IMAGES:
        ok = alt in alts
        print(f"  {alt[:50]:52} {'present' if ok else 'MISSING'}")
        bad += not ok
    for v in again['variants']:
        want = by_colour.get(v.get('option1')) or by_colour.get(v.get('option2'))
        ok = v.get('image_id') == want
        print(f"  {v['title']:16} image_id {v.get('image_id')} "
              f"{'ok' if ok else 'WRONG'}")
        bad += not ok
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
