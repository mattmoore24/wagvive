#!/usr/bin/env python3
"""Create the four round-2 products: travel bottle, lick bowl, talk button,
latex egg.

Selection data (2026-08-02, all eyeball-verified against CJ imagery):
  CJDT2874873  bottle    listed 325   need $29.88 -> $30.00   plain variants only
  CJFT2860158  lick bowl listed 46    need $31.32 -> $32.00   4 colours
  CJYD2325616  button    listed 135   need $16.33 -> $16.99   4 recording macarons
  CJMY1416710  egg       listed 55    need $16.66 -> $16.99   4 colours

Toy tags: button + egg join the "any 3 toys, 15% off" pool; both are under
100 g so consolidated parcels keep the post-discount margin above the floor
(same maths as the original toy set). The lick bowl is enrichment, not a toy.

Variant SKUs are the CJ SKUs so CJ automatic matching can pair them. Stock
starts at Shop location (Shopify default); connect to the CJ location after
pairing, per config/fix_locations.py.
"""
import json, os, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = 'gid://shopify/Publication/306551619873'
COLL_COMFORT = 516731371809

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


PRODUCTS = [
    {
        'title': 'Wagvive Travel Water Bottle & Bowl',
        'handle_hint': 'travel-water-bottle',
        'type': 'Comfort & Health',
        'tags': 'dog, travel, hydration, outdoor',
        'collection': COLL_COMFORT,
        'option': 'Color',
        'price': '30.00',
        'body': """<p><strong>Water for the walk, without carrying two things.</strong></p>
<p>A 10oz stainless bottle where the silicone lid flips open into a drinking
bowl. Tip to fill the bowl, and whatever they leave flows back into the bottle
instead of onto the pavement.</p>
<ul>
<li><strong>Bottle and bowl in one</strong>: the lid is the bowl, so there is
nothing extra to pack</li>
<li><strong>Stainless steel keeps water cool</strong> on warm walks</li>
<li><strong>No waste</strong>: unfinished water tips straight back inside</li>
<li><strong>Clips to a leash or bag</strong> with the carry loop</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>""",
        'variants': [
            ('CJDT287487301AZ', 'Blue', 165),
            ('CJDT287487302BY', 'Pink', 165),
        ],
    },
    {
        'title': 'Wagvive Lick Bowl with Ball',
        'handle_hint': 'lick-bowl',
        'type': 'Comfort & Health',
        'tags': 'dog, enrichment, calming, feeding',
        'collection': COLL_COMFORT,
        'option': 'Color',
        'price': '32.00',
        'body': """<p><strong>Licking is how dogs calm themselves down. Give it a job.</strong></p>
<p>Spread something tasty on the textured bowl, and the weighted ball in the
middle makes getting at it a slow, absorbing project. Ten minutes of quiet
concentration during storms, guests, nail trims or just a rainy afternoon.</p>
<ul>
<li><strong>Textured base</strong> holds spreads and slows fast eaters</li>
<li><strong>Rolling center ball</strong> keeps the puzzle going</li>
<li><strong>Anti-slip base</strong> stays put on hard floors</li>
<li><strong>Dishwasher safe</strong></li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>""",
        'variants': [
            ('CJFT286015801AZ', 'Blue', 328),
            ('CJFT286015802BY', 'Black', 328),
            ('CJFT286015803CX', 'Grey', 328),
            ('CJFT286015804DW', 'Yellow', 328),
        ],
    },
    {
        'title': 'Wagvive Talk Button',
        'handle_hint': 'talk-button',
        'type': 'Toys & Play',
        'tags': 'dog, toy, enrichment, training',
        'collection': None,   # toys-play is smart, tag-driven
        'option': 'Color',
        'price': '16.99',
        'body': """<p><strong>Record a word. Watch them learn to press it.</strong></p>
<p>Record any short phrase, set the button by the door or the water bowl, and
most dogs work out the cause and effect faster than you expect. Start with one
word like outside, and build from there.</p>
<ul>
<li><strong>Records your voice</strong>: any phrase, re-record any time</li>
<li><strong>Big soft-press top</strong> sized for paws</li>
<li><strong>Non-slip base</strong> stays where you put it</li>
<li><strong>Batteries included</strong></li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>""",
        'variants': [
            ('CJYD232561605EV', 'Green', 98),
            ('CJYD232561603CX', 'Pink', 98),
            ('CJYD232561606FU', 'Blue', 98),
            ('CJYD232561604DW', 'Yellow', 98),
        ],
    },
    {
        'title': 'Wagvive Bouncy Egg Squeaker',
        'handle_hint': 'bouncy-egg',
        'type': 'Toys & Play',
        'tags': 'dog, toy, fetch, squeaky',
        'collection': None,
        'option': 'Color',
        'price': '16.99',
        'body': """<p><strong>It does not bounce straight, and that is the point.</strong></p>
<p>A soft latex egg that squeaks on the bite and bounces off at angles no dog
can predict. The wobble keeps chase games going far longer than a ball that
behaves itself.</p>
<ul>
<li><strong>Soft natural latex</strong>: gentle on teeth and gums</li>
<li><strong>Unpredictable bounce</strong> for longer chases</li>
<li><strong>Built-in squeaker</strong> rewards every catch</li>
<li><strong>Light enough for indoor play</strong></li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>""",
        'variants': [
            ('CJMY141671004DW', 'Green', 50),
            ('CJMY141671005EV', 'Blue', 50),
            ('CJMY141671003CX', 'Orange', 50),
            ('CJMY141671006FU', 'Purple', 50),
        ],
    },
]


def main():
    made = {}
    for spec in PRODUCTS:
        payload = {'product': {
            'title': spec['title'],
            'body_html': spec['body'],
            'vendor': 'Wagvive',
            'product_type': spec['type'],
            'tags': spec['tags'],
            'status': 'active',
            'options': [{'name': spec['option']}],
            'variants': [{
                'option1': colour, 'sku': sku, 'price': spec['price'],
                'weight': grams, 'weight_unit': 'g',
                'inventory_management': 'shopify',
            } for sku, colour, grams in spec['variants']],
        }}
        p = api('POST', 'products.json', payload)['product']
        pid = p['id']
        made[spec['handle_hint']] = {'id': pid, 'handle': p['handle'],
                                     'title': spec['title']}
        print(f"created {spec['title']}  id={pid}  /{p['handle']}")
        if spec['collection']:
            api('POST', 'collects.json', {'collect': {
                'product_id': pid, 'collection_id': spec['collection']}})
        gql('''mutation($id:ID!,$in:[PublicationInput!]!){
              publishablePublish(id:$id,input:$in){userErrors{message}}}''',
            {'id': f'gid://shopify/Product/{pid}', 'in': [{'publicationId': PUB}]})
        time.sleep(0.5)

    with open(os.path.join(ROOT, 'config', 'round2_product_ids.json'), 'w',
              encoding='utf-8') as fh:
        json.dump(made, fh, indent=1)
    print('\nids -> config/round2_product_ids.json')
    print('NOTE: run fix_locations-style connect for CJ location after CJ pairing.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
