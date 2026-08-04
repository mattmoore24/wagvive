#!/usr/bin/env python3
"""Open up variant choice inside the five kit bundles.

The kits are already Shopify bundles (productBundleCreate, one fixed variant
per component). This script re-runs each bundle through productBundleUpdate
with MULTI-value optionSelections so customers pick colours per component.

Rules that shape the mapping:
  - Shopify caps a product at 3 options; single-value selections create no
    parent option, so each kit exposes at most 3 choosable components and
    pins the rest (documented per kit below).
  - Parent option names say what the choice controls ("Slicker Brush").
  - After update the parent's variants regenerate at component-sum prices;
    we bulk re-price every variant to the flat kit price (colour never
    changes the price - house policy).

Run:  python config/open_kit_variants.py grooming   (one kit)
      python config/open_kit_variants.py all
"""
import json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


# (component product id, {component option name: parent option name (None = pin),
#                         with pinned value when parent name is None})
# 'open' = expose every value under the parent label; ('pin', value) = fix it.
KITS = {
    'grooming': {
        'bundle': 10470156140833, 'price': '85.00',
        'components': [
            (10456336990497, {'Colour': ('open', 'Slicker Brush')}),
            (10456337056033, {'Colour': ('open', 'Hair Mitt')}),
            (10456337318177, {'Colour': ('open', 'Nail Grinder')}),
            (10469666062625, {'Colour': ('pin', 'Blue')}),          # toothbrush
        ]},
    'enrichment': {
        'bundle': 10470563053857, 'price': '98.00',
        'components': [
            (10456337613089, {'Colour': ('open', 'Slow Feeder')}),
            (10456337547553, {'Colour': ('pin', 'Grey'),            # water bowl
                              'Capacity': ('pin', '1.5L')}),
            (10470547587361, {'Colour': ('open', 'Lick Bowl')}),
            (10470547652897, {'Colour': ('open', 'Talk Button')}),
        ]},
    'travel': {
        'bundle': 10470563119393, 'price': '77.00',
        'components': [
            (10470547489057, {'Colour': ('open', 'Water Bottle')}),
            (10469666128161, {'Colour': ('open', 'Bag Dispenser')}),
            (10464689881377, {'Colour': ('open', 'Cooling Pad'),
                              'Size': ('pin', 'Medium 24" x 20"')}),
            (10469803819297, {'Title': ('pin', 'Default Title')}),  # frisbee
        ]},
    'toy': {
        'bundle': 10469812863265, 'price': '65.00',
        'components': [
            (10469665308961, {'Title': ('pin', 'Default Title')}),  # duck
            (10469665177889, {'Character': ('open', 'Squeaker Pal')}),
            (10469665603873, {'Animal': ('open', 'Rope-Limb Pal')}),
            (10469803819297, {'Title': ('pin', 'Default Title')}),  # frisbee
        ]},
    'puppy': {
        'bundle': 10469667602721, 'price': '79.00',
        'components': [
            (10464690143521, {}),   # placeholder - resolved live below
        ]},
}

# The puppy kit's live component set is read from the bundle itself (its sofa
# cover id differs from the retired US-warehouse cover). Selections applied:
PUPPY_RULES = {
    'Wagvive Waterproof Sofa & Furniture Cover': {'Colour': ('open', 'Sofa Cover'),
                                                  'Size': ('pin', 'Small 20" x 26"')},
    'Wagvive Cooling Comfort Pad': {'Colour': ('open', 'Cooling Pad'),
                                    'Size': ('pin', 'Medium 24" x 20"')},
    'Wagvive LED Waste Bag Dispenser': {'Colour': ('open', 'Bag Dispenser')},
    'Wagvive Dental Duck Chew Toy': {'Title': ('pin', 'Default Title')},
}

PRODUCT_Q = '''query($id:ID!){product(id:$id){id title
  options{id name optionValues{name}}}}'''

UPDATE = '''mutation($input: ProductBundleUpdateInput!){
  productBundleUpdate(input:$input){
    productBundleOperation{id status}
    userErrors{field message}}}'''

POLL = '''query($id:ID!){productOperation(id:$id){
  ... on ProductBundleOperation{id status product{id} userErrors{field message}}}}'''


def selections_for(pid, rules):
    d = gql(PRODUCT_Q, {'id': f'gid://shopify/Product/{pid}'})['data']['product']
    sels = []
    for opt in d['options']:
        rule = rules.get(opt['name'])
        if rule is None:
            raise SystemExit(f"{d['title']}: option {opt['name']!r} has no rule")
        mode, arg = rule
        if mode == 'open':
            values = [ov['name'] for ov in opt['optionValues']]
            parent_name = arg
        else:
            values = [arg]
            parent_name = opt['name']
        sels.append({'componentOptionId': opt['id'], 'name': parent_name,
                     'values': values})
    return d['title'], sels


def open_kit(key):
    spec = KITS[key]
    bundle_gid = f"gid://shopify/Product/{spec['bundle']}"

    comp_specs = spec['components']
    if key == 'puppy':
        r = gql('{product(id:"%s"){bundleComponents(first:10){nodes{componentProduct{id title}}}}}' % bundle_gid)
        comp_specs = []
        for n in r['data']['product']['bundleComponents']['nodes']:
            pid = int(n['componentProduct']['id'].split('/')[-1])
            rules = PUPPY_RULES.get(n['componentProduct']['title'])
            if not rules:
                raise SystemExit(f"no rules for puppy component {n['componentProduct']['title']}")
            comp_specs.append((pid, rules))

    components = []
    for pid, rules in comp_specs:
        title, sels = selections_for(pid, rules)
        combos = 1
        for s in sels:
            combos *= len(s['values'])
        print(f"  {title[:44]:46} -> {[(s['name'], len(s['values'])) for s in sels]}")
        components.append({'quantity': 1,
                           'productId': f'gid://shopify/Product/{pid}',
                           'optionSelections': sels})

    r = gql(UPDATE, {'input': {'productId': bundle_gid, 'components': components}})
    d = r['data']['productBundleUpdate']
    if d['userErrors']:
        print('  ERRORS:', json.dumps(d['userErrors'])[:400]); return False
    op = d['productBundleOperation']['id']
    for _ in range(45):
        time.sleep(2)
        p = gql(POLL, {'id': op})['data']['productOperation']
        if p['status'] == 'COMPLETE':
            break
        if p['status'] == 'FAILED':
            print('  OP FAILED:', json.dumps(p.get('userErrors'))[:300]); return False
    else:
        print('  timed out'); return False

    # re-price every regenerated parent variant to the flat kit price
    full = api('GET', f"products/{spec['bundle']}.json")['product']
    n = 0
    for v in full['variants']:
        if v['price'] != spec['price']:
            api('PUT', f"variants/{v['id']}.json",
                {'variant': {'id': v['id'], 'price': spec['price']}})
            n += 1
        time.sleep(0.3)
    print(f"  {full['title']}: {len(full['variants'])} variants, {n} re-priced to ${spec['price']}")
    return True


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    keys = list(KITS) if which == 'all' else [which]
    for k in keys:
        print(f'== {k} ==')
        ok = open_kit(k)
        if not ok:
            sys.exit(1)
