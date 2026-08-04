#!/usr/bin/env python3
"""
Create a replacement Comfort & Health Kit.

The original was created by the Shopify Bundles app, so productBundleUpdate is
refused with "This product is currently owned by a different app". Instead we
create a new bundle owned by our own app and retire the old one, freeing its
handle so the storefront URL and any existing links keep working.

Components: Cooling Comfort Pad (Light Grey, Medium) + Anti-Spill Water Bowl
(Grey, 1.5L) + Slow Feeder Bowl (Green). Landed $29.46; $79 retail is 59.4%
margin and a $19 saving against $98 bought separately.
"""
import json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import margin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_KIT = 10458198081825
HANDLE = 'comfort-health-kit'
COMFORT_COLLECTION = 516731371809
BUNDLES_COLLECTION = 516867031329
CATALOG_COLLECTION = 516730487073
ONLINE_STORE_PUB = 'gid://shopify/Publication/306551619873'

COMPONENTS = [
    (10464689881377, ['Light Grey', 'Medium 24" x 20"']),
    (10456337547553, ['Grey', '1.5L']),
    (10456337613089, ['Green']),
]

BODY = (
    "<p><strong>Comfort, hydration and rest &mdash; covered.</strong></p>"
    "<p>The three things that make the biggest daily difference for an older dog: somewhere "
    "cool to lie down, water they can drink without soaking the floor, and a bowl that slows "
    "dinner down. Bought together, and cheaper than buying them apart.</p>"
    "<p><strong>This kit includes:</strong></p><ul>"
    "<li>Cooling Comfort Pad &mdash; ice silk, Medium 24&Prime; &times; 20&Prime;, light grey</li>"
    "<li>Anti-Spill Floating Water Bowl &mdash; 1.5L, grey</li>"
    "<li>Slow Feeder Bowl &mdash; green</li></ul>"
    "<p>Ships together in one parcel. Save $19 against buying the three separately.</p>")

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


def component_input(pid, wanted):
    d = gql("""query($id:ID!){product(id:$id){title options{id name optionValues{name}}}}""",
            {'id': f'gid://shopify/Product/{pid}'})
    prod = d['data']['product']
    sels = []
    for opt, want in zip(prod['options'], wanted):
        names = [v['name'] for v in opt['optionValues']]
        if want not in names:
            raise SystemExit(f'{prod["title"]}: {opt["name"]} has no {want!r} (has {names})')
        sels.append({'componentOptionId': opt['id'], 'name': opt['name'], 'values': [want]})
    return prod['title'], {'productId': f'gid://shopify/Product/{pid}',
                           'quantity': 1, 'optionSelections': sels}


def main():
    # free the handle and retire the old kit
    api('PUT', f'products/{OLD_KIT}.json', {'product': {
        'id': OLD_KIT, 'handle': 'comfort-health-kit-retired', 'status': 'archived'}})
    print(f'old kit {OLD_KIT} -> archived, handle freed')

    comps = []
    for pid, wanted in COMPONENTS:
        title, ci = component_input(pid, wanted)
        comps.append(ci)
        print(f'   component: {title[:38]:40} {" / ".join(wanted)}')

    res = gql("""
      mutation($input: ProductBundleCreateInput!) {
        productBundleCreate(input: $input) {
          productBundleOperation { id status }
          userErrors { field message }
        }
      }""", {'input': {'title': 'Comfort & Health Kit', 'components': comps}})
    op = (res.get('data', {}).get('productBundleCreate') or {})
    if res.get('errors') or op.get('userErrors'):
        print('create failed:', json.dumps(res)[:500]); sys.exit(1)
    op_id = op['productBundleOperation']['id']
    print(f'\noperation {op_id.split("/")[-1]} status={op["productBundleOperation"]["status"]}')

    new_pid = None
    for _ in range(20):
        time.sleep(2)
        d = gql("""query($id:ID!){node(id:$id){... on ProductBundleOperation{
                   status product{id} userErrors{message}}}}""", {'id': op_id})
        n = d['data']['node']
        if n['status'] == 'COMPLETE':
            if n.get('userErrors'):
                print('operation errors:', json.dumps(n['userErrors'])[:300]); sys.exit(1)
            new_pid = int(n['product']['id'].split('/')[-1])
            break
    if not new_pid:
        print('operation did not complete in time'); sys.exit(1)
    print(f'new bundle product id {new_pid}')

    p = api('GET', f'products/{new_pid}.json')['product']
    vid = p['variants'][0]['id']
    api('PUT', f'products/{new_pid}.json', {'product': {
        'id': new_pid, 'handle': HANDLE, 'body_html': BODY,
        'vendor': 'Wagvive', 'product_type': 'Kit Bundle',
        'tags': 'comfort, bundle, kit, senior pet, dog', 'status': 'active',
        'variants': [{'id': vid, 'price': '79.00', 'compare_at_price': '98.00'}]}})

    for cid in (COMFORT_COLLECTION, BUNDLES_COLLECTION, CATALOG_COLLECTION):
        try:
            api('POST', 'collects.json', {'collect': {'product_id': new_pid, 'collection_id': cid}})
        except urllib.error.HTTPError:
            pass
    gql("""mutation($id:ID!,$in:[PublicationInput!]!){
             publishablePublish(id:$id,input:$in){userErrors{message}}}""",
        {'id': f'gid://shopify/Product/{new_pid}',
         'in': [{'publicationId': ONLINE_STORE_PUB}]})

    final = api('GET', f'products/{new_pid}.json')['product']
    print(f'\n{final["title"]}  /{final["handle"]}  {final["status"]}  '
          f'${final["variants"][0]["price"]} (compare ${final["variants"][0]["compare_at_price"]})')
    print(f'margin at $79 -> {margin(79.0, 8.79, 20.67) * 100:.1f}%')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
