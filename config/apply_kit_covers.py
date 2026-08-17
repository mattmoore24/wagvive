#!/usr/bin/env python3
"""Replace each kit's tiled grid cover with a styled flat-lay photograph.

WHY. `make_kit_covers.py` composes the cover as a grid of the component product
shots on the brand background. That is honest and never goes stale, but it reads
as a contact sheet, not as a product. The kits are the catalogue's best AOV lever
and the collection card is the only thing a shopper sees before deciding to click,
so the cover is worth real photography.

These flat-lays are generated with Runway from the SAME component photos used as
tagged references, then eyeballed one by one against those references before they
land here. Two takes were rejected outright: the Sneaker Chew Buddy rendered as an
actual child's shoe rather than a soft chew toy, and the sloth's heartbeat module
came back wearing garbled pseudo-lettering. That check is not optional. The model
will happily invent a plausible product that we do not sell.

The grid generator stays in the repo and stays correct: it is still the fallback
for a newly built kit that has no art yet, and it is what regenerates a cover when
a kit's composition changes before anyone has time to shoot a new flat-lay.

Only the cover is replaced, and it is found by its ALT (`<title> - everything
included`), never by being position 1. The per-component gallery shots below it
are left exactly as they are, because those are what `audit_kits.py` reads to
prove the gallery still matches the bundle. Trusting position 1 destroyed the
Slow Feeder Bowl and Barnyard Squeaker stills on 2026-08-17: reshooting a cover
means deleting the old one first (these scripts are idempotent by filename, so
an unchanged name is otherwise skipped), which promotes a component still into
position 1 for exactly as long as it takes this script to overwrite it.

    python config/apply_kit_covers.py            # report what would change
    python config/apply_kit_covers.py --apply
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'config', 'branding', 'kit-covers', 'flatlay')
OUT_PX = 1600
BG_TOL = 14        # per-channel distance from the corner colour that counts as content
MIN_OFFSET = 0.02  # recentre only if the content is off by more than this

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
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode()
            time.sleep(0.55)          # REST is capped at 2 calls/second
            return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            # 429 is the documented rate limit; 409 means Shopify is still
            # settling a previous write to the same product.
            if exc.code in (429, 409) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def content_box(im):
    """Bounding box of everything that is not the seamless background.

    The background is a soft cream with a gentle vignette, so a flat colour
    match misses the corners. Difference against the mean of the four corner
    patches, then threshold, which keeps contact shadows (they are part of the
    composition) without treating the vignette as an object.
    """
    w, h = im.size
    s = max(w // 40, 8)
    patches = [im.crop(b) for b in ((0, 0, s, s), (w - s, 0, w, s),
                                    (0, h - s, s, h), (w - s, h - s, w, h))]
    px = [p.resize((1, 1), Image.LANCZOS).getpixel((0, 0)) for p in patches]
    bg = tuple(sum(c[i] for c in px) // len(px) for i in range(3))

    diff = ImageChops.difference(im, Image.new('RGB', im.size, bg))
    mask = diff.convert('L').point(lambda v: 255 if v > BG_TOL else 0)
    return mask.getbbox(), bg


def recentre(im):
    """Crop the largest centred square that still holds all the content.

    Cropping rather than translating the pixels: shifting the arrangement would
    leave a rectangle to fill, and any fill shows a seam against the vignette.
    """
    box, _ = content_box(im)
    if not box:
        return im, 'no content detected, left as is'
    w, h = im.size
    cx = (box[0] + box[2]) / 2 / w
    cy = (box[1] + box[3]) / 2 / h
    off = max(abs(cx - 0.5), abs(cy - 0.5))
    if off < MIN_OFFSET:
        return im, f'already centred (off by {off*100:.1f}%)'

    # largest square centred on the content that stays inside the frame
    half = min(cx, 1 - cx, cy, 1 - cy) * min(w, h)
    # ...but never crop into the content itself
    need = max(box[2] - box[0], box[3] - box[1]) / 2 * 1.06
    half = max(half, need)
    ccx, ccy = cx * w, cy * h
    left, top = ccx - half, ccy - half
    right, bottom = ccx + half, ccy + half
    # clamp back inside the canvas if protecting the content pushed us out
    if left < 0:
        right, left = right - left, 0
    if top < 0:
        bottom, top = bottom - top, 0
    if right > w:
        left, right = left - (right - w), w
    if bottom > h:
        top, bottom = top - (bottom - h), h
    left, top = max(left, 0), max(top, 0)
    return im.crop((int(left), int(top), int(right), int(bottom))), \
        f'recentred (was off by {off*100:.1f}%)'


def prep(path):
    im = Image.open(path).convert('RGB')
    im, note = recentre(im)
    im = im.resize((OUT_PX, OUT_PX), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=92, optimize=True)
    return buf.getvalue(), note


def main():
    apply = '--apply' in sys.argv
    if not os.path.isdir(ART):
        print(f'no artwork directory at {os.path.relpath(ART, ROOT)}')
        return 1

    prods = api('GET', 'products.json?limit=250&status=active')['products']
    kits = {p['handle']: p for p in prods
            if not any(v.get('sku') for v in p['variants'])}

    art = {os.path.splitext(f)[0]: os.path.join(ART, f)
           for f in sorted(os.listdir(ART)) if f.lower().endswith(('.png', '.jpg'))}
    missing = [h for h in kits if h not in art]
    unknown = [h for h in art if h not in kits]
    if unknown:
        print(f'!! artwork with no matching kit: {unknown}')
    if missing:
        print(f'   kits with no flat-lay yet (keeping the grid cover): {missing}')

    changed = 0
    for handle, path in art.items():
        k = kits.get(handle)
        if not k:
            continue
        # The old cover is identified by ALT, not by being position 1. Taking
        # whatever sits at position 1 destroyed two component stills on
        # 2026-08-17: the previous cover had been deleted so the reshoot would
        # re-upload, which promoted a component still into position 1, and this
        # then consumed it. When no image carries the cover alt there is nothing
        # to replace and the new cover is simply inserted.
        alt = f"{k['title']} - everything included"
        old = next((i for i in k['images'] if (i.get('alt') or '') == alt), None)
        blob, note = prep(path)
        print(f"\n{k['title']}")
        print(f"   {note}, {len(blob)//1024} KB")
        print(f"   gallery now: {len(k['images'])} image(s), "
              + (f"replacing #{old['id']}" if old
                 else 'no existing cover, inserting'))
        if not apply:
            continue

        # Upload FIRST, delete the old cover second. The reverse order leaves a
        # kit with no cover at all if the upload fails, and a blank product card
        # is worse than a dated one.
        new = api('POST', f"products/{k['id']}/images.json", {'image': {
            'attachment': base64.b64encode(blob).decode(),
            'filename': f'kit-flatlay-{handle}.jpg',
            'alt': alt, 'position': 1}})['image']
        if old:
            api('DELETE', f"products/{k['id']}/images/{old['id']}.json")

        fresh = api('GET', f"products/{k['id']}.json")['product']
        first = fresh['images'][0]
        # Gallery size holds steady on a replace and grows by one on an insert.
        want_n = len(k['images']) + (0 if old else 1)
        ok = (first['id'] == new['id']
              and len(fresh['images']) == want_n
              and (first.get('alt') or '') == alt)
        print(f"   {'OK ' if ok else 'BAD'} cover={first['id']} "
              f"gallery={len(fresh['images'])} alt={first.get('alt')!r}")
        if not ok:
            return 1
        changed += 1

    if not apply:
        print('\nDry run. Use --apply to publish these covers.')
        return 0
    print(f'\n{changed} kit cover(s) replaced and verified')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
