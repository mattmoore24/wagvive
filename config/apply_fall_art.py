#!/usr/bin/env python3
"""Put house-style art on the fall products and wire it per variant.

The fall lineup launched on CJ's own photography so it could be live before
Halloween. This replaces that with cream #F7F2E9 studio shots matching the rest
of the catalogue, and points `variant.image_id` at the right colour so the
swatches actually swap the photo.

WHY variant.image_id MATTERS BEYOND THE GALLERY. It drives the CART THUMBNAIL.
Without it a customer who picked the Black hoodie sees the grey one at the exact
moment they are deciding whether to buy. Single-variant products need it too.

Art lands in config/branding/fall/<handle>__<option value>.jpg, mirroring the
kit-cover convention, so a rerun is idempotent and the repo holds the masters.

Idempotent: an image already on the product with the same filename is reused
rather than duplicated, but the variant wiring is re-asserted every run because
that is what silently comes undone.

    python config/apply_fall_art.py            # report
    python config/apply_fall_art.py --apply
"""
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'config', 'branding', 'fall')
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
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')

# handle -> which option index carries the look. None means single-image product.
LOOK_OPTION = {
    'wagvive-pumpkin-hoodie': 'Color',
    'wagvive-big-dog-costume': 'Design',
    'wagvive-thanksgiving-turkey-coat': 'Design',
    'wagvive-jack-o-lantern-sweater': 'Color',
    # Both colourways differ only by a small button accent and CJ photographs
    # only one, so a single shared master is honest here rather than inventing
    # a pink-button render nobody has seen.
    'wagvive-steam-grooming-brush': None,
    'wagvive-glow-skeleton-suit': None,
    'wagvive-ball-launcher': None,
    'wagvive-pumpkin-snuffle-mat': None,
    'wagvive-roast-turkey-sniff-toy': None,
    'wagvive-pumpkin-chew-toy': None,
}


def api(method, path, payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def by_handle(handle):
    for st in ('active', 'draft', 'archived'):
        ps = api('GET', f'products.json?handle={handle}&limit=1&status={st}'
                 ).get('products') or []
        if ps:
            return ps[0]
    return None


def prep(path):
    im = Image.open(path).convert('RGB').resize((OUT_PX, OUT_PX), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=92, optimize=True)
    return buf.getvalue()


def art_files():
    """{handle: {option value or '_': path}} from config/branding/fall/."""
    out = {}
    if not os.path.isdir(ART):
        return out
    for fn in sorted(os.listdir(ART)):
        if not fn.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        stem = os.path.splitext(fn)[0]
        handle, sep, look = stem.partition('__')
        out.setdefault(handle, {})[look if sep else '_'] = os.path.join(ART, fn)
    return out


def main():
    apply = '--apply' in sys.argv
    files = art_files()
    if not files:
        print(f'no art in {os.path.relpath(ART, ROOT)}')
        return 1

    problems = []
    for handle, looks in sorted(files.items()):
        p = by_handle(handle)
        if not p:
            print(f'{handle}: product not found')
            problems.append(handle)
            continue
        opt_name = LOOK_OPTION.get(handle, '_')
        opt_idx = None
        if opt_name:
            names = [o['name'] for o in p['options']]
            if opt_name not in names:
                print(f"{handle}: no option named {opt_name!r}, has {names}")
                problems.append(handle)
                continue
            opt_idx = names.index(opt_name) + 1

        print(f"\n{p['title']}  ({len(looks)} image(s), "
              f"{len(p['variants'])} variants)")
        for look, path in sorted(looks.items()):
            fname = f"{handle}__{look}.jpg" if look != '_' else f"{handle}.jpg"
            targets = ([v for v in p['variants']
                        if str(v.get(f'option{opt_idx}') or '') == look]
                       if opt_idx else list(p['variants']))
            print(f"   {look:18} -> {len(targets)} variant(s)")
            if not targets:
                print(f"      !! no variant has {opt_name} == {look!r}")
                problems.append(handle)
                continue
            if not apply:
                continue

            existing = next((im for im in p['images']
                             if fname in im['src'].split('/')[-1]), None)
            if existing:
                img_id = existing['id']
            else:
                img_id = api('POST', f"products/{p['id']}/images.json", {'image': {
                    'attachment': base64.b64encode(prep(path)).decode(),
                    'filename': fname,
                    'alt': f"{p['title']}" + (f" - {look}" if look != '_' else ''),
                }})['image']['id']
                print(f"      uploaded {fname}")
            for v in targets:
                api('PUT', f"variants/{v['id']}.json",
                    {'variant': {'id': v['id'], 'image_id': img_id}})
            print(f"      wired {len(targets)} variant(s)")

    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    # verify against the live product, not the writes
    print('\n--- verify ---')
    for handle in sorted(files):
        p = by_handle(handle)
        if not p:
            continue
        unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
        state = 'ok' if not unwired else f'{len(unwired)} UNWIRED'
        print(f"{p['title']:44} {len(p['images'])} img  {state}")
        if unwired:
            problems.append(handle)
    if problems:
        print(f'\n{len(set(problems))} product(s) need attention')
        return 1
    print('\nEvery variant points at art.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
