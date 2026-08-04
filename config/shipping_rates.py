#!/usr/bin/env python3
"""
Bring Shopify shipping rates in line with what the site actually promises.

Sets the rates that are best for this store rather than whatever was configured.

Product prices already absorb freight and duty at a 50% floor, so shipping revenue
is upside, not cost recovery - which means the threshold is free to do the job it
is actually good at: lifting average order value.

  Standard $5.95      undercuts the $8.00 that was configured, and is the figure
                      the site copy already advertised
  Free over $50       reachable by any two-item order (entry price is $19) and by
                      the $56 pad, the $64 cover and both $79 kits on their own.
                      $70 put it out of reach of most single-item carts.
  Express $15.00      unchanged

    python config/shipping_rates.py          # show current
    python config/shipping_rates.py --apply  # rewrite to match the promise
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STANDARD_PRICE = 5.95
FREE_THRESHOLD = 50.00
EXPRESS_PRICE = 15.00

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

READ = """
{
  deliveryProfiles(first: 3) {
    nodes {
      id
      name
      default
      profileLocationGroups {
        locationGroupZones(first: 10) {
          nodes {
            zone { id name }
            methodDefinitions(first: 10) {
              nodes {
                id
                name
                active
                rateProvider {
                  __typename
                  ... on DeliveryRateDefinition { id price { amount } }
                }
                methodConditions {
                  field
                  operator
                  conditionCriteria {
                    __typename
                    ... on MoneyV2 { amount }
                    ... on Weight { value unit }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

UPDATE = """
mutation($id: ID!, $profile: DeliveryProfileInput!) {
  deliveryProfileUpdate(id: $id, profile: $profile) {
    profile { id name }
    userErrors { field message }
  }
}
"""


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def show():
    d = gql(READ)
    if 'errors' in d:
        print(json.dumps(d['errors'], indent=1)[:800]); sys.exit(1)
    found = []
    for p in d['data']['deliveryProfiles']['nodes']:
        print(f'profile: {p["name"]}  default={p["default"]}')
        for g in p['profileLocationGroups']:
            for z in g['locationGroupZones']['nodes']:
                zone = z['zone']
                print(f'  zone {zone["name"]}  ({zone["id"].split("/")[-1]})')
                for m in z['methodDefinitions']['nodes']:
                    rp = m.get('rateProvider') or {}
                    price = (rp.get('price') or {}).get('amount')
                    conds = []
                    for c in (m.get('methodConditions') or []):
                        cc = c.get('conditionCriteria') or {}
                        conds.append(f'{c["field"]} {c["operator"]} '
                                     f'{cc.get("amount") or cc.get("value")}')
                    print(f'     {m["name"]:<12} ${price:<8} active={m["active"]!s:<6} '
                          f'cond={conds or "none"}')
                    found.append({
                        'profile_id': p['id'], 'zone_id': zone['id'],
                        'method_id': m['id'], 'name': m['name'], 'price': price,
                        'conditions': conds,
                    })
    return found


def apply(found):
    """Delete the existing definitions and recreate them to match the promise."""
    if not found:
        print('nothing to change'); return
    profile_id = found[0]['profile_id']
    zone_id = found[0]['zone_id']

    to_delete = [m['method_id'] for m in found]
    new_methods = [
        # Capped a cent below the threshold so the paid and free rates never both
        # show on the same cart.
        {'name': 'Standard', 'active': True,
         'description': f'Free on orders over ${FREE_THRESHOLD:.0f}',
         'rateDefinition': {'price': {'amount': STANDARD_PRICE, 'currencyCode': 'USD'}},
         'conditions': [{'criteria': {'unit': 'USD', 'value': FREE_THRESHOLD - 0.01},
                         'field': 'TOTAL_PRICE', 'operator': 'LESS_THAN_OR_EQUAL_TO'}]},
        {'name': 'Free shipping', 'active': True,
         'description': f'On orders over ${FREE_THRESHOLD:.0f}',
         'rateDefinition': {'price': {'amount': 0.0, 'currencyCode': 'USD'}},
         'conditions': [{'criteria': {'unit': 'USD', 'value': FREE_THRESHOLD},
                         'field': 'TOTAL_PRICE', 'operator': 'GREATER_THAN_OR_EQUAL_TO'}]},
        {'name': 'Express', 'active': True,
         'description': 'Priority handling',
         'rateDefinition': {'price': {'amount': EXPRESS_PRICE, 'currencyCode': 'USD'}}},
    ]

    payload = {'locationGroupsToUpdate': [{
        'id': None, 'zonesToUpdate': [{
            'id': zone_id,
            'methodDefinitionsToCreate': new_methods,
            'methodDefinitionsToDelete': to_delete,
        }],
    }]}
    # locationGroup id is required; fetch it
    d = gql(READ)
    lg = None
    for p in d['data']['deliveryProfiles']['nodes']:
        if p['id'] == profile_id:
            # locationGroup id isn't in the trimmed query, so query it directly
            break
    q = """
    query($id: ID!) {
      deliveryProfile(id: $id) {
        profileLocationGroups { locationGroup { id } }
      }
    }
    """
    lgd = gql(q, {'id': profile_id})
    lg = lgd['data']['deliveryProfile']['profileLocationGroups'][0]['locationGroup']['id']
    payload['locationGroupsToUpdate'][0]['id'] = lg

    res = gql(UPDATE, {'id': profile_id, 'profile': payload})
    errs = (res.get('data', {}).get('deliveryProfileUpdate') or {}).get('userErrors')
    if res.get('errors'):
        print('GQL errors:', json.dumps(res['errors'])[:500]); sys.exit(1)
    if errs:
        print('userErrors:', json.dumps(errs)[:500]); sys.exit(1)
    print('rates rewritten\n')
    show()


if __name__ == '__main__':
    current = show()
    if '--apply' in sys.argv:
        print()
        apply(current)
