#!/usr/bin/env python3
"""Create the six-product fall lineup: five seasonal, one viral grooming device.

Sourced and costed in docs/fall-lineup-research-2026-08.md from a 5,535 product
sweep. Every SKU here cleared the same gate: no duplicate SPU, live CJ freight
inside the 12 business day promise, deep stock, and every CJ reference image
opened at full size. That last check is not ceremony. It is what caught
CJYD1861730, listed as "Halloween Pumpkin Vest For Dogs", which is actually a
CAT head hood.

TIMING IS THE POINT. Halloween is 31 October and the promise is 5 to 12 business
days, so orders must land by about 10 October. This lineup is worth shipping
early rather than perfect and late.

MARGINS are quoted on the WORST variant, never the cheapest, because the cheapest
variant is how the multipack trap gets in: CJGY2140137 pairs a $1.04 accessory
with the real $44.44 device. Each floor_margin_pct below is the achieved
worst-case margin less the 8pt drift buffer the rest of the price book uses.

Created as DRAFT with CJ's own verified photography, so nothing is briefly live
without imagery. House-style cream art is shot afterwards and swapped in, then
--finish activates and publishes to every sales channel.

    python config/add_fall_lineup.py            # report
    python config/add_fall_lineup.py --apply    # create drafts
    python config/add_fall_lineup.py --finish --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                              # noqa: E402
import sync_inventory                                      # noqa: E402

SHOP_LOCATION = 113363058977
GROOMING_ID = 516731339041
SEASONAL_HANDLE = 'fall-halloween'
SEASONAL_TITLE = 'Fall and Halloween'

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


def sizes(design, rows):
    return [((design, s), k, w) for (s, k, w) in rows]


SPECS = [
 {'handle': 'wagvive-glow-skeleton-suit',
  'title': 'Wagvive Glow in the Dark Skeleton Suit',
  'spu': 'CJGD2143164', 'price': '24.99', 'floor': 46.4, 'type': 'Apparel',
  'tags': 'apparel, costume, dog, fall, halloween, seasonal',
  'options': ['Size'],
  'variants': [(('S',), 'CJGD214316401AZ', 60), (('M',), 'CJGD214316402BY', 66),
               (('L',), 'CJGD214316403CX', 75), (('XL',), 'CJGD214316404DW', 86)],
  'seo_title': 'Glow in the Dark Dog Skeleton Costume, 4 Sizes',
  'seo_desc': 'A black four leg suit with a skeleton that glows after dark. '
              'Soft brushed knit, four sizes from small to extra large.',
  'body': """<p><strong>It glows once the sun goes down.</strong></p>
<p>A black four leg suit with a bone print that charges in daylight and glows on
the evening walk, which is exactly when everyone is out looking at dogs.</p>
<ul>
<li>Soft brushed knit, pulls on over the head</li>
<li>Ribbed neck and cuffs so it stays put</li>
<li>Four sizes, small through extra large</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-halloween-snuffle-mat',
  'title': 'Wagvive Halloween Snuffle Mat',
  'spu': 'CJYD2183039', 'price': '32.99', 'floor': 44.9, 'type': 'Toys',
  'tags': 'dog, enrichment, fall, halloween, puzzle, seasonal, toy',
  'options': ['Size'],
  'variants': [(('50 x 60 cm',), 'CJYD218303901AZ', 270)],
  'seo_title': 'Halloween Dog Snuffle Mat, Hides Treats in Fleece',
  'seo_desc': 'Hide treats in the ghosts, bats and pumpkins and let dinner take '
              'ten minutes instead of thirty seconds. 50 by 60 cm fleece mat.',
  'body': """<p><strong>Hide the treats. Let them work for it.</strong></p>
<p>Fleece ghosts, bats, pumpkins and a haunted house, with a drawstring pumpkin
pouch in the corner. Tuck food into the folds and a thirty second inhale becomes
ten minutes of sniffing, which is what actually tires a dog out.</p>
<ul>
<li>Ghosts, bats and pumpkins to hide food under</li>
<li>Drawstring pumpkin pouch for the harder finds</li>
<li>50 by 60 cm, machine washable</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-jack-o-lantern-sweater',
  'title': 'Wagvive Jack-o-Lantern Sweater',
  'spu': 'CJGD1809813', 'price': '17.99', 'floor': 37.5, 'type': 'Apparel',
  'tags': 'apparel, dog, fall, halloween, seasonal, sweater',
  'options': ['Color', 'Size'],
  'variants': (
    sizes('Orange Stripe', [('XS', 'CJGD180981301AZ', 85),
                            ('S', 'CJGD180981302BY', 95),
                            ('M', 'CJGD180981303CX', 105),
                            ('L', 'CJGD180981304DW', 115),
                            ('XL', 'CJGD180981305EV', 125)]) +
    sizes('Black Embroidered', [('XS', 'CJGD180981306FU', 85),
                                ('S', 'CJGD180981307GT', 95),
                                ('M', 'CJGD180981308HS', 105),
                                ('L', 'CJGD180981309IR', 115),
                                ('XL', 'CJGD180981310JQ', 125)]) +
    sizes('Black Jacquard', [('XS', 'CJGD180981311KP', 85),
                             ('S', 'CJGD180981312LO', 95),
                             ('M', 'CJGD180981313MN', 105),
                             ('L', 'CJGD180981314NM', 115),
                             ('XL', 'CJGD180981315OL', 125)]) +
    sizes('Orange Pumpkin', [('XS', 'CJGD180981316PK', 85),
                             ('S', 'CJGD180981317QJ', 95),
                             ('M', 'CJGD180981318RI', 105),
                             ('L', 'CJGD180981319SH', 115),
                             ('XL', 'CJGD180981320TG', 125)])),
  'seo_title': 'Jack-o-Lantern Dog Sweater, 4 Colours and 5 Sizes',
  'seo_desc': 'Chunky orange and black knit with a glitter pumpkin on the chest. '
              'Four colourways, five sizes from extra small to extra large.',
  'body': """<p><strong>Warm enough for October, silly enough for Halloween.</strong></p>
<p>A chunky knit with a glitter jack-o-lantern on the chest. Thick enough to be
the actual coat on a cold walk, not just a costume that comes off after the
photos.</p>
<ul>
<li>Soft chunky knit with a ribbed neck</li>
<li>Four colourways, five sizes from XS to XL</li>
<li>Pulls on over the head, legs stay free</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-halloween-squeaky-bones',
  'title': 'Wagvive Halloween Squeaky Bones',
  'spu': 'CJYD2146653', 'price': '15.99', 'floor': 46.3, 'type': 'Toys',
  'tags': 'dog, fall, halloween, seasonal, squeaky, toy',
  'options': ['Design'],
  'variants': [(('Witch Hat Bone',), 'CJYD214665301AZ', 56),
               (('Skull Candy',), 'CJYD214665302BY', 56),
               (('Blue Witch Hat',), 'CJYD214665303CX', 56),
               (('Black Cat Bone',), 'CJYD214665304DW', 56),
               (('Skull Bone',), 'CJYD214665305EV', 56),
               (('Lollipop Bone',), 'CJYD214665306FU', 56),
               (('Long Bone',), 'CJYD214665307GT', 56),
               (('Candy Corn Bone',), 'CJYD214665308HS', 56)],
  'seo_title': 'Halloween Squeaky Dog Toy, 8 Designs',
  'seo_desc': 'A soft squeaky bone in eight Halloween designs, from witch hats '
              'to skull candy. Light enough for small dogs to carry all day.',
  'body': """<p><strong>One squeak, eight ways to look ridiculous.</strong></p>
<p>A soft bone with a squeaker inside, printed for the season. Light enough for a
small dog to carry around the house all day, which they will.</p>
<ul>
<li>Eight designs, from witch hats to skull candy</li>
<li>Soft enough for gentle chewers, squeaks the whole time</li>
<li>Light and easy to carry</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-thanksgiving-turkey-coat',
  'title': 'Wagvive Thanksgiving Turkey Coat',
  'spu': 'CJGD1841040', 'price': '19.99', 'floor': 31.7, 'type': 'Apparel',
  'tags': 'apparel, coat, dog, fall, seasonal, thanksgiving',
  'options': ['Design', 'Size'],
  'variants': (
    sizes('Turkey', [('S', 'CJGD184104005EV', 75), ('M', 'CJGD184104006FU', 90),
                     ('L', 'CJGD184104007GT', 110), ('XL', 'CJGD184104008HS', 120)]) +
    sizes('Boo', [('S', 'CJGD184104009IR', 75), ('M', 'CJGD184104010JQ', 90),
                  ('L', 'CJGD184104011KP', 110), ('XL', 'CJGD184104012LO', 120)]) +
    sizes('Plaid', [('S', 'CJGD184104001AZ', 75), ('M', 'CJGD184104002BY', 90),
                    ('L', 'CJGD184104003CX', 110), ('XL', 'CJGD184104004DW', 120)])),
  'seo_title': 'Thanksgiving Dog Coat, Turkey, Boo and Plaid',
  'seo_desc': 'A lapel coat in three fall designs: a turkey for Thanksgiving, '
              'a Boo for Halloween and a classic plaid. Four sizes.',
  'body': """<p><strong>One coat, the whole of autumn.</strong></p>
<p>A lapel coat in three designs, so it covers Halloween and Thanksgiving without
buying twice. Warm enough to be the real coat on a cold walk.</p>
<ul>
<li>Turkey for Thanksgiving, Boo for Halloween, plaid for everything else</li>
<li>Retro lapel collar with contrast trim</li>
<li>Four sizes, small through extra large</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-steam-grooming-brush',
  'title': 'Wagvive 3-in-1 Steam Grooming Brush',
  'spu': 'CJYD2256797', 'price': '26.99', 'floor': 45.5, 'type': 'Grooming',
  'tags': 'brush, dog, grooming, shedding, steam',
  'options': ['Color'],
  'variants': [(('Pink',), 'CJYD225679701AZ', 200),
               (('Red',), 'CJYD225679702BY', 200)],
  'seo_title': 'Steam Dog Grooming Brush, No Rinse, 3 in 1',
  'seo_desc': 'Fill the tank, press the button and brush. Lifts loose hair and '
              'freshens the coat between baths, with no rinsing needed.',
  'body': """<p><strong>A bath without the bath.</strong></p>
<p>Fill the little tank, press the button and brush. A fine mist goes down with
the bristles, so loose hair lifts instead of flying and the coat comes up clean
between proper washes.</p>
<ul>
<li>Water tank and a one press mist button</li>
<li>Soft silicone bristles that will not scratch</li>
<li>Lifts loose hair rather than spreading it round the room</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},
]


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
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:400]}')
    return {}


def gql(q, v=None):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    time.sleep(0.4)
    return out


def by_handle(handle):
    """Look a product up by handle, across every status.

    NOT `status=any`. That value is invalid on products.json and Shopify answers
    with an empty list rather than an error, so the lookup silently finds
    nothing. That made the duplicate guard here a no-op: a second --apply would
    have created a second copy of all six products.
    """
    ps = []
    for st in ('active', 'draft', 'archived'):
        ps = api('GET', f'products.json?handle={handle}&limit=1&status={st}'
                 ).get('products') or []
        if ps:
            return ps[0]
    return None


def seasonal_collection(create=False):
    for c in api('GET', 'custom_collections.json?limit=250')['custom_collections']:
        if c['handle'] == SEASONAL_HANDLE:
            return c['id']
    if not create:
        return None
    c = api('POST', 'custom_collections.json', {'custom_collection': {
        'title': SEASONAL_TITLE, 'handle': SEASONAL_HANDLE,
        'body_html': '<p>Costumes, coats and toys for Halloween and '
                     'Thanksgiving. Order by 10 October to have it in time.</p>',
        'published': True}})['custom_collection']
    print(f'  created collection {SEASONAL_TITLE} ({c["id"]})')
    return c['id']


def cj_photos(spu, limit=6):
    d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
    return (d.get('productImageSet') or [])[:limit]


def create_one(spec, seasonal_id):
    """Draft, SEO, collections, stock. Imagery from CJ's verified originals."""
    print(f"\n=== {spec['title']} ===")
    if by_handle(spec['handle']):
        print('  already exists, skipping')
        return None

    payload = {'product': {
        'title': spec['title'], 'handle': spec['handle'],
        'body_html': spec['body'], 'vendor': 'Wagvive',
        'product_type': spec['type'], 'status': 'draft', 'tags': spec['tags'],
        'options': [{'name': n} for n in spec['options']],
        'variants': [{
            **{f'option{i+1}': v for i, v in enumerate(opts)},
            'sku': sku, 'price': spec['price'],
            'grams': w, 'weight': w, 'weight_unit': 'g',
            'inventory_management': 'shopify', 'inventory_policy': 'deny',
            'requires_shipping': True, 'taxable': True,
        } for opts, sku, w in spec['variants']]}}
    prod = api('POST', 'products.json', payload)['product']
    pid = prod['id']
    print(f"  created draft {pid} with {len(prod['variants'])} variant(s)")

    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id }
               userErrors { field message } } }''',
        {'input': {'id': f'gid://shopify/Product/{pid}', 'metafields': [
            {'namespace': 'global', 'key': 'title_tag',
             'type': 'single_line_text_field', 'value': spec['seo_title']},
            {'namespace': 'global', 'key': 'description_tag',
             'type': 'multi_line_text_field', 'value': spec['seo_desc']}]}})
    print('  SEO set')

    for cid in filter(None, [seasonal_id,
                             GROOMING_ID if spec['type'] == 'Grooming' else None]):
        api('POST', 'collects.json',
            {'collect': {'product_id': pid, 'collection_id': cid}})
    print('  collections set')

    for i, url in enumerate(cj_photos(spec['spu'])):
        try:
            api('POST', f'products/{pid}/images.json',
                {'image': {'src': url, 'position': i + 1,
                           'alt': spec['title']}})
        except SystemExit as e:
            print(f'  image {i} rejected: {str(e)[:90]}')
    print('  imagery uploaded from CJ originals')

    # Stock at the canonical location only. Anything at the legacy CJ location
    # is inert and double-counts.
    for v in prod['variants']:
        q = sync_inventory.cj_stock(v['sku']) or 0
        api('POST', 'inventory_levels/set.json',
            {'location_id': SHOP_LOCATION,
             'inventory_item_id': v['inventory_item_id'], 'available': q})
    print(f"  stock written for {len(prod['variants'])} variant(s)")
    return pid


def finish(apply):
    """Price book floors, activate, publish to every channel, verify live."""
    book_path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(book_path, encoding='utf-8'))

    live = by_handle('wagvive-sneaker-chew-buddy') or by_handle('toy-kit')
    chans = gql('''query($id: ID!) { product(id: $id) {
                     resourcePublicationsV2(first: 25) {
                       nodes { publication { id name } } } } }''',
                {'id': f'gid://shopify/Product/{live["id"]}'}
                )['data']['product']['resourcePublicationsV2']['nodes']
    pubs = [{'publicationId': n['publication']['id']} for n in chans]
    print(f'publishing to {len(pubs)} channel(s): '
          f'{[n["publication"]["name"] for n in chans]}')

    bad = []
    for spec in SPECS:
        p = by_handle(spec['handle'])
        if not p:
            print(f"  {spec['handle']}: MISSING")
            bad.append(spec['handle'])
            continue
        if not apply:
            print(f"  would activate + publish {spec['handle']}")
            continue
        api('PUT', f"products/{p['id']}.json",
            {'product': {'id': p['id'], 'status': 'active'}})
        gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
                 publishablePublish(id: $id, input: $input) {
                   userErrors { field message } } }''',
            {'id': f"gid://shopify/Product/{p['id']}", 'input': pubs})
        book.setdefault(spec['handle'], {})['floor_margin_pct'] = spec['floor']
        print(f"  {spec['handle']}: active, published, floor {spec['floor']}%")

    if apply:
        with open(book_path, 'w', encoding='utf-8') as fh:
            json.dump(book, fh, indent=1, ensure_ascii=False)
        print('price_book.json updated')

        print('\nverifying on the live storefront...')
        shop = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')
        for spec in SPECS:
            url = (f"https://{shop}/products/{spec['handle']}.js"
                   f"?nocache={int(time.time()*1000)}")
            try:
                req = urllib.request.Request(
                    url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    d = json.loads(r.read().decode())
                buy = sum(1 for v in d['variants'] if v['available'])
                print(f"  {d['title']:44} {buy}/{len(d['variants'])} buyable  "
                      f"${d['variants'][0]['price']/100:.2f}")
                if buy == 0:
                    bad.append(spec['handle'])
            except Exception as e:
                print(f"  {spec['handle']}: NOT LIVE ({e})")
                bad.append(spec['handle'])
            time.sleep(0.4)
    return 1 if bad else 0


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)

    print(f'{len(SPECS)} products, '
          f'{sum(len(s["variants"]) for s in SPECS)} variants total\n')
    for s in SPECS:
        print(f"  {s['title']:44} ${s['price']:>6}  "
              f"{len(s['variants']):>2} var  floor {s['floor']}%  {s['spu']}")
    if not apply:
        print('\nDry run. Use --apply to create drafts.')
        return 0

    seasonal_id = seasonal_collection(create=True)
    made = [create_one(s, seasonal_id) for s in SPECS]
    print(f'\n{sum(1 for m in made if m)} created as DRAFT. '
          f'Next: house-style art, then --finish --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
