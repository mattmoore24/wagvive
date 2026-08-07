#!/usr/bin/env python3
"""Give every kit a cover image built from its actual components.

Bundles created through productBundleCreate have no media at all, so all four
kits were showing a blank placeholder - the single worst thing a product can do
on a collection page.

Rather than picking one component's photo and pretending it represents the kit,
this composes a 2x2 grid of the components on the brand background, so the cover
answers the only question a kit cover needs to answer: what do I get. Components
are read from the live bundle, so a rebuilt kit regenerates correctly.

No text is drawn into the image. Text baked into product photography is exactly
what this audit was cleaning up elsewhere, and it does not survive being
rendered at thumbnail size anyway.

SUPERSEDED FOR THE SIX LIVE KITS (2026-08-07). Every current kit now carries a
styled Runway flat-lay published by `config/apply_kit_covers.py`; the grid read
as a contact sheet rather than a product. This generator stays because it is the
fallback for a NEW kit that has no art yet, and because it needs no art director
when a composition changes.

**Do not run this with `--force`.** Without it the script skips any kit that
already has images, which is what protects the flat-lays. With it, every cover
reverts to a grid and the gallery gains a duplicate of every component shot.
"""
import io, json, os, sys, urllib.error, urllib.request

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'config', 'branding', 'kit-covers')
CANVAS = 1400
PAD = 40
GAP = 24
BG = (245, 241, 232)      # matches the storefront background
TILE_BG = (255, 255, 255)
RADIUS = 28

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

BUNDLE_Q = """
query($id: ID!) {
  product(id: $id) {
    title
    variants(first: 3) {
      nodes {
        productVariantComponents(first: 20) {
          nodes { productVariant { product { id title featuredMedia { preview { image { url } } } } } }
        }
      }
    }
  }
}
"""


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def rounded(im, radius):
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0], im.size[1]],
                                           radius=radius, fill=255)
    out = Image.new('RGB', im.size, BG)
    out.paste(im, (0, 0), mask)
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return Image.open(io.BytesIO(r.read())).convert('RGB')


def compose(images):
    """Grid covering EVERY component. Each gets an equal, square, white tile.

    This used to be a fixed 2x2 that took images[:4], which was correct when
    every kit had four components. The 2026-08-04 rebuild moved five of the six
    kits to FIVE components, so the cover silently dropped one item from each:
    the Travel Kit advertised four pieces while selling five. A cover that
    understates the offer is a straight conversion loss on the page we buy
    traffic for, and nothing flagged it.

    Layout is derived from the count, and the final row is centered so a
    five-item kit reads as 3 over 2 rather than 3 over 2-shoved-left.
    """
    n = len(images)
    if n <= 1:
        cols = 1
    elif n <= 4:
        cols = 2
    else:
        cols = 3
    rows = (n + cols - 1) // cols

    side = min((CANVAS - 2 * PAD - (cols - 1) * GAP) // cols,
               (CANVAS - 2 * PAD - (rows - 1) * GAP) // rows)

    canvas = Image.new('RGB', (CANVAS, CANVAS), BG)
    total_h = rows * side + (rows - 1) * GAP
    oy = (CANVAS - total_h) // 2

    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)          # this row may be short
        row_w = in_row * side + (in_row - 1) * GAP
        ox = (CANVAS - row_w) // 2                 # center every row
        tile = Image.new('RGB', (side, side), TILE_BG)
        # contain, not crop - a cropped product photo loses the product
        pic = im.copy()
        pic.thumbnail((side - 40, side - 40), Image.LANCZOS)
        tile.paste(pic, ((side - pic.width) // 2, (side - pic.height) // 2))
        tile = rounded(tile, RADIUS)
        canvas.paste(tile, (ox + c * (side + GAP), oy + r * (side + GAP)))
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    # Bundles are the only products with no SKU on any variant.
    kits = [p for p in api('GET', 'products.json?limit=250&status=active')['products']
            if not any(v.get('sku') for v in p['variants'])]
    # Idempotent by default: a kit that already has a gallery keeps it, otherwise
    # rerunning after one kit is rebuilt duplicates every image on the other three.
    if '--force' not in sys.argv:
        skipped = [k['title'] for k in kits if k['images']]
        kits = [k for k in kits if not k['images']]
        for t in skipped:
            print(f'{t:28} already has images, skipped')
    if not kits:
        print('nothing to do'); return

    for k in kits:
        d = gql(BUNDLE_Q, {'id': f'gid://shopify/Product/{k["id"]}'})['data']['product']
        comps, seen = [], set()
        for v in d['variants']['nodes']:
            for c in v['productVariantComponents']['nodes']:
                p = c['productVariant']['product']
                # variant-selectable bundles repeat every component per parent
                # variant; one tile per component product, not per combination
                if p['id'] in seen:
                    continue
                seen.add(p['id'])
                media = (p.get('featuredMedia') or {}).get('preview', {}).get('image', {})
                if media.get('url'):
                    comps.append((p['title'], media['url']))
        if not comps:
            print(f'{d["title"]:28} no component images'); continue

        images = []
        for title, url in comps:      # every component, not the first four
            try:
                images.append(fetch(url))
            except Exception as exc:
                print(f'   {title[:30]} image failed: {str(exc)[:50]}')
        if not images:
            print(f'{d["title"]:28} no usable images'); continue

        cover = compose(images)
        path = os.path.join(OUT, f'{k["id"]}.jpg')
        cover.save(path, quality=92)

        # Cover goes first; component shots follow so the gallery still shows detail.
        import base64
        with open(path, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()
        api('POST', f'products/{k["id"]}/images.json', {'image': {
            'attachment': b64, 'filename': f'kit-{k["id"]}.jpg',
            'alt': f'{d["title"]} - everything included', 'position': 1}})
        # gallery carries EVERY component, even when the cover grid holds 4
        for n, (title, url) in enumerate(comps, 2):
            api('POST', f'products/{k["id"]}/images.json',
                {'image': {'src': url, 'alt': title, 'position': n}})

        fresh = api('GET', f'products/{k["id"]}.json')['product']
        print(f'{d["title"]:28} cover + {len(fresh["images"]) - 1} component shots')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
