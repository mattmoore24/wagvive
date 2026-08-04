#!/usr/bin/env python3
"""Deploy the conversion/AOV changes to the live theme.

1. Uploads snippets/free-shipping-progress.liquid.
2. Renders it at the top of the cart drawer, above the line items, so the
   shipping position is stated before the shopper starts scrolling - not at the
   bottom next to the total where it reads as a cost rather than a goal.
3. Renders it on the cart page too, via the cart summary block.

Every edit is idempotent: the marker comment is checked first, so re-running does
not duplicate the render tag. Theme files are backed up to config/theme-backup
before being touched.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'config', 'theme-work')
BACKUP = os.path.join(ROOT, 'config', 'theme-backup')
MARKER = 'wv-free-shipping-progress'

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


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def theme_id():
    return next(t for t in api('GET', 'themes.json')['themes'] if t['role'] == 'main')['id']


def get_asset(tid, key):
    q = urllib.parse.quote(key)
    return api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset'].get('value') or ''


def put_asset(tid, key, value):
    return api('PUT', f'themes/{tid}/assets.json', {'asset': {'key': key, 'value': value}})


def backup(key, value):
    os.makedirs(BACKUP, exist_ok=True)
    with open(os.path.join(BACKUP, key.replace('/', '__')), 'w', encoding='utf-8') as fh:
        fh.write(value)


def main():
    tid = theme_id()

    # 1. the snippet itself
    with open(os.path.join(WORK, 'snippets__free-shipping-progress.liquid'),
              encoding='utf-8') as fh:
        snippet = fh.read()
    put_asset(tid, 'snippets/free-shipping-progress.liquid', snippet)
    print('uploaded snippets/free-shipping-progress.liquid')

    # 2. cart drawer - above the scrollable item list
    key = 'snippets/cart-drawer.liquid'
    src = get_asset(tid, key)
    if MARKER in src:
        print('cart drawer already wired')
    else:
        backup(key, src)
        anchor = '<scroll-hint class="cart-drawer__items">'
        if anchor not in src:
            print('!! cart drawer anchor not found - skipped')
        else:
            inject = ('{% comment %}' + MARKER + '{% endcomment %}\n'
                      "                {% render 'free-shipping-progress', context: 'drawer' %}\n\n"
                      '                ' + anchor)
            put_asset(tid, key, src.replace(anchor, inject, 1))
            print('wired cart drawer')

    # 3. cart page - top of the summary column
    key = 'snippets/cart-summary.liquid'
    src = get_asset(tid, key)
    if MARKER in src:
        print('cart summary already wired')
    else:
        backup(key, src)
        # cart-summary is rendered by BOTH the drawer and the cart page, and the
        # drawer does not pass an is_drawer flag - so gate on the template name
        # instead, or the drawer shows the bar twice. cart-drawer.liquid only
        # renders when template.name != 'cart', which makes this unambiguous.
        marker_line = ('{% comment %}' + MARKER + '{% endcomment %}\n'
                       "{% if template.name == 'cart' %}"
                       "{% render 'free-shipping-progress', context: 'page' %}"
                       '{% endif %}\n')
        put_asset(tid, key, marker_line + src)
        print('wired cart summary (cart page only)')

    print('\ndone. backups in config/theme-backup/')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
