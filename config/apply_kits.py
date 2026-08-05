#!/usr/bin/env python3
"""Apply the 2026-08-04 kit optimisation to the live store.

Compositions come from the freight-physics optimiser (optimise_kits.py) after
live CJ basket re-quotes; prices are charm00(0.80 x sum of NEW single prices)
from config/price_book.json. All five existing kits change composition, and
Calm & Comfort is new:

  New Puppy Kit      $54   Teddy, Toothbrush, Sneaker, Fleece, LED Dispenser
  Toy Kit            $49   Barnyard, Frisbee, Sneaker, Jingle, Corduroy
  Grooming Kit       $70   Slicker, Grinder, Toothbrush, Bath Robe, Paw Cup
  Enrichment Kit     $46   Talk Button, Lick Bowl, Slow Feeder, Bouncy Egg
  Travel Kit         $85   Bottle, Cooling Pad, Paw Cup, Bath Robe, Fleece
  Calm & Comfort     $109  Sloth, Thunder Wrap, Fleece, Cooling Pad, Big Squeak

Existing kits go through productBundleUpdate with a full replacement
components array (proven to change optionSelections in the #52 rebuild; if
Shopify rejects a composition change the script stops so the rebuild-and
-retire path can be used instead). The new kit uses productBundleCreate.

Option rules are derived, not hand-written: Size/Capacity options are PINNED
at the variant the price book costed (the dearest), colour-like options are
OPENED under a component label until Shopify's 3-parent-option cap is hit,
then pinned at the costed variant's value. Colour never changes the price, so
every parent variant gets the flat kit price and the same compare_at: the sum
of the components' new single prices.

    python config/apply_kits.py            # dry run: show plans
    python config/apply_kits.py --apply    # write + verify
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLLECTION_BUNDLES = 516867031329
PUBLICATION = 'gid://shopify/Publication/306551619873'
PIN_OPTIONS = {'Size', 'Capacity'}      # priced options: pin at costed variant
MAX_OPEN = 3                            # Shopify parent option cap

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


def api(method, path, payload=None, tries=5):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            # 429: rate limit. 409: Shopify still finalising a bundle
            # operation on this product; it clears within seconds.
            if exc.code in (429, 409) and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    return {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    return out


# ---------------------------------------------------------------- kit specs
BODY = {}

BODY['New Puppy Kit'] = """<p><strong>Everything the first month actually needs.</strong></p>
<p>Five things that solve the five problems every new puppy owner meets in
week one: the crying, the chewing, the teeth, the cold crate and the walks.</p>
<ul>
<li><strong>Cuddle companion teddy</strong> - something warm to sleep against
instead of crying for the litter</li>
<li><strong>Sneaker chew buddy</strong> - teething happens to YOUR shoes unless
it has one of its own</li>
<li><strong>Finger toothbrush</strong> - start teeth in week one and brushing is
normal for life</li>
<li><strong>Paw print fleece blanket</strong> - makes the crate a den, and the
car and the vet smell like home</li>
<li><strong>LED waste bag dispenser</strong> - clips to the leash for the first
walks, lights the way on the late one</li>
</ul>
<p>Cheaper than picking the pieces separately, and it arrives in one parcel.</p>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

BODY['Toy Kit'] = """<p><strong>Five toys, five different games.</strong></p>
<p>Dogs get bored of a toy, not of playing. This is a spread rather than five
versions of the same thing, so there is always one that suits the mood.</p>
<ul>
<li><strong>Barnyard squeaker</strong> - soft plush, for carrying and squeaking</li>
<li><strong>Watermelon rope frisbee</strong> - for throwing, indoors or out</li>
<li><strong>Sneaker chew buddy</strong> - for chewing that spares your own shoes</li>
<li><strong>Jingle plush ball</strong> - rattles when it rolls, for the dogs who
answer to sound</li>
<li><strong>Corduroy squeak pals</strong> - light enough for small dogs to carry
around all day</li>
</ul>
<p>Cheaper than picking any four separately, and it arrives in one parcel.</p>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

BODY['Grooming Essentials Kit'] = """<p><strong>Everything for a home grooming session.</strong></p>
<p>Five tools that cover coat, nails, teeth, bath and the walk home, so you are
not stopping halfway through because you are missing the one thing you needed.</p>
<ul>
<li><strong>Self-cleaning slicker brush</strong> - one click and the coat lets go
of the bristles, which is the part everyone hates</li>
<li><strong>Quiet nail grinder</strong> - no clipper crunch, which is what most
dogs are actually frightened of</li>
<li><strong>Finger toothbrush</strong> - the bit that gets skipped, made easier
by not needing a brush handle</li>
<li><strong>Quick-dry bath robe</strong> - ends the post-bath shake-water-everywhere
lap of the house</li>
<li><strong>Paw washing cup</strong> - soft silicone fins clean four muddy paws
before they reach the carpet</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

BODY['Dog Enrichment Kit'] = """<p><strong>A busy dog is a calm dog.</strong></p>
<p>Four tools that turn meals and quiet time into work a dog actually enjoys:
eating slower, licking to settle, learning to ask instead of barking, and one
toy that plays back.</p>
<ul>
<li><strong>Talk button</strong> - record a word and let them learn to press it.
Most dogs surprise their owners inside a week</li>
<li><strong>Lick bowl with ball</strong> - spread something tasty on it and
licking does what licking is for, calming them down</li>
<li><strong>Slow feeder bowl</strong> - dinner becomes a ten minute puzzle
instead of a thirty second inhale</li>
<li><strong>Bouncy egg squeaker</strong> - bounces off at angles a ball never
would, so solo play stays interesting</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

BODY['Travel Kit'] = """<p><strong>Everything for a day away from the water bowl.</strong></p>
<p>Five pieces that live by the door or in the car, so leaving the house with
the dog stops being a packing exercise.</p>
<ul>
<li><strong>Travel bottle and bowl in one</strong> - the lid flips open into a
drinking bowl, and unfinished water tips straight back inside</li>
<li><strong>Cooling comfort pad</strong> - a familiar place to lie down in the
car, the park or a cafe</li>
<li><strong>Paw washing cup</strong> - the mud stays at the boot, not on the
back seat</li>
<li><strong>Quick-dry bath robe</strong> - for the dog who found the river</li>
<li><strong>Paw print fleece blanket</strong> - a bed that smells like home,
wherever the day ends</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

BODY['Calm & Comfort Kit'] = """<p><strong>For the dog who finds the world a bit much.</strong></p>
<p>Storms, fireworks, guests, being left: five pieces that work on the same
problem from different sides, pressure, warmth, heartbeat and heat.</p>
<ul>
<li><strong>Heartbeat soothing sloth</strong> - a pulsing heartbeat to sleep
against, which is what settled them as a puppy</li>
<li><strong>Calming thunder wrap</strong> - steady, gentle pressure, the same
principle as swaddling</li>
<li><strong>Paw print fleece blanket</strong> - warmth and a familiar smell in
the spot they retreat to</li>
<li><strong>Cooling comfort pad</strong> - anxious dogs run hot; somewhere cool
to lie changes the mood</li>
<li><strong>Big squeak plush</strong> - a soft companion big enough to lean on
when the noise starts</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""

# kit -> (bundle product id or None to create, price, components as
#         (short title, parent label[, per-option overrides])).
#
# Overrides beat the auto rule where a tie-break lands badly:
#   {'Color': ('pin', 'Blue')}          force a pin at a named value
#   {'Size': ('open', 'Paw Cup Size')}   open a level-priced size (uses a slot)
# Component ORDER decides which colour choices win the 3 parent-option slots,
# so the highest-value choices are listed first and the toothbrush (pinned
# Blue in every kit, house convention) goes last.
KITS = {
    'Dog Enrichment Kit': (10470563053857, 46, [
        ('Talk Button', 'Talk Button'),
        ('Lick Bowl with Ball', 'Lick Bowl'),
        ('Slow Feeder Bowl', 'Slow Feeder'),
        ('Bouncy Egg Squeaker', 'Egg Squeaker'),
    ], 'bundle, kit, dog, enrichment, calming'),
    'New Puppy Kit': (10469667602721, 54, [
        ('Cuddle Companion Teddy', 'Teddy'),
        ('Sneaker Chew Buddy', 'Sneaker'),
        ('Paw Print Fleece Blanket', 'Blanket'),
        ('LED Waste Bag Dispenser', 'Bag Dispenser'),
        ('Finger Toothbrush', 'Toothbrush', {'Color': ('pin', 'Blue')}),
    ], 'bundle, kit, dog, puppy, new puppy'),
    'Toy Kit': (10469812863265, 49, [
        ('Barnyard Squeaker', 'Squeaker Pal'),
        ('Watermelon Rope Frisbee', 'Frisbee'),
        ('Sneaker Chew Buddy', 'Sneaker'),
        ('Jingle Plush Ball', 'Jingle Ball'),
        ('Corduroy Squeak Pals', 'Corduroy Pal'),
    ], 'bundle, kit, dog, toy set, play'),
    'Grooming Essentials Kit': (10470156140833, 70, [
        ('Self-Cleaning Slicker Brush', 'Slicker Brush'),
        ('Quiet Electric Nail Grinder', 'Nail Grinder'),
        ('Quick-Dry Bath Robe', 'Bath Robe'),
        ('Finger Toothbrush', 'Toothbrush', {'Color': ('pin', 'Blue')}),
        ('Paw Washing Cup', 'Paw Cup', {'Size': ('pin', 'M')}),
    ], 'bundle, kit, dog, grooming'),
    'Travel Kit': (10470563119393, 85, [
        ('Travel Water Bottle & Bowl', 'Water Bottle'),
        ('Cooling Comfort Pad', 'Cooling Pad'),
        # cup sizes are level-priced, and fit is why sizes exist: open them
        ('Paw Washing Cup', 'Paw Cup', {'Size': ('open', 'Paw Cup Size'),
                                        'Color': ('pin', 'Blue')}),
        ('Quick-Dry Bath Robe', 'Bath Robe'),
        ('Paw Print Fleece Blanket', 'Blanket'),
    ], 'bundle, kit, dog, travel, outdoor'),
    # Created 2026-08-04. The id is filled in so a re-run UPDATES it; leaving
    # None here would create a second Calm & Comfort Kit and cost this one its
    # handle.
    'Calm & Comfort Kit': (10477056491809, 109, [
        ('Heartbeat Soothing Sloth', 'Sloth'),
        ('Calming Thunder Wrap', 'Thunder Wrap'),
        ('Paw Print Fleece Blanket', 'Blanket'),
        ('Cooling Comfort Pad', 'Cooling Pad'),
        ('Big Squeak Plush', 'Squeak Plush'),
    ], 'bundle, kit, dog, calming, anxiety, comfort'),
}

PRODUCT_Q = '''query($id:ID!){product(id:$id){id title
  options{id name optionValues{name}}
  variants(first:60){nodes{sku price selectedOptions{name value}}}}}'''
UPDATE = '''mutation($input: ProductBundleUpdateInput!){
  productBundleUpdate(input:$input){
    productBundleOperation{id status} userErrors{field message}}}'''
CREATE = '''mutation($input: ProductBundleCreateInput!){
  productBundleCreate(input:$input){
    productBundleOperation{id status} userErrors{field message}}}'''
POLL = '''query($id:ID!){productOperation(id:$id){
  ... on ProductBundleOperation{status product{id title handle}
  userErrors{field message}}}}'''
COMPONENTS_Q = '''query($id:ID!){product(id:$id){status
  bundleComponents(first:10){nodes{componentProduct{title}}}}}'''


def load_catalog():
    """short title -> (product id, book prices by sku)."""
    book = json.load(open(os.path.join(ROOT, 'config', 'price_book.json'),
                          encoding='utf-8'))
    return {v['title'].replace('Wagvive ', ''): (int(pid), v['variants'])
            for pid, v in book.items()}


def component_plan(pid, prices, label, open_slots, overrides=None):
    """optionSelections for one component. Returns (selections, slots_used,
    singles_price) where singles_price is the costed (dearest) variant's."""
    overrides = overrides or {}
    d = gql(PRODUCT_Q, {'id': f'gid://shopify/Product/{pid}'})['data']['product']
    costed_sku = max(prices, key=lambda s: prices[s])
    costed = next((v for v in d['variants']['nodes'] if v['sku'] == costed_sku),
                  None)
    if not costed:
        raise SystemExit(f'{d["title"]}: costed sku {costed_sku} not on store')
    pin_at = {o['name']: o['value'] for o in costed['selectedOptions']}
    sels, used = [], 0
    for opt in d['options']:
        values = [ov['name'] for ov in opt['optionValues']]
        mode, arg = overrides.get(opt['name'], (None, None))
        if mode == 'pin' and arg not in values:
            raise SystemExit(f'{d["title"]}: cannot pin {opt["name"]}='
                             f'{arg!r}, have {values}')
        open_it = (mode == 'open' or
                   (mode is None and opt['name'] not in PIN_OPTIONS
                    and opt['name'] != 'Title' and len(values) > 1))
        if open_it and open_slots - used > 0:
            sels.append({'componentOptionId': opt['id'],
                         'name': arg if mode == 'open' else label,
                         'values': values})
            used += 1
        else:
            sels.append({'componentOptionId': opt['id'], 'name': opt['name'],
                         'values': [arg if mode == 'pin' else
                                    pin_at[opt['name']]]})
    return sels, used, prices[costed_sku]


def plan_kit(title, catalog):
    bundle_id, price, comps, tags = KITS[title]
    components, singles = [], 0.0
    open_slots = MAX_OPEN
    for spec in comps:
        short, label = spec[0], spec[1]
        overrides = spec[2] if len(spec) > 2 else None
        pid, prices = catalog[short]
        sels, used, single = component_plan(pid, prices, label, open_slots,
                                            overrides)
        open_slots -= used
        singles += single
        components.append({'quantity': 1,
                           'productId': f'gid://shopify/Product/{pid}',
                           'optionSelections': sels})
        opens = [s['name'] for s in sels if len(s['values']) > 1]
        pins = {s['name']: s['values'][0] for s in sels if len(s['values']) == 1}
        print(f'   {short:34} ${single:>6.2f}  open={opens or "-"} pin={pins or "-"}')
    print(f'   singles ${singles:.2f} -> kit ${price:.2f} '
          f'(save {(1 - price / singles) * 100:.0f}%)')
    return components, singles


def run_op(mutation, inp):
    key = 'productBundleUpdate' if 'Update' in mutation else 'productBundleCreate'
    r = gql(mutation, {'input': inp})['data'][key]
    if r['userErrors']:
        print('   ERRORS:', json.dumps(r['userErrors'])[:400])
        return None
    op = r['productBundleOperation']['id']
    for _ in range(60):
        time.sleep(2)
        p = gql(POLL, {'id': op})['data']['productOperation']
        if p['status'] == 'COMPLETE':
            return p.get('product') or True
        if p['status'] == 'FAILED':
            print('   OP FAILED:', json.dumps(p.get('userErrors'))[:300])
            return None
    print('   timed out')
    return None


def reprice(pid, price, compare_at):
    full = api('GET', f'products/{pid}.json')['product']
    n = 0
    for v in full['variants']:
        if (v['price'] != f'{price:.2f}'
                or (v.get('compare_at_price') or '') != f'{compare_at:.2f}'):
            api('PUT', f'variants/{v["id"]}.json', {'variant': {
                'id': v['id'], 'price': f'{price:.2f}',
                'compare_at_price': f'{compare_at:.2f}'}})
            n += 1
            time.sleep(0.55)
    return len(full['variants']), n, full['status']


def main():
    apply = '--apply' in sys.argv
    catalog = load_catalog()
    made = {}
    for title in KITS:
        bundle_id, price, comps, tags = KITS[title]
        print(f'\n== {title}  (${price})' + ('  [CREATE]' if not bundle_id else ''))
        components, singles = plan_kit(title, catalog)
        if not apply:
            continue

        if bundle_id:
            ok = run_op(UPDATE, {'productId': f'gid://shopify/Product/{bundle_id}',
                                 'components': components})
            if not ok:
                print(f'   STOPPING: update rejected for {title}; '
                      f'use rebuild_kits.py path')
                return 1
            pid = bundle_id
        else:
            product = run_op(CREATE, {'title': title, 'components': components})
            if not product or product is True:
                print('   STOPPING: create failed')
                return 1
            pid = int(product['id'].split('/')[-1])
            api('POST', 'collects.json', {'collect': {
                'product_id': pid, 'collection_id': COLLECTION_BUNDLES}})
            gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
                     publishablePublish(id: $id, input: $input) {
                       userErrors { message } } }''',
                {'id': product['id'], 'input': [{'publicationId': PUBLICATION}]})
            made[title] = pid

        api('PUT', f'products/{pid}.json', {'product': {
            'id': pid, 'body_html': BODY[title], 'vendor': 'Wagvive',
            'product_type': 'Bundles & Kits', 'status': 'active', 'tags': tags}})
        total, changed, status = reprice(pid, float(price), singles)
        print(f'   -> {pid}: {total} parent variants, {changed} repriced, '
              f'status {status}')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    # verify against the live system
    print('\n--- verify ---')
    fail = False
    for title in KITS:
        bundle_id = KITS[title][0] or made.get(title)
        d = gql(COMPONENTS_Q, {'id': f'gid://shopify/Product/{bundle_id}'}
                )['data']['product']
        got = sorted(n['componentProduct']['title'].replace('Wagvive ', '')
                     for n in d['bundleComponents']['nodes'])
        want = sorted(s[0] for s in KITS[title][2])
        ok = got == want and d['status'] == 'ACTIVE'
        fail |= not ok
        print(f'  {"OK " if ok else "BAD"} {title}: {d["status"]}, '
              f'{len(got)} components' + ('' if ok else f' got {got}'))

    if made:
        path = os.path.join(ROOT, 'config', 'kit_ids.json')
        live = json.load(open(path, encoding='utf-8'))
        live.update(made)
        json.dump(live, open(path, 'w'), indent=1)
        print('kit_ids.json updated:', made)
    return 1 if fail else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
