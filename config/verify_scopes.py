#!/usr/bin/env python3
"""
Check a Shopify Admin API token against everything the Wagvive automation needs.

Usage:
    python config/verify_scopes.py                 # checks the token in config/shopify.env
    python config/verify_scopes.py shpat_xxxxx     # checks a token you paste in

Prints the granted scopes, what is still missing, and live probes of the
endpoints each outstanding task depends on. Nothing is written or changed.
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What each pending task actually needs.
NEEDED = {
    'variants + stock sync': [
        'read_products', 'write_products',
        'read_inventory', 'write_inventory',
        'read_locations',
    ],
    'order routing + fulfilment': [
        'read_orders', 'write_orders',
        'read_fulfillments', 'write_fulfillments',
        'read_assigned_fulfillment_orders', 'write_assigned_fulfillment_orders',
        'read_merchant_managed_fulfillment_orders', 'write_merchant_managed_fulfillment_orders',
        'read_third_party_fulfillment_orders', 'write_third_party_fulfillment_orders',
        'read_draft_orders', 'write_draft_orders',
    ],
    'shipping rates + margin rule': [
        'read_shipping', 'write_shipping',
        'read_markets', 'write_markets',
        'read_price_rules', 'write_price_rules',
        'read_discounts', 'write_discounts',
    ],
    'order testing + reporting': [
        'read_customers',
        'read_returns',
    ],
}

# Nice to have: not every store can grant these to a custom app.
OPTIONAL = ['read_all_orders', 'read_shopify_payments_payouts',
            'read_shopify_payments_disputes', 'read_reports']

PROBES = [
    ('locations',            'GET',  'locations.json'),
    ('inventory_items',      'GET',  'inventory_items.json?ids=1'),
    ('orders',               'GET',  'orders.json?limit=1&status=any'),
    ('price_rules',          'GET',  'price_rules.json?limit=1'),
    ('customers',            'GET',  'customers.json?limit=1'),
    ('carrier_services',     'GET',  'carrier_services.json'),
]
GQL_PROBES = [
    ('deliveryProfiles', '{deliveryProfiles(first:1){nodes{id}}}'),
    ('markets',          '{markets(first:1){nodes{id}}}'),
]


def env():
    e = {}
    with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                e[k] = v
    return e


def main():
    e = env()
    domain, version = e['SHOPIFY_STORE_DOMAIN'], e['SHOPIFY_API_VERSION']
    token = sys.argv[1] if len(sys.argv) > 1 else e['SHOPIFY_ADMIN_API_TOKEN']
    hdr = {'X-Shopify-Access-Token': token}

    req = urllib.request.Request(f'https://{domain}/admin/oauth/access_scopes.json', headers=hdr)
    try:
        granted = {s['handle'] for s in
                   json.loads(urllib.request.urlopen(req, timeout=45).read().decode())['access_scopes']}
    except urllib.error.HTTPError as exc:
        print(f'Could not read scopes: HTTP {exc.code}. Is the token valid?')
        sys.exit(1)

    print(f'Token grants {len(granted)} scopes on {domain}\n')

    missing_total = []
    for task, scopes in NEEDED.items():
        missing = [s for s in scopes if s not in granted]
        missing_total += missing
        state = 'READY' if not missing else f'MISSING {len(missing)}'
        print(f'[{state:>10}]  {task}')
        for s in missing:
            print(f'               - {s}')

    opt_missing = [s for s in OPTIONAL if s not in granted]
    if opt_missing:
        print('\nOptional, not granted (fine to skip):')
        for s in opt_missing:
            print(f'  - {s}')

    print('\nLive endpoint probes:')
    for label, _m, path in PROBES:
        r = urllib.request.Request(f'https://{domain}/admin/api/{version}/{path}', headers=hdr)
        try:
            urllib.request.urlopen(r, timeout=45)
            print(f'  {label:<20} OK')
        except urllib.error.HTTPError as exc:
            print(f'  {label:<20} HTTP {exc.code}')

    for label, q in GQL_PROBES:
        r = urllib.request.Request(
            f'https://{domain}/admin/api/{version}/graphql.json',
            data=json.dumps({'query': q}).encode(), method='POST',
            headers={**hdr, 'Content-Type': 'application/json'})
        try:
            d = json.loads(urllib.request.urlopen(r, timeout=45).read().decode())
            print(f'  {label:<20} {"DENIED" if "errors" in d else "OK"}')
        except urllib.error.HTTPError as exc:
            print(f'  {label:<20} HTTP {exc.code}')

    print()
    if missing_total:
        print(f'RESULT: not ready - {len(set(missing_total))} required scopes still missing.')
        sys.exit(2)
    print('RESULT: ready - every required scope is granted.')


if __name__ == '__main__':
    main()
