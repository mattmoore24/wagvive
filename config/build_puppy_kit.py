#!/usr/bin/env python3
"""Create the New Puppy Kit as a real Shopify bundle.

Contents answer the four things a new puppy owner needs in week one: somewhere to
sleep, protection for the furniture that is about to be tested, something to chew
that is not the furniture, and bags for the walks.

  Waterproof Sofa & Furniture Cover (Small)   $28
  Cooling Comfort Pad (Medium)                $34
  LED Waste Bag Dispenser                     $14
  Dental Duck Chew Toy                        $20
                                    components $96  ->  kit $79 (18% off)

All four ship as ONE consolidated parcel ($13.37, YunExpress Sensitive, 4-7 days),
which is what makes the discount affordable - the Grooming kit has to split into
four parcels at $28.38 and is priced accordingly.

productBundleCreate is asynchronous, so this polls the ProductBundleOperation
until it resolves rather than assuming success.
"""
# DELIVERY PROMISE LITERAL. The canonical text lives in
# config/delivery_promise.py; the literal below is a copy because it sits
# inside plain triple-quoted HTML. If they diverge, config/audit_claims.py
# fails against the LIVE store and config/apply_delivery_promise.py repairs
# every product body in one pass.
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICE = 79.00
COMPARE_AT = 96.00
COLLECTION_BUNDLES = 516867031329
PUBLICATION = 'gid://shopify/Publication/306551619873'

# product id -> the exact variant SKU this kit ships
COMPONENTS = [
    (10468724506913, 'CJYD225186001AZ'),   # cover, Black / Small
    (10464689881377, 'CJPM292000021UF'),   # cooling pad, Light Grey / Medium
    (10469666128161, 'CJYD222274205EV'),   # waste bag dispenser, Grey
    (10469665308961, 'CJST217844101AZ'),   # dental duck
]

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

BODY = """<p><strong>The first fortnight, sorted.</strong></p>
<p>A puppy arrives and suddenly you need four things at once. This is those four
things, chosen so they arrive together in one parcel rather than trickling in all
week.</p>
<ul>
<li><strong>Waterproof furniture cover</strong> - because the sofa is about to be
tested, and a waterproof layer is easier than a conversation about boundaries</li>
<li><strong>Cooling comfort pad</strong> - somewhere that is theirs, which helps
more than most things with settling in</li>
<li><strong>Dental duck chew toy</strong> - teething has to go somewhere, and it
may as well go somewhere useful</li>
<li><strong>LED waste bag dispenser</strong> - clips to the lead, lights up, for
the walks you will be doing in the dark</li>
</ul>
<p>Bought separately these come to $96. Together they are $79.</p>
<p><strong>Arrives in 10 to 16 business days, in one parcel.</strong></p>"""


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
    variants(first: 40) { nodes { id sku selectedOptions { name value } } }
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
      id status
      product { id title handle }
      userErrors { field message }
    }
  }
}
"""


def main():
    parts = []
    for pid, sku in COMPONENTS:
        d = gql(PRODUCT_Q, {'id': f'gid://shopify/Product/{pid}'})['data']['product']
        variant = next((v for v in d['variants']['nodes'] if v['sku'] == sku), None)
        if not variant:
            print(f'!! {sku} not found on {d["title"]}'); sys.exit(1)
        chosen = {o['name']: o['value'] for o in variant['selectedOptions']}
        selections = []
        for opt in d['options']:
            want = chosen.get(opt['name'])
            val = next((ov for ov in opt['optionValues'] if ov['name'] == want), None)
            if val:
                selections.append({'componentOptionId': opt['id'],
                                   'name': opt['name'],
                                   'values': [val['name']]})
        parts.append({'quantity': 1,
                      'productId': f'gid://shopify/Product/{pid}',
                      'optionSelections': selections})
        print(f'   {d["title"][:40]:42} {sku}  {chosen}')

    res = gql(CREATE, {'input': {
        'title': 'New Puppy Kit',
        'components': parts,
    }})
    d = res.get('data', {}).get('productBundleCreate') or {}
    if d.get('userErrors'):
        print('errors:', json.dumps(d['userErrors'])[:400]); sys.exit(1)
    op_id = d['productBundleOperation']['id']
    print(f'\noperation {op_id} -> {d["productBundleOperation"]["status"]}')

    product = None
    for _ in range(30):
        time.sleep(2)
        p = gql(POLL, {'id': op_id})['data']['productOperation']
        if p['status'] == 'COMPLETE':
            if p.get('userErrors'):
                print('op errors:', json.dumps(p['userErrors'])[:300]); sys.exit(1)
            product = p['product']
            break
        if p['status'] == 'FAILED':
            print('operation FAILED:', json.dumps(p.get('userErrors'))[:300]); sys.exit(1)
    if not product:
        print('timed out waiting for bundle'); sys.exit(1)

    pid = int(product['id'].split('/')[-1])
    print(f'created bundle {pid}  {product["handle"]}')

    full = api('GET', f'products/{pid}.json')['product']
    v = full['variants'][0]
    api('PUT', f'variants/{v["id"]}.json', {'variant': {
        'id': v['id'], 'price': f'{PRICE:.2f}',
        'compare_at_price': f'{COMPARE_AT:.2f}'}})
    api('PUT', f'products/{pid}.json', {'product': {
        'id': pid, 'body_html': BODY, 'vendor': 'Wagvive',
        'product_type': 'Bundles & Kits', 'status': 'active',
        'tags': 'bundle, kit, puppy, dog, starter'}})
    api('POST', 'collects.json',
        {'collect': {'product_id': pid, 'collection_id': COLLECTION_BUNDLES}})
    gql("""mutation($id: ID!, $input: [PublicationInput!]!) {
             publishablePublish(id: $id, input: $input) { userErrors { message } } }""",
        {'id': product['id'], 'input': [{'publicationId': PUBLICATION}]})

    print(f'priced ${PRICE:.2f} (compare-at ${COMPARE_AT:.2f}), published, '
          f'added to Bundles & Kits')
    with open(os.path.join(ROOT, 'config', 'puppy_kit_id.txt'), 'w') as fh:
        fh.write(str(pid))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
