#!/usr/bin/env python3
"""Deploy the kit callout and the cart cross-sell.

  * kit-callout   -> product page, immediately under the buy buttons. High enough
                     to be seen without scrolling, but below the add-to-cart so it
                     offers an upgrade rather than competing with the primary action.
  * cart-cross-sell -> under the line items in the drawer, and on the cart page.

The product template is JSON, so the callout goes in as a `custom-liquid` block
inside the existing product-details group. Idempotent: both the block id and the
render markers are checked before anything is written, and every touched file is
backed up first.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'config', 'theme-work')
BACKUP = os.path.join(ROOT, 'config', 'theme-backup')
BLOCK_ID = 'wv_kit_callout'
XSELL_MARKER = 'wv-cart-cross-sell'

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


def upload(tid, name):
    with open(os.path.join(WORK, f'snippets__{name}.liquid'), encoding='utf-8') as fh:
        put_asset(tid, f'snippets/{name}.liquid', fh.read())
    print(f'uploaded snippets/{name}.liquid')


def main():
    tid = theme_id()
    upload(tid, 'kit-callout')
    upload(tid, 'cart-cross-sell')

    # --- product page: custom-liquid block under buy-buttons ---
    key = 'templates/product.json'
    raw = get_asset(tid, key)
    tpl = json.loads(raw)
    details = tpl['sections']['main']['blocks']['product-details']
    blocks = details.setdefault('blocks', {})
    if BLOCK_ID in blocks:
        print('kit callout block already present')
    else:
        backup(key, raw)
        blocks[BLOCK_ID] = {
            'type': 'custom-liquid',
            'name': 'Kit callout',
            'settings': {'custom_liquid': "{% render 'kit-callout' %}"},
        }
        order = details.get('block_order')
        if order is None:
            # Horizon keeps ordering by key insertion when block_order is absent;
            # rebuild the dict so the callout lands right after the buy buttons.
            keys = list(blocks.keys())
            keys.remove(BLOCK_ID)
            if 'buy-buttons' in keys:
                keys.insert(keys.index('buy-buttons') + 1, BLOCK_ID)
            else:
                keys.append(BLOCK_ID)
            details['blocks'] = {k: blocks[k] for k in keys}
        else:
            if 'buy-buttons' in order:
                order.insert(order.index('buy-buttons') + 1, BLOCK_ID)
            else:
                order.append(BLOCK_ID)
        put_asset(tid, key, json.dumps(tpl, indent=2))
        print('added kit callout to product page')

    # --- cart drawer: cross-sell under the items ---
    key = 'snippets/cart-drawer.liquid'
    src = get_asset(tid, key)
    if XSELL_MARKER in src:
        print('cart drawer cross-sell already wired')
    else:
        backup(key, src)
        anchor = '<div class="cart-drawer__summary">'
        if anchor not in src:
            print('!! drawer summary anchor not found - skipped')
        else:
            inject = ('{% comment %}' + XSELL_MARKER + '{% endcomment %}\n'
                      "                {% render 'cart-cross-sell', context: 'drawer' %}\n\n"
                      '                ' + anchor)
            put_asset(tid, key, src.replace(anchor, inject, 1))
            print('wired cart drawer cross-sell')

    # --- cart page: cross-sell under the summary ---
    key = 'snippets/cart-summary.liquid'
    src = get_asset(tid, key)
    if XSELL_MARKER in src:
        print('cart summary cross-sell already wired')
    else:
        backup(key, src)
        line = ('\n{% comment %}' + XSELL_MARKER + '{% endcomment %}\n'
                "{% if template.name == 'cart' %}"
                "{% render 'cart-cross-sell', context: 'page' %}"
                '{% endif %}\n')
        put_asset(tid, key, src + line)
        print('wired cart page cross-sell')

    print('\ndone. backups in config/theme-backup/')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
