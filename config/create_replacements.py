#!/usr/bin/env python3
"""
Create the two replacements for the archived mat and bed.

Cooling Comfort Pad - ice silk, 4 colours x 4 dog-appropriate sizes (XS/S are
cat-sized and deliberately excluded). Priced per size off measured CJ freight.

Waterproof Furniture Cover - US warehouse, 5-7 day delivery, single 31.5" x 70.9"
size. Priced with the freight buffer because CJ quotes $0.00 for US-stocked items
and that has not been confirmed against a real order.

Shopify variant SKUs are set to the CJ variant SKUs so CJ's automatic matching can
pair them, instead of hand-pairing every variant in that modal.
"""
import base64, json, os, sys, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
from pricing import margin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'config', 'branding', 'cj-raw', 'newskus')
ONLINE_STORE_PUB = 'gid://shopify/Publication/306551619873'

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


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def publish(pid):
    return gql('''mutation($id:ID!,$in:[PublicationInput!]!){
        publishablePublish(id:$id,input:$in){userErrors{field message}}}''',
        {'id': f'gid://shopify/Product/{pid}', 'in': [{'publicationId': ONLINE_STORE_PUB}]})


def add_images(pid, files, alt):
    for n, f in enumerate(files, 1):
        p = os.path.join(RAW, f)
        if not os.path.exists(p):
            print(f'    MISSING {f}')
            continue
        with open(p, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode()
        img = api('POST', f'products/{pid}/images.json', {'image': {
            'attachment': b64, 'filename': f.replace('.img', '.jpg'),
            'alt': alt if n == 1 else f'{alt} - detail', 'position': n}})['image']
        print(f'    {f:12} -> {img["width"]}x{img["height"]}')


# ---------------------------------------------------------------- cooling pad
SIZE_PLAN = [
    ('M 60x50cm',     'Medium 24" x 20"',    3.37, 145, 34.00, 6.11),
    ('L 70x55cm',     'Large 28" x 22"',     3.65, 190, 36.00, 6.73),
    ('XL100x70cm',    'X-Large 39" x 28"',   5.00, 345, 42.00, 8.20),
    ('XXL 150x100cm', 'XX-Large 59" x 39"',  7.69, 650, 56.00, 12.16),
]
COLOUR_PLAN = [('Light gray', 'Light Grey'), ('Coffee color', 'Coffee'),
               ('Dark blue', 'Dark Blue'), ('Pink', 'Pink')]

PAD_BODY = (
    "<p><strong>Cools the moment they lie down.</strong></p>"
    "<p>Ice-silk fabric moves body heat away by conduction rather than trapping it, so the "
    "surface stays cool without gels, water or power. No leaking, nothing to freeze, and "
    "nothing that stops working after twenty minutes. Roll it out on the floor, a sofa, "
    "a crate base or the back seat.</p><ul>"
    "<li>Contact cooling &mdash; works as soon as your dog settles on it</li>"
    "<li>No gel, no chemicals, no charging</li>"
    "<li>Breathable and anti-slip on the underside</li>"
    "<li>Folds flat and weighs almost nothing &mdash; easy to take along</li>"
    "<li>Machine washable at 30&ndash;40&deg;C</li>"
    "<li>Four sizes from 24&Prime; up to 59&Prime; for giant breeds</li></ul>"
    "<p>Sized for dogs, not scaled down for cats &mdash; the smallest option here fits a "
    "spaniel comfortably.</p>")

COVER_BODY = (
    "<p><strong>Let them on the sofa without losing the sofa.</strong></p>"
    "<p>A waterproof barrier stops muddy paws, wet fur and accidents reaching the cushions, "
    "while the quilted side gives your dog somewhere soft that smells like home. Reversible, "
    "so flip it when one side needs a wash.</p><ul>"
    "<li>Waterproof layer blocks moisture and liquids</li>"
    "<li>Reversible &mdash; two usable sides in one cover</li>"
    "<li>31.5&Prime; &times; 70.9&Prime;, sized for a standard sofa or loveseat</li>"
    "<li>Quilted and breathable, not crinkly or plastic-feeling</li>"
    "<li>Machine washable, holds its colour</li>"
    "<li>Also works on a bed, a crate floor or a car seat</li></ul>"
    "<p><strong>Ships from our US warehouse in 5&ndash;7 days.</strong></p>")


def build_pad():
    res = cj_api.call('/product/query', {'productSku': 'CJPM2920000'})
    cjv = {(v.get('variantKey') or '').strip(): v for v in res['data']['variants']}

    variants = []
    for cj_colour, nice_colour in COLOUR_PLAN:
        for cj_size, nice_size, cost, weight, price, freight in SIZE_PLAN:
            key = f'{cj_colour}-{cj_size}'
            v = cjv.get(key)
            if not v:
                print(f'  !! CJ variant not found: {key}')
                continue
            variants.append({
                'option1': nice_colour, 'option2': nice_size,
                'price': f'{price:.2f}', 'sku': v.get('variantSku'),
                'weight': weight, 'weight_unit': 'g',
                'inventory_management': 'shopify', 'inventory_policy': 'deny',
                'requires_shipping': True,
            })

    payload = {'product': {
        'title': 'Wagvive Cooling Comfort Pad',
        'handle': 'wagvive-cooling-comfort-pad',
        'body_html': PAD_BODY,
        'vendor': 'Wagvive', 'product_type': 'Comfort & Health',
        'tags': 'comfort, cooling, summer, dog, heat relief, senior pet',
        'status': 'active',
        'options': [
            {'name': 'Colour', 'values': [c[1] for c in COLOUR_PLAN]},
            {'name': 'Size', 'values': [s[1] for s in SIZE_PLAN]},
        ],
        'variants': variants,
    }}
    p = api('POST', 'products.json', payload)['product']
    print(f'  created {p["id"]}  {p["title"]}  variants={len(p["variants"])}')
    add_images(p['id'], ['pad04.img', 'pad05.img', 'pad11.img', 'pad08.img', 'pad12.img'],
               'Wagvive Cooling Comfort Pad')
    publish(p['id'])
    for s in SIZE_PLAN:
        print(f'    {s[1]:22} ${s[4]:.2f} -> {margin(s[4], s[2], s[5]) * 100:.1f}% margin')
    return p['id']


def build_cover():
    res = cj_api.call('/product/query', {'productSku': 'CJBQ3005963'})
    v = res['data']['variants'][0]
    payload = {'product': {
        'title': 'Wagvive Waterproof Furniture Cover',
        'handle': 'wagvive-waterproof-furniture-cover',
        'body_html': COVER_BODY,
        'vendor': 'Wagvive', 'product_type': 'Comfort & Health',
        'tags': 'comfort, waterproof, sofa, furniture, dog, us warehouse',
        'status': 'active',
        'variants': [{
            'price': '64.00', 'sku': v.get('variantSku'),
            'weight': 450, 'weight_unit': 'g',
            'inventory_management': 'shopify', 'inventory_policy': 'deny',
            'requires_shipping': True,
        }],
    }}
    p = api('POST', 'products.json', payload)['product']
    print(f'  created {p["id"]}  {p["title"]}')
    add_images(p['id'], ['cov02.img', 'cov03.img'], 'Wagvive Waterproof Furniture Cover')
    publish(p['id'])
    print(f'    $64.00 -> {margin(64.0, 22.99, 0.0) * 100:.1f}% margin '
          f'(51.3% if freight turns out to be $6)')
    return p['id']


if __name__ == '__main__':
    try:
        print('Cooling Comfort Pad:')
        build_pad()
        print('\nWaterproof Furniture Cover:')
        build_cover()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
