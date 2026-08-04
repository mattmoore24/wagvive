#!/usr/bin/env python3
"""Find every place the site still quotes the old shipping rates.

Live rates are now $5.95 standard / free over $50 / $15 express. Anything that
still says $8 or $70 is a false claim to a customer.
"""
import json, os, re, sys, urllib.request

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

STALE = re.compile(r'[^<>]{0,80}(\$\s?8\b|\$\s?8\.00|\$\s?70\b|over \$?70|flat[- ]rate)'
                   r'[^<>]{0,80}', re.I)


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def scan(label, ident, text):
    hits = [m.group(0).strip() for m in STALE.finditer(text or '')]
    for h in hits:
        clean = re.sub(r'\s+', ' ', h).encode('ascii', 'replace').decode()
        print(f'  {label:9} {ident[:30]:32} {clean[:120]}')
    return len(hits)


def main():
    total = 0
    print('SHOPIFY CONTENT')
    for pg in api('pages.json?limit=250')['pages']:
        total += scan('page', pg['handle'], pg.get('body_html'))
    for p in api('products.json?limit=250&status=active')['products']:
        total += scan('product', p['handle'], p.get('body_html'))
    for c in api('custom_collections.json?limit=250')['custom_collections']:
        total += scan('collection', c['handle'], c.get('body_html'))
    for b in api('blogs.json?limit=50').get('blogs', []):
        for a in api(f'blogs/{b["id"]}/articles.json?limit=250').get('articles', []):
            total += scan('article', a['handle'], a.get('body_html'))

    print('\nTHEME FILES')
    theme = next((t for t in api('themes.json')['themes'] if t['role'] == 'main'), None)
    if theme:
        assets = api(f'themes/{theme["id"]}/assets.json')['assets']
        for a in assets:
            key = a['key']
            if not (key.endswith('.json') or key.endswith('.liquid')):
                continue
            try:
                v = api(f'themes/{theme["id"]}/assets.json'
                        f'?asset[key]={urllib.parse.quote(key)}')['asset']
            except Exception:
                continue
            total += scan('theme', key, v.get('value'))

    print(f'\n{total} stale reference(s)')


if __name__ == '__main__':
    import urllib.parse
    main()
