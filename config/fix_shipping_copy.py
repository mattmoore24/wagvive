#!/usr/bin/env python3
"""Bring site copy in line with the shipping rates that are now live.

Live: $5.95 standard (5-11 business days), free over $50, $15 express.
Stale copy said free over $70 with an $8.00 flat rate below that.

Touches the Shipping & Returns page, plus three theme files that hard-code the
threshold in section settings.
"""
import json, os, re, sys, urllib.parse, urllib.request, urllib.error

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

REPLACEMENTS = [
    (r'\$70\.00', '$50.00'),
    (r'\$70\b', '$50'),
    (r'\$8\.00 flat rate', '$5.95 flat rate'),
    (r'\$8\.00', '$5.95'),
    (r'\$8 flat', '$5.95 flat'),
]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def rewrite(text):
    out = text
    for pat, rep in REPLACEMENTS:
        out = re.sub(pat, rep, out)
    return out


def main():
    changed = 0

    for pg in api('GET', 'pages.json?limit=250')['pages']:
        body = pg.get('body_html') or ''
        new = rewrite(body)
        if new != body:
            api('PUT', f'pages/{pg["id"]}.json',
                {'page': {'id': pg['id'], 'body_html': new}})
            print(f'page   {pg["handle"]}  updated')
            changed += 1

    theme = next(t for t in api('GET', 'themes.json')['themes'] if t['role'] == 'main')
    for key in ('templates/index.json', 'templates/product.json',
                'locales/en.default.schema.json'):
        got = api('GET', f'themes/{theme["id"]}/assets.json'
                         f'?asset[key]={urllib.parse.quote(key)}')['asset']
        val = got.get('value') or ''
        new = rewrite(val)
        if new != val:
            api('PUT', f'themes/{theme["id"]}/assets.json',
                {'asset': {'key': key, 'value': new}})
            print(f'theme  {key}  updated')
            changed += 1

    print(f'\n{changed} file(s) rewritten')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
