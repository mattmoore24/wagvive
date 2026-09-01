#!/usr/bin/env python3
"""Upload the wave-1 US-warehouse renders and wire every variant to its colour.

Colour-level images: one photo per colourway, wired to EVERY variant of that
colour. The Halo Collar has 5 colours x 3 sizes, so five photos cover fifteen
variants; the Travel Bowl has 4 colours across 6 variants.

WHY EVERY VARIANT MUST BE WIRED. `variant.image_id` is what makes the swatch
swap the photo, and it is also what the cart thumbnail reads. A variant with no
image_id shows the product's first image regardless of what the customer chose,
so a customer who picked Hot Pink sees Blue in their cart. CLAUDE.md requires
it even on single-variant products for exactly that reason.

ORDER MATTERS. Images are uploaded first and the variant wiring is a SECOND
pass, because Shopify assigns image ids on create and they are not knowable in
advance. The wiring pass re-reads the product rather than trusting the create
response.

    python config/apply_us_wave1_images.py            # show the plan
    python config/apply_us_wave1_images.py --apply
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

# handle -> [(colour, filename)]. Order here is the gallery order; the first
# entry becomes the product's cover.
PLAN = {
 'wagvive-led-safety-halo-collar': [
   ('Blue', 'halo-master-blue.png'),
   ('Red', 'halo-red.png'),
   ('Orange', 'halo-orange.png'),
   ('Hot Pink', 'halo-hot-pink.png'),
   ('Green', 'halo-green.png'),
 ],
 'wagvive-3-in-1-travel-bowl': [
   ('Green', 'bowl-master-green.png'),
   ('Blue', 'bowl-blue.png'),
   ('Pink', 'bowl-pink.png'),
   ('Yellow', 'bowl-yellow.png'),
 ],
}
TITLES = {'wagvive-led-safety-halo-collar': 'Wagvive LED Safety Halo Collar',
          'wagvive-3-in-1-travel-bowl': 'Wagvive 3-in-1 Travel Bowl'}


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


def main():
    apply = '--apply' in sys.argv
    missing = []
    for handle, rows in PLAN.items():
        for colour, fn in rows:
            if not os.path.exists(os.path.join(SCRATCH, fn)):
                missing.append(fn)
    if missing:
        print('MISSING renders, nothing written:')
        for m in missing:
            print('  ! ' + m)
        return 1

    for handle, rows in PLAN.items():
        p = product(handle)
        if not p:
            print(f'{handle}: product not found'); return 1
        print(f"\n{TITLES[handle]}  id={p['id']}  "
              f"{len(p['variants'])} variants, {len(p['images'])} images now")
        for colour, fn in rows:
            n = sum(1 for v in p['variants']
                    if colour in (v.get('option1'), v.get('option2')))
            print(f'   {colour:10} {fn:24} -> {n} variant(s)')

    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    for handle, rows in PLAN.items():
        p = product(handle)
        pid = p['id']
        title = TITLES[handle]

        # ---- pass 1: upload -------------------------------------------------
        by_colour = {}
        for pos, (colour, fn) in enumerate(rows, start=1):
            with open(os.path.join(SCRATCH, fn), 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
            img = api('POST', f'products/{pid}/images.json', {'image': {
                'attachment': b64, 'position': pos,
                'alt': f'{title}, {colour}'}})['image']
            by_colour[colour] = img['id']
            print(f"  uploaded {colour:10} image {img['id']}")

        # ---- pass 2: wire variants, from a RE-READ, not the create response --
        fresh = api('GET', f'products/{pid}.json')['product']
        wired = 0
        for v in fresh['variants']:
            colour = next((c for c in by_colour
                           if c in (v.get('option1'), v.get('option2'))), None)
            if not colour:
                print(f"  ! no colour match for variant {v['title']}")
                continue
            api('PUT', f"variants/{v['id']}.json",
                {'variant': {'id': v['id'], 'image_id': by_colour[colour]}})
            wired += 1
        print(f'  wired {wired}/{len(fresh["variants"])} variants')

    # ---- verify ------------------------------------------------------------
    print('\n--- verify (re-fetched) ---')
    bad = 0
    for handle in PLAN:
        p = product(handle)
        unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
        print(f"  {TITLES[handle][:40]:42} images={len(p['images'])} "
              f"unwired={len(unwired)}")
        if unwired:
            print(f'      {unwired}')
        bad += len(unwired)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
