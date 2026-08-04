#!/usr/bin/env python3
"""Re-order product galleries so each leads with its best selling image.

Products were built by taking CJ's first N images in order, which is fine until
the supplier's first image is a dimensions diagram or a marketing panel. The
audit sheet (config/branding/audit/_covers.png) surfaced five that were leading
with the wrong thing, plus a sixth problem: the slicker brush and its glove
sibling are photographed almost entirely on CATS, which is no good for a dog-only
brand.

Indices below are the CJ productImageSet positions, hand-picked from the contact
sheets in config/branding/audit/_fix_*.png. Rules applied:
  - never lead with a dimensions diagram or a text/marketing panel
  - never show a cat
  - prefer a clean product shot or a dog actually using the thing
"""
import base64, json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'config', 'branding', 'audit')

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

# product id -> (spu, [CJ image indices in the order we want them])
FIXES = {
    # was: "More than just a storage capsule" marketing panel
    10469666128161: ('CJYD2222742', [7, 2, 1, 3, 8]),
    # was: a text-heavy branded can reading "Pet Ear Cleaner ... 50 pcs/can"
    10456337154337: ('CJYD2169796', [5, 9, 0, 4]),
    # was: a row of three different brushes; cats in most of the rest
    10456336990497: ('CJMY1952185', [8, 0, 2, 3]),
    # was: a dull glove-on-hand; everything else is dimensions or "2pcs" panels
    10456337056033: ('CJYD2332008', [9, 2, 7, 4]),
    # was: a 120mm/150mm/220mm dimensions diagram
    10469665964321: ('CJST2175587', [4, 2, 1, 3]),
}


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def main():
    for pid, (spu, order) in FIXES.items():
        p = api('GET', f'products/{pid}.json')['product']
        title = p['title']
        d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
        imgs = d.get('productImageSet') or []
        if not imgs:
            print(f'{title:34} no CJ images'); continue

        for img in p.get('images', []):
            api('DELETE', f'products/{pid}/images/{img["id"]}.json')

        added = 0
        for pos, idx in enumerate(order, 1):
            if idx >= len(imgs):
                continue
            cached = os.path.join(CACHE, f'{spu}_{idx}.jpg')
            try:
                if os.path.exists(cached):
                    with open(cached, 'rb') as fh:
                        b64 = base64.b64encode(fh.read()).decode()
                    api('POST', f'products/{pid}/images.json', {'image': {
                        'attachment': b64, 'filename': f'{spu}_{idx}.jpg',
                        'alt': title, 'position': pos}})
                else:
                    api('POST', f'products/{pid}/images.json', {'image': {
                        'src': imgs[idx], 'alt': title, 'position': pos}})
                added += 1
            except Exception as exc:
                print(f'   {title[:28]} image {idx} failed: {str(exc)[:60]}')

        print(f'{title:34} cover -> CJ image #{order[0]}, {added} image(s)')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
