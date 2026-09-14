#!/usr/bin/env python3
"""Photography for the Wagvive Hot Dog Costume, and the variant wiring.

House format, matching the other costumes and the calming vest:
  1. a studio flat-lay on cream #F7F2E9 (the Big Dog Costume's format), which
     leads and is wired to EVERY variant, because there is one design and size
     does not change what it looks like;
  2. a lifestyle shot on a large dog (Golden Retriever), and
  3. a lifestyle shot on a small dog (Bichon Frise), NOT wired to any variant.

TWO lifestyle shots rather than the vest's one, on purpose: this costume runs
S to XL, and the owner asked that the sizing look right in the images. One big
dog and one small dog, each wearing it at the proportion CJ's own photos show
(bun from behind the shoulders to the hips, head, legs and tail free), is the
honest way to show the range.

Every render was generated from CJ's own photos as references and eyeballed
against them before upload (CLAUDE.md, imagery).

FILENAMES ARE LOAD-BEARING. `audit_fall_imagery.py` counts an image as house
art only when its Shopify filename starts with the product handle. The first
upload sent no filename, Shopify named the files itself, and the audit failed
all three as "unknown". So the art lives in the repo under handle-prefixed
names and is uploaded with `filename` set:

    config/branding/fall/wagvive-hot-dog-costume.jpg            the lead shot
    config/branding/fall-lifestyle/wagvive-hot-dog-costume__*.jpg  lifestyle

`fall-lifestyle/` is its own folder so that neither apply_fall_art.py (which
matches `__<look>` against option values) nor apply_fall_detail.py (one detail
shot per product) picks these up. Matched and replaced BY ALT TEXT, never by
position. 1600 x 1600 JPEG, like the other costume photos.

    python config/apply_hot_dog_images.py            # plan
    python config/apply_hot_dog_images.py --apply
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALL = os.path.join(ROOT, 'config', 'branding', 'fall')
LIFE = os.path.join(ROOT, 'config', 'branding', 'fall-lifestyle')

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

HANDLE = 'wagvive-hot-dog-costume'
TITLE = 'Wagvive Hot Dog Costume'

# (path, alt, wire to every variant?)
IMAGES = [
    (os.path.join(FALL, f'{HANDLE}.jpg'), TITLE, True),
    (os.path.join(LIFE, f'{HANDLE}__large-dog.jpg'), f'{TITLE} on a large dog', False),
    (os.path.join(LIFE, f'{HANDLE}__small-dog.jpg'), f'{TITLE} on a small dog', False),
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
            if e.code in (429, 409, 500, 502, 503, 504) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {body}')
    return {}


def product():
    # No `status` parameter: REST ignores `status=any` and returns nothing.
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] == HANDLE:
            return p
    return None


def upload(pid, path, alt, position):
    with open(path, 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return api('POST', f'products/{pid}/images.json',
               {'image': {'attachment': b64, 'filename': os.path.basename(path),
                          'alt': alt, 'position': position}})['image']


def shopify_name(img):
    return img['src'].split('/')[-1].split('?')[0]


def main():
    apply = '--apply' in sys.argv
    missing = [p for p, _, _ in IMAGES if not os.path.exists(p)]
    if missing:
        print('MISSING art, nothing written:', missing)
        return 1
    p = product()
    if not p:
        print(f'{HANDLE} does not exist. Run add_hot_dog_costume.py --apply.')
        return 1
    print(f"{p['title']}  id={p['id']}  status={p['status']}  "
          f"{len(p['images'])} images, {len(p['variants'])} variants")
    for path, alt, wire in IMAGES:
        have = [i for i in p['images'] if i.get('alt') == alt]
        print(f"   {alt:44} {len(have)} existing -> {os.path.basename(path)}"
              f"{'  (wired to all variants)' if wire else '  (not wired)'}")
    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    pid = p['id']
    lead = None
    for n, (path, alt, wire) in enumerate(IMAGES, start=1):
        for old in [i for i in p['images'] if i.get('alt') == alt]:
            api('DELETE', f"products/{pid}/images/{old['id']}.json")
            print(f'  deleted old {alt}')
        img = upload(pid, path, alt, n)
        if wire:
            lead = img['id']
        print(f"  uploaded {alt} -> {img['id']}")

    fresh = api('GET', f'products/{pid}.json')['product']
    for v in fresh['variants']:
        api('PUT', f"variants/{v['id']}.json",
            {'variant': {'id': v['id'], 'image_id': lead}})
    print(f"  wired {len(fresh['variants'])} variants to the flat-lay")

    print('\n--- verify, re-fetched (each variant by id) ---')
    again = api('GET', f'products/{pid}.json')['product']
    by_alt = {i.get('alt'): i for i in again['images']}
    bad = 0
    for n, (_path, alt, _w) in enumerate(IMAGES, start=1):
        i = by_alt.get(alt)
        ok = (bool(i) and i['position'] == n
              and shopify_name(i).startswith(HANDLE))
        print(f"  {alt:44} {'pos ' + str(i['position']) if i else 'MISSING'} "
              f"{shopify_name(i) if i else ''}  {'ok' if ok else 'WRONG'}")
        bad += not ok
    if len(again['images']) != len(IMAGES):
        print(f"  ! product carries {len(again['images'])} images, "
              f"expected {len(IMAGES)}")
        bad += 1
    for v in again['variants']:
        vv = api('GET', f"variants/{v['id']}.json")['variant']
        ok = vv.get('image_id') == lead
        print(f"  {vv['title']:4} image_id {vv.get('image_id')} "
              f"{'ok' if ok else 'WRONG'}")
        bad += not ok
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
