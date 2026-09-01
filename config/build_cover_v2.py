#!/usr/bin/env python3
"""Create the replacement furniture cover and retire the old one.

The incumbent (CJBQ3005963) had to go for reasons that were about data, not the
product: CJ quotes $0.00 freight on it from every carrier, and it carries a
placeholder 50 units. Both defects turned out to be systemic to CJ's US-warehouse
listings in this category, so the replacement is China-origin, where freight is
actually quoted.

Replacement: CJYD2251860, "Pet Sofa Cushion Dog Bed Short Plush Waterproof".
Chosen over the quilted CJYD2628447 - which is arguably the better product -
because every one of that listing's photos has a cat composited onto it, and the
quilt's perspective defeats any attempt to patch it out cleanly. This one is
photographed with a Labrador and no cats at all, which matters for a dog-only
brand.

Curated to 3 colours x 3 sizes. The larger sizes are all over 1kg, where China
freight stops being viable per the sourcing rule.
"""
# DELIVERY PROMISE LITERAL. The canonical text lives in
# config/delivery_promise.py; the literal below is a copy because it sits
# inside plain triple-quoted HTML. If they diverge, config/audit_claims.py
# fails against the LIVE store and config/apply_delivery_promise.py repairs
# every product body in one pass.
import base64, json, os, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'config', 'branding', 'cj-raw', 'cover5')
OLD_PRODUCT = 10464690143521
COLLECTION_COMFORT = 516731371809
PUBLICATION = 'gid://shopify/Publication/306551619873'

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

# colour -> (sku_xs, sku_s, sku_m)
SKUS = {
    'Black': ('CJYD225186001AZ', 'CJYD225186002BY', 'CJYD225186003CX'),
    'Brown': ('CJYD225186007GT', 'CJYD225186008HS', 'CJYD225186009IR'),
    'Grey':  ('CJYD225186013MN', 'CJYD225186014NM', 'CJYD225186015OL'),
}
# size label -> (price, weight g)
SIZES = [
    ('Small 20" x 28"',  28.00, 250),
    ('Medium 28" x 39"', 40.00, 450),
    ('Large 39" x 57"',  58.00, 820),
]
# colour -> source image file for the variant thumbnail
COLOUR_IMG = {'Black': 'p00.jpg', 'Brown': 'p01.jpg', 'Grey': 'p02.jpg'}

BODY = """<p><strong>Let them on the sofa without losing the sofa.</strong></p>
<p>A waterproof layer stops muddy paws, wet fur and accidents reaching the
cushions. The top is short plush, the border is sherpa, so it reads as something
you chose for the room rather than a mat you tolerate.</p>
<ul>
<li>Waterproof backing blocks moisture before it reaches upholstery</li>
<li>Short plush face with a sherpa border - soft on both sides</li>
<li>Three sizes, from an armchair seat to a full three-seater</li>
<li>Machine washable, holds its color</li>
<li>Also works on a bed, a crate floor or the back seat of a car</li>
</ul>
<p><strong>Arrives in 10 to 16 business days.</strong></p>"""


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


def b64(name):
    with open(os.path.join(IMG, name), 'rb') as fh:
        return base64.b64encode(fh.read()).decode()


def main():
    variants = []
    for colour, skus in SKUS.items():
        for (label, price, weight), sku in zip(SIZES, skus):
            variants.append({
                'option1': colour, 'option2': label, 'sku': sku,
                'price': f'{price:.2f}', 'weight': weight, 'weight_unit': 'g',
                'inventory_management': 'shopify', 'inventory_policy': 'deny',
                'requires_shipping': True, 'taxable': True,
            })

    payload = {'product': {
        'title': 'Wagvive Waterproof Sofa & Furniture Cover',
        'body_html': BODY,
        'vendor': 'Wagvive',
        'product_type': 'Comfort & Health',
        'tags': 'comfort, dog, furniture, sofa, waterproof, washable',
        'status': 'active',
        'options': [{'name': 'Color'}, {'name': 'Size'}],
        'variants': variants,
    }}
    p = api('POST', 'products.json', payload)['product']
    pid = p['id']
    print(f'created {pid}  {p["handle"]}  ({len(p["variants"])} variants)')

    # Gallery: hero brown, the Labrador lifestyle shot, the other colourways,
    # then the folded product shot.
    gallery = [('p01.jpg', 'Wagvive Waterproof Sofa & Furniture Cover in brown'),
               ('p03_dog.jpg', 'Labrador resting on the Wagvive waterproof sofa cover'),
               ('p00.jpg', 'Wagvive Waterproof Sofa & Furniture Cover in black'),
               ('p02.jpg', 'Wagvive Waterproof Sofa & Furniture Cover in grey'),
               ('p03_fold.jpg', 'Folded Wagvive waterproof sofa cover showing sherpa border')]
    uploaded = {}
    for n, (fname, alt) in enumerate(gallery, 1):
        path = os.path.join(IMG, fname)
        if not os.path.exists(path):
            print(f'   MISSING {fname}'); continue
        img = api('POST', f'products/{pid}/images.json', {'image': {
            'attachment': b64(fname), 'filename': fname, 'alt': alt, 'position': n}})['image']
        uploaded[fname] = img['id']
        print(f'   image {fname:14} -> {img["width"]}x{img["height"]}')

    # Point each colour's variants at its own swatch.
    fresh = api('GET', f'products/{pid}.json')['product']
    for v in fresh['variants']:
        src = COLOUR_IMG.get(v['option1'])
        if src and src in uploaded:
            api('PUT', f'variants/{v["id"]}.json',
                {'variant': {'id': v['id'], 'image_id': uploaded[src]}})
    print('   variant images assigned')

    api('POST', 'collects.json',
        {'collect': {'product_id': pid, 'collection_id': COLLECTION_COMFORT}})
    print(f'   added to Comfort & Health')

    res = gql("""
    mutation($id: ID!, $input: [PublicationInput!]!) {
      publishablePublish(id: $id, input: $input) {
        userErrors { field message }
      }
    }""", {'id': f'gid://shopify/Product/{pid}',
           'input': [{'publicationId': PUBLICATION}]})
    errs = (res.get('data', {}).get('publishablePublish') or {}).get('userErrors')
    print(f'   published{"" if not errs else "  errors: " + json.dumps(errs)[:200]}')

    print(f'\nnew product id: {pid}')
    with open(os.path.join(ROOT, 'config', 'new_cover_id.txt'), 'w') as fh:
        fh.write(str(pid))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
