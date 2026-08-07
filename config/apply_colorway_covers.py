#!/usr/bin/env python3
"""Give every kit colorway its own cover, and wire it to that colorway's variants.

WHY. After the Size + Colorway rebuild all variants of a kit shared one photo, so
picking Pink still showed the blue set. The cover is the only thing a shopper
sees before deciding, and showing them the wrong colour set is worse than showing
them a grid.

WHAT IT DOES. For each file in config/branding/kit-covers/colorway/ named
`<kit handle>__<colorway>.jpg`, upload it as product media, then point
`variant.image_id` at it for EVERY variant of that kit whose colorway matches.
Size is deliberately not part of the filename: a Small and a Large kit contain
the same colours and photograph identically, so the three sizes share one image
rather than tripling the shoot for no visible difference.

Wiring by variant matters beyond the gallery. `variant.image_id` is what drives
the cart thumbnail, so without it a customer who picked Pink sees the blue set
again at the moment they are deciding whether to buy.

Idempotent: an already-uploaded colorway (matched by filename) is reused rather
than duplicated, so this can be re-run as more colorways are shot.

    python config/apply_colorway_covers.py            # report
    python config/apply_colorway_covers.py --apply
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from kit_colorways import KITS                       # noqa: E402

ART = os.path.join(ROOT, 'config', 'branding', 'kit-covers', 'colorway')
OUT_PX = 1600

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


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read().decode()
            time.sleep(0.6)
            return json.loads(b) if b.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise
    return {}


def main():
    apply = '--apply' in sys.argv
    if not os.path.isdir(ART):
        print(f'no artwork at {os.path.relpath(ART, ROOT)}')
        return 1

    art = {}
    for f in sorted(os.listdir(ART)):
        if not f.lower().endswith(('.jpg', '.png')):
            continue
        stem = os.path.splitext(f)[0]
        if '__' not in stem:
            print(f'!! {f}: expected "<kit handle>__<colorway>"')
            continue
        handle, cw = stem.split('__', 1)
        art.setdefault(handle, {})[cw] = os.path.join(ART, f)

    prods = {p['handle']: p for p in
             api('GET', 'products.json?limit=250&status=active')['products']}

    # every colorway the design expects, so gaps are reported not ignored
    expected = {}
    for kit_title, spec in KITS.items():
        h = next((p['handle'] for p in prods.values() if p['title'] == kit_title),
                 None)
        if h:
            expected[h] = set(spec['values'])

    total_wired, missing = 0, []
    for handle, want_cws in sorted(expected.items()):
        have = art.get(handle, {})
        gap = sorted(want_cws - set(have))
        p = prods[handle]
        print(f"\n{p['title']}  ({len(have)}/{len(want_cws)} colorways shot)")
        if gap:
            print(f'   still to shoot: {gap}')
            missing += [f'{handle}__{c}' for c in gap]

        for cw, path in sorted(have.items()):
            fname = f'kit-{handle}-{cw.lower().replace(" ", "-")}.jpg'
            targets = [v for v in p['variants']
                       if any(str(v.get(f'option{i}') or '') == cw
                              for i in (1, 2, 3))]
            existing = next((im for im in p['images']
                             if fname in im['src'].split('/')[-1]), None)
            print(f'   {cw:12} -> {len(targets)} variant(s)'
                  f'{"  [already uploaded]" if existing else ""}')
            if not apply:
                continue
            if not targets:
                print(f'      !! no variant has colorway {cw!r}, skipped')
                continue

            if existing:
                img_id = existing['id']
            else:
                im = Image.open(path).convert('RGB')
                im = im.resize((OUT_PX, OUT_PX), Image.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, 'JPEG', quality=92, optimize=True)
                img_id = api('POST', f"products/{p['id']}/images.json", {'image': {
                    'attachment': base64.b64encode(buf.getvalue()).decode(),
                    'filename': fname,
                    'alt': f"{p['title']} - {cw}",
                }})['image']['id']

            api('PUT', f"products/{p['id']}/images/{img_id}.json", {'image': {
                'id': img_id, 'variant_ids': [v['id'] for v in targets]}})
            total_wired += len(targets)

        if apply:
            fresh = api('GET', f"products/{p['id']}.json")['product']
            unwired = [v['title'] for v in fresh['variants'] if not v.get('image_id')]
            done = len(fresh['variants']) - len(unwired)
            print(f"   {'OK ' if not unwired else '.. '}{done}/{len(fresh['variants'])} "
                  f"variants now carry a colorway image")
            if unwired:
                print(f'      not yet: {unwired[:6]}')

    print('\n' + '=' * 62)
    if not apply:
        print('Dry run. Use --apply to upload and wire.')
        return 0
    print(f'wired {total_wired} variant(s)')
    if missing:
        print(f'{len(missing)} colorway cover(s) still to shoot: {missing}')
        return 1
    print('every colorway of every kit has its own cover')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
