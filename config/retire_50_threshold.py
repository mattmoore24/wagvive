#!/usr/bin/env python3
"""Move every published mention of the free-shipping threshold from $50 to $60.

The delivery profile now grants free shipping at $60. Any surviving "$50" is a
promise the checkout will not honour, which is the exact failure mode - a cost
appearing late - that the progress bar exists to prevent.

Covers pages, theme templates/locales, product descriptions, and the shop
policies, which are rendered at checkout and in order emails.
"""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD, NEW = 50, 60

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

# Only rewrite $50 where it is the shipping threshold, never a price.
PATTERNS = [
    (re.compile(r'(over\s*)\$50\b', re.I), r'\g<1>$60'),
    (re.compile(r'(above\s*)\$50\b', re.I), r'\g<1>$60'),
    (re.compile(r'\$50\+', re.I), '$60+'),
    (re.compile(r'(free[^.<]{0,30}shipping[^.<]{0,30}?)\$50\b', re.I), r'\g<1>$60'),
    (re.compile(r'\$50(\s*(?:or more|and up))', re.I), r'$60\1'),
]


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


def rewrite(text):
    out = text or ''
    for pat, rep in PATTERNS:
        out = pat.sub(rep, out)
    return out


def main():
    changed = 0

    for pg in api('GET', 'pages.json?limit=250')['pages']:
        new = rewrite(pg.get('body_html'))
        if new != (pg.get('body_html') or ''):
            api('PUT', f'pages/{pg["id"]}.json', {'page': {'id': pg['id'], 'body_html': new}})
            print(f'page     {pg["handle"]}'); changed += 1

    for p in api('GET', 'products.json?limit=250&status=active')['products']:
        new = rewrite(p.get('body_html'))
        if new != (p.get('body_html') or ''):
            api('PUT', f'products/{p["id"]}.json',
                {'product': {'id': p['id'], 'body_html': new}})
            print(f'product  {p["handle"]}'); changed += 1

    theme = next(t for t in api('GET', 'themes.json')['themes'] if t['role'] == 'main')
    for a in api('GET', f'themes/{theme["id"]}/assets.json')['assets']:
        key = a['key']
        if not (key.endswith('.json') or key.endswith('.liquid')):
            continue
        try:
            val = api('GET', f'themes/{theme["id"]}/assets.json'
                             f'?asset[key]={urllib.parse.quote(key)}')['asset'].get('value') or ''
        except Exception:
            continue
        new = rewrite(val)
        if new != val:
            api('PUT', f'themes/{theme["id"]}/assets.json',
                {'asset': {'key': key, 'value': new}})
            print(f'theme    {key}'); changed += 1

    pols = gql('{ shop { shopPolicies { type body } } }')['data']['shop']['shopPolicies']
    for p in pols:
        new = rewrite(p['body'])
        if new != (p['body'] or ''):
            gql("""mutation($input: ShopPolicyInput!){
                     shopPolicyUpdate(shopPolicy:$input){ userErrors{ message } } }""",
                {'input': {'type': p['type'], 'body': new}})
            print(f'policy   {p["type"]}'); changed += 1

    print(f'\n{changed} item(s) updated to ${NEW}')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
