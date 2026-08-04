#!/usr/bin/env python3
"""Rebuild a kit whose composition has changed.

Four kits, four distinct life stages / jobs:

  New Puppy Kit        teething, accidents, first walks
  Senior Dog Kit       joints, hydration, digestion, teeth
  Grooming Essentials  coat, nails, teeth
  Toy Kit              play

A bundle cannot have components added or swapped through the API once it exists,
so any change of composition means creating a new product and archiving the old
one. Pass the kit titles to rebuild as arguments; with no arguments it rebuilds
everything, which is almost never what you want.

Two things this has to get right, both learned the hard way:

  * Shopify keeps a handle reserved even after the product is archived, so the
    outgoing kit is renamed to `<handle>-retired` BEFORE the replacement is
    created. Otherwise the new kit lands on `senior-dog-kit-1` and every link,
    menu entry and metafield that names the clean handle points at a dead page.
  * Losing a component silently moves a kit to DRAFT. Nothing warns you. Check
    every kit is still ACTIVE after touching any variant.

Every kit is priced off its live component total, so the advertised saving is
real. Bundles are created with no media, so run make_kit_covers.py afterwards,
and link_kits.py to repoint the component pages at the new kit.
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLLECTION_BUNDLES = 516867031329
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

SENIOR_BODY = """<p><strong>For the dog who has earned an easier life.</strong></p>
<p>Older dogs need different things, and they need them before anything looks
wrong. These four cover the parts that quietly get harder with age.</p>
<ul>
<li><strong>Cooling comfort pad</strong> - stiff joints and poor heat regulation
are the two complaints that come with age. A cool, even surface helps both.</li>
<li><strong>Anti-spill water bowl</strong> - kidney function declines with age and
steady hydration matters more. The floating disc stops the spillage that makes
owners put the bowl somewhere inconvenient.</li>
<li><strong>Slow feeder bowl</strong> - digestion slows down. So should dinner.</li>
<li><strong>Finger toothbrush</strong>: dental disease is one of the most
common conditions in older dogs. A soft sleeve over your finger gives you far
more control than a brush handle, and most dogs tolerate a finger better.</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

GROOMING_BODY = """<p><strong>Everything for a home grooming session.</strong></p>
<p>Four tools that cover coat, nails and teeth, so you are not stopping halfway
through because you are missing the one thing you needed.</p>
<ul>
<li><strong>Self-cleaning slicker brush</strong> - one click and the coat lets go
of the bristles, which is the part everyone hates</li>
<li><strong>Shedding gloves</strong> - for the dogs who will not tolerate a brush
but will happily be stroked</li>
<li><strong>Quiet nail grinder</strong> - no clipper crunch, which is what most
dogs are actually frightened of</li>
<li><strong>Finger toothbrush</strong>: the bit that gets skipped, made
easier by not needing a brush handle</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

TOY_BODY = """<p><strong>Four toys, four different games.</strong></p>
<p>Dogs get bored of a toy, not of playing. This is a spread rather than four
versions of the same thing - something to squeak, something to chew, something to
shake and something to throw - so there is always one that suits the mood.</p>
<ul>
<li><strong>Dental duck</strong> - ridged latex, for chewing that does something</li>
<li><strong>Barnyard squeaker</strong> - soft plush, for carrying and squeaking</li>
<li><strong>Woodland rope-limb plush</strong> - rope arms and legs for tugging</li>
<li><strong>Watermelon rope frisbee</strong> - for throwing, indoors or out</li>
</ul>
<p>Cheaper than picking any three separately, and it arrives in one parcel.</p>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

# The dental slot appears in TWO kits, so it lives in one place here. A bundle
# cannot have components swapped after creation, and losing a component silently
# drafts the kit, so changing this means rebuilding both.
#
# Was the Dental & Ear Wipes (CJYD216979603CX). Moved to the Finger Toothbrush on
# 2026-08-01 for one reason: photography. Every image CJ has for that wipes
# listing is a branded plastic can with a cat printed on the label, and a search
# of the whole catalogue turned up no wipes product that is genuinely better -
# the closest alternatives either drop dental entirely or carry another
# manufacturer's retail packaging in every frame. The toothbrush is clean,
# brand-neutral, dog-appropriate, cheaper to put in a kit, and reusable rather
# than a consumable. The wipes stay on the site as a standalone.
DENTAL = (10469666062625, 'CJYD262686408HS')   # Finger Toothbrush, Blue


ENRICHMENT_BODY = """<p><strong>A busy dog is a calm dog.</strong></p>
<p>Four tools that turn meals and quiet time into work a dog actually enjoys:
eating slower, drinking without mess, licking to settle, and learning to ask
for things instead of barking at them.</p>
<ul>
<li><strong>Slow feeder bowl</strong>: dinner becomes a ten minute puzzle instead
of a thirty second inhale</li>
<li><strong>Anti-spill water bowl</strong>: steady hydration without the puddle</li>
<li><strong>Lick bowl with ball</strong>: spread something tasty on it and licking
does what licking is for, calming them down</li>
<li><strong>Talk button</strong>: record a word and let them learn to press it.
Most dogs surprise their owners inside a week</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

TRAVEL_BODY = """<p><strong>Everything for a day away from the water bowl.</strong></p>
<p>Four pieces that live by the door or in the car, so leaving the house with
the dog stops being a packing exercise.</p>
<ul>
<li><strong>Travel bottle and bowl in one</strong>: the lid flips open into a
drinking bowl, and unfinished water tips straight back inside</li>
<li><strong>LED waste bag dispenser</strong>: clips to the leash, lights the way
on late walks</li>
<li><strong>Cooling comfort pad</strong>: a familiar place to lie down in the car,
the park or a cafe</li>
<li><strong>Watermelon rope frisbee</strong>: because a day out should include
one proper game of fetch</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

# title -> (components as (product_id, sku), body, tags)
KITS = {
    'Senior Dog Kit': (
        [(10464689881377, 'CJPM292000021UF'),   # cooling pad, LG / Medium
         (10456337547553, 'CJGY102545403CX'),   # water bowl, Grey / 1.5L
         (10456337613089, 'CJGY174846501AZ'),   # slow feeder, Green
         DENTAL],
        SENIOR_BODY, 'bundle, kit, dog, senior, comfort, health'),
    'Grooming Essentials Kit': (
        [(10456336990497, 'CJMY195218501AZ'),   # slicker brush, Green
         (10456337056033, 'CJYD233200807GT'),   # gloves, Dark Brown
         (10456337318177, 'CJGY200835701AZ'),   # nail grinder, Deep Green
         DENTAL],
        GROOMING_BODY, 'bundle, kit, dog, grooming'),
    'Dog Enrichment Kit': (
        [(10456337613089, 'CJGY174846501AZ'),   # slow feeder, Green
         (10456337547553, 'CJGY102545403CX'),   # water bowl, Grey / 1.5L
         (10470547587361, 'CJFT286015801AZ'),   # lick bowl, Blue
         (10470547652897, 'CJYD232561605EV')],  # talk button, Green
        ENRICHMENT_BODY, 'bundle, kit, dog, enrichment, calming'),
    'Travel Kit': (
        [(10470547489057, 'CJDT287487301AZ'),   # travel bottle, Blue
         (10469666128161, 'CJYD222274205EV'),   # LED dispenser, Grey
         (10464689881377, 'CJPM292000021UF'),   # cooling pad, LG / Medium
         (10469803819297, 'CJMY124424501AZ')],  # watermelon frisbee
        TRAVEL_BODY, 'bundle, kit, dog, travel, outdoor'),
    'Toy Kit': (
        [(10469665308961, 'CJST217844101AZ'),   # dental duck
         (10469665177889, 'CJYD242287801AZ'),   # barnyard squeaker, blue donkey
         (10469665603873, 'CJST258364603CX'),   # woodland rope-limb, fox
         (10469803819297, 'CJMY124424501AZ')],  # watermelon frisbee
        TOY_BODY, 'bundle, kit, dog, toy set, play'),
}

# kits being replaced -> hand over the handle, then archive once the new one is live
RETIRE = {'Senior Dog Kit': 10469812142369,
          'Grooming Essentials Kit': 10469812470049}


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


PRODUCT_Q = """
query($id: ID!) {
  product(id: $id) {
    title
    options { id name optionValues { id name } }
    variants(first: 40) { nodes { id sku price selectedOptions { name value } } }
  }
}
"""
CREATE = """
mutation($input: ProductBundleCreateInput!) {
  productBundleCreate(input: $input) {
    productBundleOperation { id status }
    userErrors { field message }
  }
}
"""
POLL = """
query($id: ID!) {
  productOperation(id: $id) {
    ... on ProductBundleOperation {
      status product { id title handle } userErrors { message }
    }
  }
}
"""


def build(title, components, body, tags):
    parts, retail = [], 0.0
    for pid, sku in components:
        d = gql(PRODUCT_Q, {'id': f'gid://shopify/Product/{pid}'})['data']['product']
        var = next((v for v in d['variants']['nodes'] if v['sku'] == sku), None)
        if not var:
            print(f'   !! {sku} missing from {d["title"]}'); return None
        retail += float(var['price'])
        chosen = {o['name']: o['value'] for o in var['selectedOptions']}
        sels = []
        for opt in d['options']:
            want = chosen.get(opt['name'])
            if any(ov['name'] == want for ov in opt['optionValues']):
                sels.append({'componentOptionId': opt['id'], 'name': opt['name'],
                             'values': [want]})
        parts.append({'quantity': 1,
                      'productId': f'gid://shopify/Product/{pid}',
                      'optionSelections': sels})
        print(f'   {d["title"][:38]:40} {sku:20} ${float(var["price"]):.2f}')

    res = gql(CREATE, {'input': {'title': title, 'components': parts}})
    d = res.get('data', {}).get('productBundleCreate') or {}
    if d.get('userErrors'):
        print('   errors:', json.dumps(d['userErrors'])[:300]); return None
    op = d['productBundleOperation']['id']
    product = None
    for _ in range(30):
        time.sleep(2)
        p = gql(POLL, {'id': op})['data']['productOperation']
        if p['status'] == 'COMPLETE':
            product = p['product']; break
        if p['status'] == 'FAILED':
            print('   FAILED:', json.dumps(p.get('userErrors'))[:200]); return None
    if not product:
        print('   timed out'); return None

    pid = int(product['id'].split('/')[-1])
    # Price so the saving is real and consistent with the other kits.
    price = round(retail * 0.80)
    full = api('GET', f'products/{pid}.json')['product']
    v = full['variants'][0]
    api('PUT', f'variants/{v["id"]}.json', {'variant': {
        'id': v['id'], 'price': f'{price:.2f}',
        'compare_at_price': f'{retail:.2f}'}})
    api('PUT', f'products/{pid}.json', {'product': {
        'id': pid, 'body_html': body, 'vendor': 'Wagvive',
        'product_type': 'Bundles & Kits', 'status': 'active', 'tags': tags}})
    api('POST', 'collects.json',
        {'collect': {'product_id': pid, 'collection_id': COLLECTION_BUNDLES}})
    gql("""mutation($id: ID!, $input: [PublicationInput!]!) {
             publishablePublish(id: $id, input: $input) { userErrors { message } } }""",
        {'id': product['id'], 'input': [{'publicationId': PUBLICATION}]})
    print(f'   -> {pid}  ${price:.2f} (was ${retail:.2f}, save '
          f'{(1 - price / retail) * 100:.0f}%)\n')
    return pid


def main():
    # Only rebuild what changed. Rebuilding an unchanged kit would create a
    # duplicate and cost it its handle for nothing.
    wanted = sys.argv[1:] or list(KITS)
    made = {}
    for title in wanted:
        comps, body, tags = KITS[title]
        print(title)
        old = RETIRE.get(title)
        if old:
            # Shopify keeps a handle reserved even after archiving, so the
            # replacement would land on "senior-dog-kit-1" unless the outgoing
            # kit gives the handle up first.
            h = api('GET', f'products/{old}.json?fields=handle')['product']['handle']
            if not h.endswith('-retired'):
                api('PUT', f'products/{old}.json',
                    {'product': {'id': old, 'handle': f'{h}-retired'}})
                print(f'   freed handle /{h}')
        pid = build(title, comps, body, tags)
        if pid:
            made[title] = pid
        elif old:
            api('PUT', f'products/{old}.json', {'product': {'id': old, 'handle': h}})
            print(f'   build failed, handle /{h} given back')

    for title, old in RETIRE.items():
        if title in made:
            api('PUT', f'products/{old}.json',
                {'product': {'id': old, 'status': 'archived'}})
            print(f'archived old {title} ({old})')

    path = os.path.join(ROOT, 'config', 'kit_ids.json')
    live = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            live = json.load(fh)
    live.update(made)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(live, fh, indent=1)
    print(f'\n{len(made)} kit(s) built')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
