#!/usr/bin/env python3
"""Point every kit component at the kit it belongs to, via a product metafield.

The kits are the strongest AOV lever in the catalogue - the Grooming kit is $109
against $136 of components, the Comfort kit $79 against $108 - and until now
nothing on a component's page said so. A shopper looking at the $39 nail grinder
had no idea it comes in a set that saves them 20%.

Uses a `custom.kit` product reference rather than hardcoding pairs in Liquid, so
the saving is computed from live prices and the mapping stays editable in admin.
Components are read from the live bundle definition, so this stays correct if a
kit is ever rebuilt.
"""
import json, os, sys, urllib.error, urllib.request

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

DEFINITION = """
mutation($def: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $def) {
    createdDefinition { id name }
    userErrors { field message code }
  }
}
"""

BUNDLES = """
{
  products(first: 50, query: "status:active") {
    nodes {
      id title handle
      variants(first: 5) {
        nodes {
          price
          productVariantComponents(first: 20) {
            nodes { productVariant { product { id title handle } } }
          }
        }
      }
    }
  }
}
"""

SET = """
mutation($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key }
    userErrors { field message }
  }
}
"""

EXISTING = """
{
  products(first: 100, query: "status:active") {
    nodes { id title metafield(namespace: "custom", key: "kit") { id } }
  }
}
"""

DELETE = """
mutation($ids: [MetafieldIdentifierInput!]!) {
  metafieldsDelete(metafields: $ids) { userErrors { message } }
}
"""


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main():
    res = gql(DEFINITION, {'def': {
        'name': 'Kit', 'namespace': 'custom', 'key': 'kit',
        'description': 'The bundle kit this product is a component of.',
        'type': 'product_reference', 'ownerType': 'PRODUCT',
        'access': {'storefront': 'PUBLIC_READ'},
    }})
    d = res.get('data', {}).get('metafieldDefinitionCreate') or {}
    errs = d.get('userErrors') or []
    if errs and all(e.get('code') == 'TAKEN' for e in errs):
        print('metafield definition custom.kit already exists')
    elif errs:
        print('definition errors:', json.dumps(errs)[:300])
    else:
        print(f'created definition {d["createdDefinition"]["name"]}')

    prods = gql(BUNDLES)['data']['products']['nodes']
    mapping = {}
    for p in prods:
        for v in p['variants']['nodes']:
            comps = v['productVariantComponents']['nodes']
            if not comps:
                continue
            for c in comps:
                cp = c['productVariant']['product']
                # A component can only sensibly point at one kit; first wins.
                mapping.setdefault(cp['id'], (cp['title'], p['id'], p['title']))

    if not mapping:
        print('no bundle components found'); return

    payload = [{'ownerId': cid, 'namespace': 'custom', 'key': 'kit',
                'type': 'product_reference', 'value': kit_id}
               for cid, (_, kit_id, _) in mapping.items()]
    out = gql(SET, {'metafields': payload})
    e = out['data']['metafieldsSet']['userErrors']
    if e:
        print('set errors:', json.dumps(e)[:300])

    # A product dropped from a kit keeps its old link and would advertise a kit
    # it is no longer part of, pointing at an archived product. Clear those.
    stale = [p for p in gql(EXISTING)['data']['products']['nodes']
             if p['metafield'] and p['id'] not in mapping]
    if stale:
        gql(DELETE, {'ids': [{'ownerId': p['id'], 'namespace': 'custom', 'key': 'kit'}
                             for p in stale]})
        for p in stale:
            print(f'   cleared stale link on {p["title"][:38]}')

    print(f'\n{len(mapping)} component(s) linked:')
    for cid, (ctitle, _, ktitle) in sorted(mapping.items(), key=lambda x: x[1][0]):
        print(f'   {ctitle[:38]:40} -> {ktitle}')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
