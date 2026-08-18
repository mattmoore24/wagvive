#!/usr/bin/env python3
"""Put the fall edit on the homepage, directly under "Start with a kit".

Built by CLONING the existing kit band rather than authoring a new section from
scratch. Horizon's section JSON carries dozens of presentation settings and a
hand-written block silently renders wrong; copying the shape that already works
and changing only the heading, the copy and the collection is the safe edit.

Writes a timestamped backup of templates/index.json to config/theme-backup/
before it touches anything, because a bad homepage is the most visible possible
failure.

    python config/add_fall_homepage.py            # show the plan
    python config/add_fall_homepage.py --apply
"""
import copy
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
D, T, V = (env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'],
           env['SHOPIFY_API_VERSION'])
COLLECTION = 'fall-halloween'
HEAD = '<h2>Dressed for fall</h2>'
SUB = ('<p>Costumes that fit every size, treat-hiding toys and coats for '
       'Halloween and Thanksgiving. Order by 10 October to have it in time.</p>')


def api(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(f'https://{D}/admin/api/{V}/{path}', data=data,
                                 method=method,
                                 headers={'X-Shopify-Access-Token': T,
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read().decode()
    time.sleep(0.6)
    return json.loads(raw) if raw.strip() else {}


def main():
    apply = '--apply' in sys.argv
    theme = [t for t in api('themes.json')['themes'] if t['role'] == 'main'][0]
    key = urllib.parse.quote('templates/index.json')
    raw = api(f"themes/{theme['id']}/assets.json?asset[key]={key}"
              )['asset']['value']
    d = json.loads(raw)

    if 'fall_head' in d['sections']:
        print('fall section already present')
        return 0
    for need in ('bundle_head', 'bundle_products'):
        if need not in d['sections']:
            print(f'{need} missing; homepage shape changed, not editing blindly')
            return 1

    head = copy.deepcopy(d['sections']['bundle_head'])
    head['blocks']['h']['settings']['text'] = HEAD
    head['blocks']['p']['settings']['text'] = SUB

    plist = copy.deepcopy(d['sections']['bundle_products'])
    # Horizon's product-list takes a BARE HANDLE ("bundles-kits"), not a
    # "collections/..." path and not a gid. Writing a path here renders an empty
    # band that still looks like a real section, which is the worst outcome.
    if 'collection' not in plist.get('settings', {}):
        print('product-list has no `collection` setting; shape changed, stopping')
        return 1
    plist['settings']['collection'] = COLLECTION
    plist['settings']['max_products'] = 8
    plist['settings']['columns'] = 4
    changed = ['collection -> ' + COLLECTION, 'max_products -> 8',
               'columns -> 4']

    d['sections']['fall_head'] = head
    d['sections']['fall_products'] = plist
    order = d['order']
    order.insert(order.index('bundle_products') + 1, 'fall_head')
    order.insert(order.index('fall_head') + 1, 'fall_products')

    print(f"collection setting(s) rewritten: {changed}")
    print('new order:')
    for s in order:
        mark = '  <== NEW' if s.startswith('fall_') else ''
        print(f"  {s}{mark}")
    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    bdir = os.path.join(ROOT, 'config', 'theme-backup')
    os.makedirs(bdir, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    with open(os.path.join(bdir, f'index.json.{stamp}.bak'), 'w',
              encoding='utf-8') as fh:
        fh.write(raw)
    print(f'backup -> config/theme-backup/index.json.{stamp}.bak')

    api(f"themes/{theme['id']}/assets.json", 'PUT',
        {'asset': {'key': 'templates/index.json',
                   'value': json.dumps(d, ensure_ascii=False, indent=1)}})
    print('written')

    # verify against the rendered storefront, not the write's return value
    for attempt in range(6):
        time.sleep(6)
        url = f"https://wagvive.com/?nocache={int(time.time()*1000)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
        if 'Dressed for fall' in html:
            i = html.index('Dressed for fall')
            after = html[i:i + 6000]
            # Ball Launcher was in this list and should never have been: it is
            # a year round fetch toy from the viral-products brief that got
            # swept into the seasonal collection, and it was taking one of the
            # eight slots this row has. See fix_fall_membership.py.
            names = [n for n in ('Pumpkin Hoodie', 'Skeleton Suit', 'Big Dog',
                                 'Turkey', 'Jack-o-Lantern', 'Snuffle')
                     if n in after]
            print(f'LIVE: heading rendered, fall products visible after it: {names}')
            return 0
        print(f'  attempt {attempt+1}: not rendered yet (CDN)')
    print('heading did not appear; check the theme editor')
    return 1


if __name__ == '__main__':
    sys.exit(main())
