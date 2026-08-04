#!/usr/bin/env python3
"""Create the 14 round-4 products from config/round4_manifest.json.

Prices are the floor-verified ones from round4_pricing.py (FAILS: none on
2026-08-02). Variant SKUs are the exact CJ SKUs so CJ auto-matching pairs
them. Weights come from round4_picks_variants.json. Tags drive the smart
collections (toy -> Toys & Play, travel/outdoor -> Travel & Outdoor,
calming/enrichment -> Calming & Enrichment); Grooming and Comfort & Health
are manual collections handled via collects here.
"""
import json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = 'gid://shopify/Publication/306551619873'
COLL_COMFORT = 516731371809
COLL_GROOMING = None  # resolved at runtime by handle

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


def api(method, path, payload=None, tries=4):
    for i in range(tries):
        try:
            url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
            data = json.dumps(payload).encode() if payload is not None else None
            req = urllib.request.Request(url, data=data, method=method, headers={
                'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 409) and i < tries - 1:
                time.sleep(2.5 * (i + 1)); continue
            raise


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


ARRIVES = '<p><strong>Arrives in 5 to 12 business days.</strong></p>'

META = {
 'sneaker': dict(handle='sneaker-chew-buddy', type='Toys & Play',
    tags='dog, toy, chew, squeaky', collection=None,
    body='<p><strong>The shoe they are finally allowed to have.</strong></p>'
    '<p>A canvas sneaker built for dogs: rope laces to tug, a rope-trimmed sole to gnaw, '
    'and a squeak hidden in the toe. Give them their own pair and keep yours by the door.</p>'
    '<ul><li><strong>Rope laces and sole</strong> stand up to serious chewing</li>'
    '<li><strong>Built-in squeaker</strong> rewards every bite</li>'
    '<li><strong>Canvas body</strong> is light enough for indoor fetch</li></ul>' + ARRIVES),
 'ringball': dict(handle='jingle-plush-ball', type='Toys & Play',
    tags='dog, toy, fetch, puppy', collection=None,
    body='<p><strong>A soft ball that answers back.</strong></p>'
    '<p>Bells inside, crinkly tags outside, and a stitched character on every panel. The jingle '
    'keeps play going, the tags give puppies something legal to mouth, and the plush body is '
    'gentle on young teeth.</p>'
    '<ul><li><strong>Jingle bell core</strong> makes every roll exciting</li>'
    '<li><strong>Sensory ribbon tags</strong> for teething puppies</li>'
    '<li><strong>Soft plush panels</strong>, easy on gums and floors</li></ul>' + ARRIVES),
 'teddy': dict(handle='cuddle-companion-teddy', type='Toys & Play',
    tags='dog, toy, plush, comfort', collection=None,
    body='<p><strong>The naptime teddy.</strong></p>'
    '<p>A 27cm knit teddy sized for carrying, wrestling and finally falling asleep on. The '
    'textured knit is tougher than it looks, and the softness is exactly what it looks like.</p>'
    '<ul><li><strong>27cm knit plush</strong>, big enough to snuggle</li>'
    '<li><strong>Durable textured fabric</strong> survives daily carrying</li>'
    '<li><strong>No hard parts</strong>, safe for the toy basket</li></ul>' + ARRIVES),
 'vocalplush': dict(handle='corduroy-squeak-pals', type='Toys & Play',
    tags='dog, toy, squeaky, plush', collection=None,
    body='<p><strong>Corduroy characters with a loud opinion.</strong></p>'
    '<p>Ribbed corduroy bodies, knotted rope limbs, and a squeaker in the middle of it all. '
    'The rope arms and legs double as tug handles, so one toy covers squeak, tug and fetch.</p>'
    '<ul><li><strong>Corduroy body</strong> with reinforced stitching</li>'
    '<li><strong>Knotted rope limbs</strong> built for tug</li>'
    '<li><strong>Loud, satisfying squeak</strong></li></ul>' + ARRIVES),
 'chicken': dict(handle='screaming-chicken', type='Toys & Play',
    tags='dog, toy, squeaky, funny', collection=None,
    body='<p><strong>The internet-famous scream, in plush form.</strong></p>'
    '<p>Squeeze it and it yells. Dogs find the sound irresistible, and so does everyone '
    'filming them. Long neck for shaking, plush body for catching, chaos for the whole '
    'household.</p>'
    '<ul><li><strong>The signature screaming squawk</strong> dogs go wild for</li>'
    '<li><strong>Long neck</strong> made for shake-it-out play</li>'
    '<li><strong>Soft plush body</strong>, safe indoors</li></ul>' + ARRIVES),
 'towel': dict(handle='quick-dry-bath-robe', type='Grooming', tags='dog, grooming, bath',
    collection='grooming',
    body='<p><strong>From soaked to snug in one wrap.</strong></p>'
    '<p>A hooded microfibre robe that drinks the bathwater off your dog before it ends up on '
    'your walls. Wrap, fasten, and let them do the post-bath zoomies already dry.</p>'
    '<ul><li><strong>Ultra-absorbent microfibre</strong> cuts drying time</li>'
    '<li><strong>Hooded wrap design</strong> stays on wiggly dogs</li>'
    '<li><strong>Machine washable</strong>, dries fast itself</li></ul>'
    '<p><strong>Sizing:</strong> XS suits small breeds, S mediums, M larger dogs. When between '
    'sizes, size up.</p>' + ARRIVES),
 'lednail': dict(handle='led-nail-clippers', type='Grooming', tags='dog, grooming, nails',
    collection='grooming',
    body='<p><strong>See the quick before you cut.</strong></p>'
    '<p>A bright LED shines through the nail so the quick shows as a shadow, taking the '
    'guesswork and the nerves out of trim day. Sharp stainless blades cut clean in one '
    'squeeze.</p>'
    '<ul><li><strong>Built-in LED</strong> reveals the quick on light nails</li>'
    '<li><strong>Stainless steel blades</strong> for a clean, fast cut</li>'
    '<li><strong>Comfortable non-slip grip</strong></li></ul>' + ARRIVES),
 'dematting': dict(handle='dematting-comb', type='Grooming', tags='dog, grooming, deshedding',
    collection='grooming',
    body='<p><strong>For the knots the brush gave up on.</strong></p>'
    '<p>Curved stainless teeth slice through mats and tangles instead of pulling them, with a '
    'smooth wooden handle that is easy on your grip through a full coat.</p>'
    '<ul><li><strong>Curved cutting teeth</strong> work through mats gently</li>'
    '<li><strong>Rounded tips</strong> protect the skin underneath</li>'
    '<li><strong>Solid wood handle</strong>, comfortable for long sessions</li></ul>' + ARRIVES),
 'pawtrimmer': dict(handle='cordless-paw-trimmer', type='Grooming', tags='dog, grooming, paws',
    collection='grooming',
    body='<p><strong>Tidy paws without the salon trip.</strong></p>'
    '<p>A slim, quiet, cordless trimmer sized for the fiddly spots: between paw pads, around '
    'the face, anywhere a full-size clipper is overkill. Waterproof head rinses clean.</p>'
    '<ul><li><strong>Low-noise motor</strong> keeps nervous dogs calm</li>'
    '<li><strong>Slim precision head</strong> for paw pads and touch-ups</li>'
    '<li><strong>USB rechargeable</strong> and fully washable head</li></ul>' + ARRIVES),
 'pawcup': dict(handle='paw-washing-cup', type='Grooming', tags='dog, grooming, paws, walks',
    collection='grooming',
    body='<p><strong>Muddy walk in, clean paws out.</strong></p>'
    '<p>Add a little water, insert one muddy paw, twist gently. Soft silicone bristles inside '
    'the cup lift off the dirt before it reaches your floors.</p>'
    '<ul><li><strong>Soft silicone bristles</strong> clean without scrubbing</li>'
    '<li><strong>Contained water</strong> means no bathroom wrestling match</li>'
    '<li><strong>Rinses clean</strong> in seconds</li></ul>'
    '<p><strong>Sizing:</strong> S for small paws, M for medium breeds, L for large.</p>' + ARRIVES),
 'wblanket': dict(handle='waterproof-snuggle-blanket', type='Comfort & Health',
    tags='dog, comfort, blanket, furniture', collection='comfort',
    body='<p><strong>The blanket that guards the couch.</strong></p>'
    '<p>Plush flannel on top, a waterproof layer through the middle. Drool, wet fur and '
    'accidents stay on the blanket, not in your cushions.</p>'
    '<ul><li><strong>Waterproof membrane</strong> protects whatever is underneath</li>'
    '<li><strong>Plush flannel face</strong> dogs actually choose to lie on</li>'
    '<li><strong>Machine washable</strong>, holds up wash after wash</li></ul>'
    '<p><strong>Sizing:</strong> XS for beds and car seats, S covers a sofa cushion.</p>' + ARRIVES),
 'thunder': dict(handle='calming-thunder-wrap', type='Comfort & Health',
    tags='dog, calming, comfort, anxiety', collection='comfort',
    body='<p><strong>Gentle pressure for loud nights.</strong></p>'
    '<p>A soft dimpled wrap that applies light, even pressure, the same idea as a weighted '
    'blanket. For storms, fireworks and travel days, it gives anxious dogs something that '
    'feels like being held.</p>'
    '<ul><li><strong>Light, even pressure</strong> has a naturally calming effect</li>'
    '<li><strong>Dimpled minky fabric</strong> is soothing to lie against</li>'
    '<li><strong>Machine washable</strong>, 81 x 61cm</li></ul>' + ARRIVES),
 'heartbeat': dict(handle='heartbeat-soothing-sloth', type='Comfort & Health',
    tags='dog, calming, comfort, puppy', collection='comfort',
    body='<p><strong>A heartbeat to curl up against.</strong></p>'
    '<p>A plush sloth with a battery heartbeat module tucked inside its pouch. The steady '
    'pulse mimics a littermate, easing first nights home, crate training and separation '
    'whines.</p>'
    '<ul><li><strong>Realistic heartbeat module</strong> with on-off control</li>'
    '<li><strong>Soft weighted plush</strong> made for leaning on</li>'
    '<li><strong>Module removes</strong> so the sloth can be washed</li></ul>' + ARRIVES),
 'fleece': dict(handle='paw-print-fleece-blanket', type='Comfort & Health',
    tags='dog, comfort, blanket', collection='comfort',
    body='<p><strong>The everywhere blanket.</strong></p>'
    '<p>A soft coral fleece throw for crates, car seats, sofa corners and anywhere else your '
    'dog decides is a bed. Light enough to pack, soft enough that they will not argue.</p>'
    '<ul><li><strong>Double-sided coral fleece</strong> with stitched trim</li>'
    '<li><strong>Light and packable</strong> for travel and crates</li>'
    '<li><strong>Machine washable</strong>, quick to dry</li></ul>'
    '<p><strong>Sizing:</strong> S 76 x 52cm, M 100 x 75cm.</p>' + ARRIVES),
}


def main():
    manifest = json.load(open(os.path.join(ROOT, 'config', 'round4_manifest.json')))
    picks = json.load(open(os.path.join(ROOT, 'config', 'round4_picks_variants.json')))
    weights = {}
    for key, info in picks.items():
        for v in info['variants']:
            w = v['w']
            try:
                weights[(key, v['sku'])] = int(float(str(w).split('-')[0]))
            except Exception:
                weights[(key, v['sku'])] = 200

    grooming_id = [c for c in api('GET', 'custom_collections.json?limit=50')['custom_collections']
                   if c['handle'] == 'grooming'][0]['id']
    coll_ids = {'grooming': grooming_id, 'comfort': COLL_COMFORT}

    made = {}
    for key, m in manifest.items():
        meta = META[key]
        opt = m['opt']
        if opt is None:
            options = [{'name': 'Title'}]
        elif isinstance(opt, str):
            options = [{'name': opt}]
        else:
            options = [{'name': o} for o in opt]

        variants = []
        for v in m['variants']:
            row = {'sku': v['sku'], 'price': v['price'],
                   'weight': weights.get((key, v['sku']), 200), 'weight_unit': 'g',
                   'inventory_management': 'shopify'}
            for i, val in enumerate(v['opts'], 1):
                row[f'option{i}'] = val
            variants.append(row)

        payload = {'product': {
            'title': m['title'], 'handle': f"wagvive-{meta['handle']}",
            'body_html': meta['body'], 'vendor': 'Wagvive',
            'product_type': meta['type'], 'tags': meta['tags'],
            'status': 'active', 'options': options, 'variants': variants}}
        p = api('POST', 'products.json', payload)['product']
        made[key] = {'id': p['id'], 'handle': p['handle'], 'title': m['title']}
        print(f"created {m['title']:38} id={p['id']} /{p['handle']} ({len(variants)} variants)")

        if meta['collection']:
            api('POST', 'collects.json', {'collect': {
                'product_id': p['id'], 'collection_id': coll_ids[meta['collection']]}})
        gql('mutation($id:ID!,$in:[PublicationInput!]!){publishablePublish(id:$id,input:$in){userErrors{message}}}',
            {'id': f"gid://shopify/Product/{p['id']}", 'in': [{'publicationId': PUB}]})
        time.sleep(0.6)

    with open(os.path.join(ROOT, 'config', 'round4_product_ids.json'), 'w', encoding='utf-8') as fh:
        json.dump(made, fh, indent=1)
    print('\nids -> config/round4_product_ids.json')


if __name__ == '__main__':
    main()
