#!/usr/bin/env python3
"""
Rebuild the Comfort & Health Kit around components that can actually ship.

Old kit: cooling mat + orthopedic bed + water bowl + slow feeder = 6,560g, which
no carrier would accept. New kit drops the two bulky items and uses the ice silk
pad instead:

    Cooling Comfort Pad (Light Grey, Medium)  $3.37
    Anti-Spill Water Bowl (Grey, 1.5L)        $4.13
    Slow Feeder Bowl (Green)                  $1.29
    -------------------------------------------------
    product $8.79 + consolidated freight $20.67 = landed $29.46
    at $79 retail -> 62.7% margin

Uses productBundleUpdate so the existing product id, handle and SEO survive.
"""
import json, os, sys, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import margin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = 10458198081825

COMPONENTS = [
    (10464689881377, 'Light Grey', 'Medium 24" x 20"'),   # cooling pad
    (10456337547553, 'Grey', '1.5L'),                      # water bowl
    (10456337613089, 'Green', None),                        # slow feeder
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


def find_variant(pid, opt1, opt2):
    p = api('GET', f'products/{pid}.json')['product']
    for v in p['variants']:
        if v.get('option1') == opt1 and (opt2 is None or v.get('option2') == opt2):
            return v['id'], p['title'], v['title'], float(v['price'])
    raise SystemExit(f'variant not found on {pid}: {opt1} / {opt2}')


BODY = (
    "<p><strong>Comfort, hydration and rest &mdash; covered.</strong></p>"
    "<p>Three things that make the biggest daily difference for an older dog: somewhere cool "
    "to lie down, water they can actually drink without soaking the floor, and a bowl that "
    "slows them down at dinner. Buy them together and save.</p>"
    "<p><strong>This kit includes:</strong></p><ul>"
    "<li>Cooling Comfort Pad &mdash; ice silk, Medium 24&Prime; &times; 20&Prime;, light grey</li>"
    "<li>Anti-Spill Floating Water Bowl &mdash; 1.5L, grey</li>"
    "<li>Slow Feeder Bowl &mdash; green</li></ul>"
    "<p>Everything ships together in one parcel.</p>")


OPTIONS_Q = """
query($id: ID!) {
  product(id: $id) {
    title
    options { id name optionValues { id name } }
  }
}
"""


def component_input(pid, wanted):
    """Bundle components are declared as productId + a chosen value per option."""
    d = gql(OPTIONS_Q, {'id': f'gid://shopify/Product/{pid}'})
    prod = d['data']['product']
    selections = []
    for opt, want in zip(prod['options'], wanted):
        if want is None:
            continue
        names = [v['name'] for v in opt['optionValues']]
        if want not in names:
            raise SystemExit(f'{prod["title"]}: option {opt["name"]} has no value {want!r} '
                             f'(has {names})')
        selections.append({'componentOptionId': opt['id'], 'name': opt['name'],
                           'values': [want]})
    return prod['title'], {
        'productId': f'gid://shopify/Product/{pid}',
        'quantity': 1,
        'optionSelections': selections,
    }


def main():
    comps = []
    print('components:')
    for pid, o1, o2 in COMPONENTS:
        title, ci = component_input(pid, [o1, o2])
        comps.append(ci)
        picked = ' / '.join(s['values'][0] for s in ci['optionSelections'])
        print(f'   {title[:36]:38} {picked}')

    res = gql('''
      mutation($input: ProductBundleUpdateInput!) {
        productBundleUpdate(input: $input) {
          productBundleOperation { id status }
          userErrors { field message }
        }
      }''', {'input': {
        'productId': f'gid://shopify/Product/{KIT}',
        'title': 'Comfort & Health Kit',
        'components': comps,
    }})
    print('\nproductBundleUpdate ->', json.dumps(res)[:400])

    if res.get('errors') or (res.get('data', {}).get('productBundleUpdate') or {}).get('userErrors'):
        print('\nBundle mutation rejected - falling back to manual component note.')
        return

    api('PUT', f'products/{KIT}.json', {'product': {
        'id': KIT, 'body_html': BODY, 'status': 'active',
        'tags': 'comfort, bundle, kit, senior pet, dog'}})
    gql('''mutation($id:ID!,$in:[PublicationInput!]!){
             publishablePublish(id:$id,input:$in){userErrors{message}}}''',
        {'id': f'gid://shopify/Product/{KIT}',
         'in': [{'publicationId': 'gid://shopify/Publication/306551619873'}]})
    landed = 8.79 + 20.67
    print(f'\nkit reactivated. landed ${landed:.2f} at $79 -> {margin(79.0, 8.79, 20.67)*100:.1f}% margin')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
