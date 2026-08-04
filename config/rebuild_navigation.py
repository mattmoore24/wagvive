#!/usr/bin/env python3
"""Rebuild Wagvive main + footer navigation via the GraphQL Admin API."""
import json, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'], env['SHOPIFY_API_VERSION']

COLL = lambda i: f'gid://shopify/Collection/{i}'
PAGE = lambda i: f'gid://shopify/Page/{i}'

C_GROOMING, C_COMFORT, C_BUNDLES = 516731339041, 516731371809, 516867031329
P_ABOUT, P_CONTACT, P_CREATORS = 172410732833, 172409782561, 172410765601
P_PRIVACY, P_SHIPPING, P_FAQ = 172409815329, 172458705185, 172458737953

MAIN_MENU_ID = 'gid://shopify/Menu/314006995233'
FOOTER_MENU_ID = 'gid://shopify/Menu/314007028001'

MUTATION = """
mutation menuUpdate($id: ID!, $title: String!, $handle: String!, $items: [MenuItemUpdateInput!]!) {
  menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
    menu { id handle items { title items { title } } }
    userErrors { field message }
  }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json',
        data=json.dumps({'query': query, 'variables': variables}).encode(),
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


main_items = [
    {'title': 'Shop', 'type': 'CATALOG', 'items': [
        {'title': 'Grooming', 'type': 'COLLECTION', 'resourceId': COLL(C_GROOMING)},
        {'title': 'Comfort & Health', 'type': 'COLLECTION', 'resourceId': COLL(C_COMFORT)},
        {'title': 'Bundles & Kits', 'type': 'COLLECTION', 'resourceId': COLL(C_BUNDLES)},
    ]},
    {'title': 'Bundles & Kits', 'type': 'COLLECTION', 'resourceId': COLL(C_BUNDLES), 'items': []},
    {'title': 'About', 'type': 'PAGE', 'resourceId': PAGE(P_ABOUT), 'items': []},
    {'title': 'FAQ', 'type': 'PAGE', 'resourceId': PAGE(P_FAQ), 'items': []},
]

footer_items = [
    {'title': 'Shop All', 'type': 'CATALOG', 'items': []},
    {'title': 'Grooming', 'type': 'COLLECTION', 'resourceId': COLL(C_GROOMING), 'items': []},
    {'title': 'Comfort & Health', 'type': 'COLLECTION', 'resourceId': COLL(C_COMFORT), 'items': []},
    {'title': 'Shipping & Returns', 'type': 'PAGE', 'resourceId': PAGE(P_SHIPPING), 'items': []},
    {'title': 'FAQ', 'type': 'PAGE', 'resourceId': PAGE(P_FAQ), 'items': []},
    {'title': 'Contact', 'type': 'PAGE', 'resourceId': PAGE(P_CONTACT), 'items': []},
    {'title': 'About', 'type': 'PAGE', 'resourceId': PAGE(P_ABOUT), 'items': []},
    {'title': 'Creator Program', 'type': 'PAGE', 'resourceId': PAGE(P_CREATORS), 'items': []},
    {'title': 'Your Privacy Choices', 'type': 'PAGE', 'resourceId': PAGE(P_PRIVACY), 'items': []},
]

for label, mid, handle, title, items in [
    ('MAIN', MAIN_MENU_ID, 'main-menu', 'Main menu', main_items),
    ('FOOTER', FOOTER_MENU_ID, 'footer', 'Footer menu', footer_items),
]:
    res = gql(MUTATION, {'id': mid, 'title': title, 'handle': handle, 'items': items})
    if 'errors' in res:
        print(f'{label}: GraphQL errors ->', json.dumps(res['errors'])[:400])
        continue
    payload = res['data']['menuUpdate']
    if payload['userErrors']:
        print(f'{label}: userErrors ->', payload['userErrors'])
        continue
    print(f'{label} menu rebuilt:')
    for it in payload['menu']['items']:
        print(f"   - {it['title']}")
        for s in it['items']:
            print(f"       * {s['title']}")
