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
    """2x2 grid. Each component gets an equal, square, white tile."""
    n = min(len(images), 4)
    cols = 2 if n > 1 else 1
    rows = 2 if n > 2 else 1
    cell = (CANVAS - 2 * PAD - (cols - 1) * GAP) // cols
    cell_h = (CANVAS - 2 * PAD - (rows - 1) * GAP) // rows
    side = min(cell, cell_h)

    canvas = Image.new('RGB', (CANVAS, CANVAS), BG)
    total_w = cols * side + (cols - 1) * GAP
    total_h = rows * side + (rows - 1) * GAP
    ox = (CANVAS - total_w) // 2
    oy = (CANVAS - total_h) // 2

    for i, im in enumerate(images[:4]):
        tile = Image.new('RGB', (side, side), TILE_BG)
        # contain, not crop - a cropped product photo loses the product
        pic = im.copy()
        pic.thumbnail((side - 40, side - 40), Image.LANCZOS)
        tile.paste(pic, ((side - pic.width) // 2, (side - pic.height) // 2))
        tile = rounded(tile, RADIUS)
        x = ox + (i % cols) * (side + GAP)
        y = oy + (i // cols) * (side + GAP)
        canvas.paste(tile, (x, y))
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
        comps = []
        for v in d['variants']['nodes']:
            for c in v['productVariantComponents']['nodes']:
                p = c['productVariant']['product']
                media = (p.get('featuredMedia') or {}).get('preview', {}).get('image', {})
                if media.get('url'):
                    comps.append((p['title'], media['url']))
        if not comps:
            print(f'{d["title"]:28} no component images'); continue

        images = []
        for title, url in comps[:4]:
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
        for n, (title, url) in enumerate(comps[:4], 2):
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
