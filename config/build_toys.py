#!/usr/bin/env python3
"""Create the toy range plus two low-cost accessories.

Selection was ranked on CJ's `listedNum` (merchant adoption) then filtered on the
rules this catalogue already runs on: real freight quote, sub-1kg China origin,
deep stock, dog-only imagery free of competitor branding, and the 50% floor.
Everything rejected and why is in the session notes; the short version is that
disposable training pads are not viable from CJ at all (1.3-2.5kg, $0.00 freight
quotes, and stock in the low hundreds).

Prices form a deliberate ladder from $12 to $30. The point is the free-shipping
threshold: at $60, a shopper holding a single $39 item needs one more thing, and
a $12-$30 toy is an easy yes. Every price still clears the 50% floor on its own.

Variants are curated, not imported wholesale - the finger toothbrush has 12 CJ
variants including unboxed singles, and the dispenser has 10 including versions
with no bags in them. Neither belongs on a storefront.
"""
import base64, json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, 'config', 'branding', 'cj-raw', 'newprod')
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

# spu, title, price, option name, {option value: cj variant key}, tags, body
SPEC = [
    ('CJYD2422878', 'Wagvive Barnyard Squeaker', 18.00, 'Character',
     {'Green Dog': 'Green Dog', 'Brown Dog': 'Brown Dog', 'Giraffe': 'Giraffe',
      'Grey Donkey': 'Gray Donkey', 'White Goat': 'White Goat', 'Puppy': 'Puppy',
      'Blue Donkey': 'Blue donkey'},
     'toy, squeaky, plush',
     '<p><strong>The one they carry everywhere.</strong></p><p>A soft plush '
     'squeaker sized for carrying, shaking and the occasional act of violence. '
     'Seven characters, so you can find the one they bond with.</p><ul>'
     '<li>Internal squeaker holds up to enthusiastic chewing</li>'
     '<li>Soft enough for indoor play and gentle mouths</li>'
     '<li>Light to carry, easy to toss</li></ul>'),

    ('CJST2178441', 'Wagvive Dental Duck Chew Toy', 20.00, None, None,
     'toy, dental, chew',
     '<p><strong>A chew toy that earns its keep.</strong></p><p>Textured latex '
     'with raised ridges that work against teeth while they chew, so the time '
     'they spend gnawing does something useful.</p><ul>'
     '<li>Ridged surface helps scrub as they chew</li>'
     '<li>Squeaks, which is the entire point as far as they are concerned</li>'
     '<li>Soft latex, kinder on teeth than hard plastic</li></ul>'),

    ('CJST2178342', 'Wagvive Crinkle Plush Buddy', 22.00, 'Color',
     {'Blue': 'Blue', 'Green': 'Green', 'Orange': 'Orange'},
     'toy, plush, squeaky',
     '<p><strong>Squeak on one end, crinkle on the other.</strong></p><p>Two '
     'noises in one toy, which is two reasons to keep picking it up. Flat-bodied '
     'and floppy, so it is easy to shake and easy to carry.</p><ul>'
     '<li>Squeaker and crinkle panel</li>'
     '<li>Flat, floppy shape for shaking and carrying</li>'
     '<li>Three colours</li></ul>'),

    ('CJST2583646', 'Wagvive Woodland Rope-Limb Plush', 24.00, 'Animal',
     {'Fox': 'Fox', 'Rabbit': 'Rabbit', 'Tiger': 'Tiger', 'Monkey': 'Monkey',
      'Koala': 'Koala', 'Squirrel': 'Squirrel'},
     'toy, plush, rope, squeaky',
     '<p><strong>Plush body, rope limbs.</strong></p><p>The rope arms and legs '
     'give them something to actually work at once the squeaking novelty wears '
     'off - and they are the part that usually survives longest.</p><ul>'
     '<li>Knotted rope limbs for tugging and chewing</li>'
     '<li>Squeaker in the body</li>'
     '<li>Six animals to choose from</li></ul>'),

    ('CJST2190132', 'Wagvive Big Squeak Plush', 26.00, 'Color',
     {'Blue': 'Blue', 'Orange': 'Orange'},
     'toy, plush, squeaky, rope',
     '<p><strong>Long-limbed and built for shaking.</strong></p><p>The dangling '
     'legs and knotted rope make this one a shaker rather than a chewer, which is '
     'the game most dogs want to play with a person holding the other end.</p><ul>'
     '<li>Long limbs for shaking and tug</li>'
     '<li>Knotted rope section</li>'
     '<li>Squeaker inside</li></ul>'),

    ('CJST2175587', 'Wagvive Rope-Limb Puppy Plush', 28.00, None, None,
     'toy, plush, rope, squeaky',
     '<p><strong>A dog, for your dog.</strong></p><p>Plush body with rope arms '
     'and legs and a crinkle-paper sound panel inside. Around 22cm across, so it '
     'suits small and medium dogs rather than heavy chewers.</p><ul>'
     '<li>Rope limbs and a crinkle sound panel</li>'
     '<li>Roughly 22 x 15cm</li>'
     '<li>Best for small to medium dogs</li></ul>'),

    ('CJST2221397', 'Wagvive Squirrel Squeaky Plush', 30.00, None, None,
     'toy, plush, squeaky',
     '<p><strong>The classic.</strong></p><p>A realistic plush squirrel with a '
     'squeaker in the body and a tail built for carrying. If your dog has a '
     'thing about squirrels, this is the one.</p><ul>'
     '<li>Squeaker in the body</li>'
     '<li>Long tail, easy to pick up and carry</li>'
     '<li>Soft plush, for play rather than heavy chewing</li></ul>'),

    ('CJYD2626864', 'Wagvive Finger Toothbrush', 12.00, 'Color',
     {'Blue': 'Blue-Boxed', 'Dark Blue': 'Dark Blue-Boxed',
      'Orange': 'Orange-Boxed', 'White': 'White-Boxed'},
     'dental, grooming, teeth',
     '<p><strong>Brushing, without the fight.</strong></p><p>A soft silicone '
     'sleeve that fits over your finger, so you have far more control than you '
     'get with a brush handle - and most dogs tolerate a finger better.</p><ul>'
     '<li>360-degree bristles reach the gum line</li>'
     '<li>Soft silicone, gentle on gums</li>'
     '<li>Rinses clean, use it daily</li>'
     '<li>Boxed, so it stays clean between uses</li></ul>'),

    ('CJYD2222742', 'Wagvive LED Waste Bag Dispenser', 14.00, 'Color',
     {'Pink': 'Pink Gray-Including Garbage Bag',
      'Blue': 'Blue Gray-Including Garbage Bag',
      'Grey': 'Gray Gray-Including Garbage Bag',
      'Green': 'Green Gray-Including Garbage Bag',
      'Black': 'Gray Black-Including Garbage Bag'},
     'accessory, walks, waste bags',
     '<p><strong>For the walk you do in the dark.</strong></p><p>A clip-on '
     'dispenser with a built-in LED, so you can actually see what you are doing '
     'on a winter evening. Comes with a roll of bags.</p><ul>'
     '<li>Built-in LED light</li>'
     '<li>Clips to a lead or a belt loop</li>'
     '<li>Includes a roll of bags, refills with any standard roll</li></ul>'),
]


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


def fetch(url, path):
    if os.path.exists(path):
        return path
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        with open(path, 'wb') as fh:
            fh.write(r.read())
    return path


def main():
    os.makedirs(IMGDIR, exist_ok=True)
    cj = json.load(open(os.path.join(ROOT, 'config', 'cj_new_products.json'),
                        encoding='utf-8'))
    existing = {p['handle']: p for p in
                api('GET', 'products.json?limit=250')['products']}
    created = {}

    for spu, title, price, opt_name, opt_map, tags, body in SPEC:
        d = cj.get(spu) or (cj_api.call('/product/query',
                                        {'productSku': spu}).get('data') or {})
        by_key = {str(v.get('variantKey')): v for v in (d.get('variants') or [])}

        variants = []
        if opt_map:
            for label, key in opt_map.items():
                v = by_key.get(key)
                if not v:
                    print(f'   !! {spu}: no variant {key!r}'); continue
                variants.append({
                    'option1': label, 'sku': v.get('variantSku'),
                    'price': f'{price:.2f}',
                    'weight': float(v.get('variantWeight') or 0), 'weight_unit': 'g',
                    'inventory_management': 'shopify', 'inventory_policy': 'deny',
                    'requires_shipping': True, 'taxable': True})
        else:
            v = (d.get('variants') or [])[0]
            variants.append({
                'option1': 'Default Title', 'sku': v.get('variantSku'),
                'price': f'{price:.2f}',
                'weight': float(v.get('variantWeight') or 0), 'weight_unit': 'g',
                'inventory_management': 'shopify', 'inventory_policy': 'deny',
                'requires_shipping': True, 'taxable': True})

        payload = {'product': {
            'title': title, 'body_html': body, 'vendor': 'Wagvive',
            'product_type': 'Toys & Play' if 'toy' in tags else 'Comfort & Health',
            'tags': f'dog, {tags}', 'status': 'active',
            'options': [{'name': opt_name or 'Title'}],
            'variants': variants}}

        handle_guess = title.lower().replace('&', '').replace('  ', ' ').replace(' ', '-')
        if handle_guess in existing:
            print(f'{title:42} already exists, skipped'); continue

        p = api('POST', 'products.json', payload)['product']
        created[spu] = p['id']
        print(f'{title:42} id {p["id"]}  {len(p["variants"])} variant(s)')

        for n, url in enumerate((d.get('productImageSet') or [])[:5], 1):
            fp = os.path.join(IMGDIR, f'{spu}_{n}.jpg')
            try:
                fetch(url, fp)
                with open(fp, 'rb') as fh:
                    b64 = base64.b64encode(fh.read()).decode()
                api('POST', f'products/{p["id"]}/images.json',
                    {'image': {'attachment': b64, 'filename': f'{spu}_{n}.jpg',
                               'alt': title, 'position': n}})
            except Exception as exc:
                print(f'      image {n} failed: {str(exc)[:60]}')

        gql("""mutation($id: ID!, $input: [PublicationInput!]!) {
                 publishablePublish(id: $id, input: $input) {
                   userErrors { message } } }""",
            {'id': f'gid://shopify/Product/{p["id"]}',
             'input': [{'publicationId': PUBLICATION}]})

    with open(os.path.join(ROOT, 'config', 'new_toy_ids.json'), 'w', encoding='utf-8') as fh:
        json.dump(created, fh, indent=1)
    print(f'\n{len(created)} product(s) created')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
