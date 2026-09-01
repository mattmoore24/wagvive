#!/usr/bin/env python3
"""
Set the Domestic shipping rates to what this store should actually charge.

Product prices already absorb freight and duty at a 50% floor, so shipping
revenue is upside rather than cost recovery. That frees the threshold to do the
job it is good at - lifting average order value.

  Standard      $8.00 -> $5.95   undercuts the old rate and matches site copy
  Free over     $70   -> $50     reachable by any two-item order (entry $19) and
                                 by the $56 pad, $64 cover and both $79 kits alone
  Express       $15.00 -> removed

Express is dropped because nothing behind it delivers on the promise. A Shopify
flat rate does not choose the carrier - CJ does - so paying $15 changes no part of
fulfilment. Worse, the catalogue cannot hit an express window even in principle:
CJMY195218501AZ has exactly one carrier at 6-12 days, and the best any other item
reaches is 4-7. See config/express_check.py for the per-variant carrier lists.

The existing definitions were created with a newer API than deliveryProfileUpdate
can edit - conditionsToUpdate rejects their condition ids, and methodDefinitions-
ToUpdate refuses them outright ("uses new configurations ... use the new updated
API for associating multiple conditions"). They are therefore deleted and rebuilt.
methodDefinitionsToDelete lives on DeliveryProfileInput, not on the zone input,
and runs in the same atomic mutation as the creates, so the zone is never rateless.
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise  # noqa: E402  the single source of the delivery numbers

STANDARD = 5.95
# Raised from $50 on 2026-08-01. Two reasons. The price ladder moved up when the
# margin floor was properly costed (Slow Feeder $22->$26, Nail Grinder $34->$39,
# Water Bowl $42->$48), so $50 had started clearing on a single mid-price item -
# which spends the incentive without buying a second item. And the published
# benchmark for a threshold is 20-30% above AOV, with a $59 industry average.
#
# There is no order history yet, so this is set from the price ladder rather than
# from a measured AOV: at $60 almost no single item qualifies, while almost any
# two-item basket does. REVISIT once ~100 orders exist and a real AOV is known.
THRESHOLD = 60.00
# Delivery window quoted at checkout. Imported, never typed: this string used
# to be a literal here AND in the policies AND in 40 product bodies, and they
# drifted into two contradictory promises. It was also hyphenated, which breaks
# CLAUDE.md non-negotiable #4 (no hyphenated day ranges) on the single most
# legally-visible surface in the store.
#
# It is now a door-to-door figure that includes CJ's handling step. The old
# "5-12" was a transit-only carrier number and never covered the 4.9 to 11 day
# gap before a parcel gets its first scan.
WINDOW = delivery_promise.WINDOW

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
      id name default
      profileLocationGroups {
        locationGroup { id }
        locationGroupZones(first: 10) {
          nodes {
            zone { id name }
            methodDefinitions(first: 20) {
              nodes {
                id name active description
                rateProvider { __typename ... on DeliveryRateDefinition { id price { amount } } }
                methodConditions { id field operator
                  conditionCriteria { __typename ... on MoneyV2 { amount } } }
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
    profile { id }
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


def read_zone():
    d = gql(READ)
    if 'errors' in d:
        print(json.dumps(d['errors'])[:600]); sys.exit(1)
    prof = next(p for p in d['data']['deliveryProfiles']['nodes'] if p['default'])
    grp = prof['profileLocationGroups'][0]
    zone = grp['locationGroupZones']['nodes'][0]
    return prof['id'], grp['locationGroup']['id'], zone


def report(zone):
    for m in zone['methodDefinitions']['nodes']:
        price = ((m.get('rateProvider') or {}).get('price') or {}).get('amount')
        conds = [f'{c["field"]} {c["operator"]} '
                 f'{(c.get("conditionCriteria") or {}).get("amount")}'
                 for c in (m.get('methodConditions') or [])]
        print(f'   {m["name"]:<16} ${price:<8} active={m["active"]!s:<6} '
              f'{conds or "no condition"}')


def main():
    profile_id, lg_id, zone = read_zone()
    print(f'zone {zone["zone"]["name"]} before:')
    report(zone)

    old_ids = [m['id'] for m in zone['methodDefinitions']['nodes']]

    new_methods = [
        # Capped a cent under the threshold so the paid and free rates never both
        # appear on the same cart.
        {'name': 'Standard shipping', 'active': True,
         'description': f'{WINDOW}. Free on orders over ${THRESHOLD:.0f}.',
         'rateDefinition': {'price': {'amount': STANDARD, 'currencyCode': 'USD'}},
         'priceConditionsToCreate': [{
             'criteria': {'amount': THRESHOLD - 0.01, 'currencyCode': 'USD'},
             'operator': 'LESS_THAN_OR_EQUAL_TO'}]},
        {'name': 'Free shipping', 'active': True,
         'description': f'{WINDOW}.',
         'rateDefinition': {'price': {'amount': 0.0, 'currencyCode': 'USD'}},
         'priceConditionsToCreate': [{
             'criteria': {'amount': THRESHOLD, 'currencyCode': 'USD'},
             'operator': 'GREATER_THAN_OR_EQUAL_TO'}]},
    ]

    res = gql(UPDATE, {'id': profile_id, 'profile': {
        'methodDefinitionsToDelete': old_ids,
        'locationGroupsToUpdate': [{
            'id': lg_id,
            'zonesToUpdate': [{'id': zone['zone']['id'],
                               'methodDefinitionsToCreate': new_methods}],
        }]}})
    if res.get('errors'):
        print('\nGQL errors:', json.dumps(res['errors'])[:600]); sys.exit(1)
    errs = (res['data']['deliveryProfileUpdate'] or {}).get('userErrors')
    if errs:
        print('\nuserErrors:', json.dumps(errs)[:600]); sys.exit(1)

    _, _, zone2 = read_zone()
    print(f'\nzone {zone2["zone"]["name"]} after:')
    report(zone2)


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
