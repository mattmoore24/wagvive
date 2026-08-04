#!/usr/bin/env python3
"""
Shopify OAuth: build the authorize link, then trade the returned code for a token.

Step 1 - print the link to open in the browser:
    python config/oauth_exchange.py link <client_id>

Step 2 - after approving, paste back the full redirect URL:
    python config/oauth_exchange.py token <client_id> <client_secret> "<redirect_url>"

On success the new token is written to config/shopify.env (the previous one is
kept as SHOPIFY_ADMIN_API_TOKEN_PREVIOUS so nothing is lost if we need to roll back).
The token itself is never printed - only the scope list it came back with.
"""
import os, sys, json, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, 'config', 'shopify.env')

REDIRECT_URI = 'https://example.com'

SCOPES = ','.join([
    'read_products', 'write_products',
    'read_inventory', 'write_inventory',
    'read_locations',
    'read_orders', 'write_orders',
    'read_fulfillments', 'write_fulfillments',
    'read_assigned_fulfillment_orders', 'write_assigned_fulfillment_orders',
    'read_merchant_managed_fulfillment_orders', 'write_merchant_managed_fulfillment_orders',
    'read_third_party_fulfillment_orders', 'write_third_party_fulfillment_orders',
    'read_draft_orders', 'write_draft_orders',
    'read_returns', 'write_returns',
    'read_shipping', 'write_shipping',
    'read_markets', 'write_markets',
    'read_price_rules', 'write_price_rules',
    'read_discounts', 'write_discounts',
    'read_customers', 'write_customers',
    'read_files', 'write_files',
    'read_online_store_navigation', 'write_online_store_navigation',
    'read_publications', 'write_publications',
    'read_content', 'write_content',
    'read_themes', 'write_themes', 'write_theme_code',
    'read_reports',
])


def read_env():
    e = {}
    with open(ENV, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                e[k] = v
    return e


def write_token(new_token):
    e = read_env()
    old = e.get('SHOPIFY_ADMIN_API_TOKEN', '')
    e['SHOPIFY_ADMIN_API_TOKEN_PREVIOUS'] = old
    e['SHOPIFY_ADMIN_API_TOKEN'] = new_token
    with open(ENV, 'w', encoding='utf-8') as fh:
        for k, v in e.items():
            fh.write(f'{k}={v}\n')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode, client_id = sys.argv[1], sys.argv[2]
    shop = read_env()['SHOPIFY_STORE_DOMAIN']

    if mode == 'link':
        q = urllib.parse.urlencode({
            'client_id': client_id,
            'scope': SCOPES,
            'redirect_uri': REDIRECT_URI,
            'state': 'wagvive-scope-upgrade',
        })
        print(f'https://{shop}/admin/oauth/authorize?{q}')
        print(f'\n({len(SCOPES.split(","))} scopes requested)')
        return

    if mode == 'token':
        client_secret, redirect_url = sys.argv[3], sys.argv[4]
        code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query).get('code', [None])[0]
        if not code:
            print('No ?code= found in that URL. Paste the full address bar contents '
                  'after approving, including everything after the "?".')
            sys.exit(1)

        body = urllib.parse.urlencode({
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        }).encode()
        req = urllib.request.Request(
            f'https://{shop}/admin/oauth/access_token', data=body, method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            res = json.loads(urllib.request.urlopen(req, timeout=45).read().decode())
        except urllib.error.HTTPError as exc:
            print(f'Exchange failed: HTTP {exc.code}')
            print(exc.read().decode()[:400])
            sys.exit(1)

        token = res.get('access_token')
        if not token:
            print('No access_token in response:', json.dumps(res)[:300])
            sys.exit(1)

        write_token(token)
        granted = res.get('scope', '').split(',')
        print(f'Token saved to config/shopify.env  (prefix {token[:6]}..., {len(token)} chars)')
        print(f'Granted {len(granted)} scopes.')
        missing = [s for s in SCOPES.split(',') if s not in granted]
        if missing:
            print('Requested but NOT granted:')
            for s in missing:
                print('  -', s)
        else:
            print('Every requested scope was granted.')
        return

    print(__doc__)
    sys.exit(1)


if __name__ == '__main__':
    main()
