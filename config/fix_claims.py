#!/usr/bin/env python3
"""
Align every storefront claim with what is actually true.

  "One vetted supplier"        -> false: sourcing now spans CJ in-house, Manifest
                                  Store LLC and others. Replaced with a claim that
                                  is true and still says something.
  "Free ... over $60" / "$50"  -> live rate is free over $70
  "$5.95 flat"                 -> live rate is $8.00
  "5-11 business days"         -> the slicker brush's fastest carrier is 6-12, so
                                  5-12 is the honest range
"""
import json, os, re, sys, urllib.request, urllib.error

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
THEME = 187585560865

# ordered: longest / most specific first
EDITS = [
    ('One vetted supplier', 'Every product hand-picked'),
    ('Free US shipping over $60', 'Free US shipping over $70'),
    ('Free shipping over $50', 'Free shipping over $70'),
    ('Free standard shipping on orders over $60', 'Free standard shipping on orders over $70'),
    ('Free over $60, otherwise $5.95 flat', 'Free over $70, otherwise $8.00 flat'),
    ('$5.95 flat rate below that', '$8.00 flat rate below that'),
    ('free shipping over $60', 'free shipping over $70'),
    ('over $60', 'over $70'),
    ('$5.95', '$8.00'),
    # The three 5-11 -> 5-12 rewrites that used to live here are GONE. Both
    # numbers are retired (config/delivery_promise.RETIRED) and this script
    # would have re-stamped "5-12" over the current promise wherever it ran.
    # Delivery wording is now owned by config/apply_delivery_promise.py.
]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def apply_edits(text):
    changed = []
    for old, new in EDITS:
        if old in text:
            n = text.count(old)
            text = text.replace(old, new)
            changed.append(f'{old!r} -> {new!r} x{n}')
    return text, changed


def fix_pages():
    for p in api('GET', 'pages.json?limit=50')['pages']:
        body = p.get('body_html') or ''
        new, changed = apply_edits(body)
        if not changed:
            continue
        api('PUT', f'pages/{p["id"]}.json', {'page': {'id': p['id'], 'body_html': new}})
        print(f'page /{p["handle"]}')
        for c in changed:
            print(f'    {c}')


def fix_theme():
    for key in ('templates/index.json', 'templates/product.json',
                'locales/en.default.schema.json', 'locales/en.default.json'):
        try:
            asset = api('GET', f'themes/{THEME}/assets.json?asset[key]={key}')['asset']
        except urllib.error.HTTPError:
            continue
        value = asset.get('value')
        if not value:
            continue
        new, changed = apply_edits(value)
        if not changed:
            continue
        api('PUT', f'themes/{THEME}/assets.json', {'asset': {'key': key, 'value': new}})
        print(f'theme {key}')
        for c in changed:
            print(f'    {c}')


if __name__ == '__main__':
    try:
        fix_pages()
        fix_theme()
        print('\ndone')
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
