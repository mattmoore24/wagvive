#!/usr/bin/env python3
"""Correct every customer-facing "colour" to the US spelling "color".

The store sells to the United States only, so British spelling on the swatch
label of every product page reads as a foreign or careless store, which is
exactly the trust signal a new brand cannot afford.

Four surfaces carry it:

  1. 23 product OPTION NAMES ("Colour"). This is the visible one: it is the
     label above the swatches on every product page and the column header in
     the cart line item. Renamed via GraphQL productOptionUpdate with
     variantStrategy LEAVE_AS_IS, since only the label changes; no option
     VALUE contains the word, and no option has a linked metafield or swatch
     configuration that a rename could break.
  2. The FAQ page, twice, in the kit-customisation answer.
  3. The Terms of Service, once, under "Images and descriptions".
  4. One CSS comment in snippets/free-shipping-progress.liquid. Not
     customer-visible, corrected for consistency.

Bundle safety: kits reference component options by ID, not by name, so a
rename cannot orphan a component. It IS still checked afterwards, because
losing a component silently moves a kit to DRAFT and nothing warns you.

    python config/americanize_colour.py            # report
    python config/americanize_colour.py --apply    # write + verify
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = 187585560865
SNIPPET = 'snippets/free-shipping-progress.liquid'

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


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    return out


PRODUCTS_Q = '''{products(first:60,query:"status:active"){nodes{id title
  options{id name}}}}'''
OPTION_UPDATE = '''
mutation($productId: ID!, $option: OptionUpdateInput!,
         $variantStrategy: ProductOptionUpdateVariantStrategy) {
  productOptionUpdate(productId: $productId, option: $option,
                      variantStrategy: $variantStrategy) {
    product { id options { id name } }
    userErrors { field message code }
  }
}
'''
KITS_Q = '''query($q: String!) {
  products(first: 20, query: $q) {
    nodes { title status
      bundleComponents(first: 10) { nodes { componentProduct { title } } } }
  }
}'''
KITS_FILTER = "product_type:'Bundles & Kits'"


def find_targets():
    out = []
    for p in gql(PRODUCTS_Q)['data']['products']['nodes']:
        for o in p['options']:
            if 'colour' in o['name'].lower():
                out.append((p['id'], p['title'], o['id'], o['name'],
                            o['name'].replace('Colour', 'Color')
                                     .replace('colour', 'color')))
    return out


def get_asset(key):
    q = urllib.parse.urlencode({'asset[key]': key})
    return api('GET', f'themes/{THEME}/assets.json?{q}')['asset']['value']


def main():
    apply = '--apply' in sys.argv
    targets = find_targets()
    print(f'{len(targets)} product option(s) named "Colour":')
    for _, title, _, old, new in targets:
        print(f'   {title.replace("Wagvive ", "")[:40]:42} {old} -> {new}')

    pages = [p for p in api('GET', 'pages.json?limit=250')['pages']
             if 'colour' in (p.get('body_html') or '').lower()]
    print(f'\n{len(pages)} page(s):')
    for p in pages:
        n = len(re.findall(r'[Cc]olour', p['body_html']))
        print(f'   /{p["handle"]:32} {n} occurrence(s)')

    snippet = get_asset(SNIPPET)
    n_snip = len(re.findall(r'[Cc]olour', snippet))
    print(f'\ntheme snippet {SNIPPET}: {n_snip} occurrence(s)')

    print('\nTerms of Service: rewritten by config/write_policies.py '
          '(source corrected; run that script to publish)')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    print('\n--- writing ---')
    for pid, title, oid, old, new in targets:
        r = gql(OPTION_UPDATE, {'productId': pid,
                                'option': {'id': oid, 'name': new},
                                'variantStrategy': 'LEAVE_AS_IS'})
        errs = r['data']['productOptionUpdate']['userErrors']
        if errs:
            print(f'   FAILED {title}: {json.dumps(errs)[:200]}')
            return 1
        print(f'   renamed {title.replace("Wagvive ", "")[:40]}')
        time.sleep(0.55)

    for p in pages:
        body = re.sub(r'Colour', 'Color', p['body_html'])
        body = re.sub(r'colour', 'color', body)
        api('PUT', f'pages/{p["id"]}.json',
            {'page': {'id': p['id'], 'body_html': body}})
        print(f'   rewrote /{p["handle"]}')
        time.sleep(0.55)

    if n_snip:
        fixed = re.sub(r'colour', 'color', re.sub(r'Colour', 'Color', snippet))
        api('PUT', f'themes/{THEME}/assets.json',
            {'asset': {'key': SNIPPET, 'value': fixed}})
        print(f'   rewrote {SNIPPET}')

    # --- verify against the live system -----------------------------------
    print('\n--- verify ---')
    left = find_targets()
    print(f'  option names still British: {len(left)}')
    fresh_pages = [p for p in api('GET', 'pages.json?limit=250')['pages']
                   if 'colour' in (p.get('body_html') or '').lower()]
    print(f'  pages still British: {len(fresh_pages)}')

    kits = gql(KITS_Q, {'q': KITS_FILTER})['data']['products']['nodes']
    bad = [k for k in kits
           if k['status'] != 'ACTIVE' or not k['bundleComponents']['nodes']]
    for k in kits:
        n = len(k['bundleComponents']['nodes'])
        flag = 'OK ' if (k['status'] == 'ACTIVE' and n) else 'BAD'
        if k['status'] == 'ARCHIVED':
            continue
        print(f'  {flag} {k["title"]}: {k["status"]}, {n} components')

    # storefront, cache-busted, checking the label a shopper actually sees
    ok_front = False
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                f'https://wagvive.com/products/wagvive-finger-toothbrush.js'
                f'?nocache={int(time.time())}{attempt}',
                headers={'User-Agent': 'Mozilla/5.0'})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read())
            names = [o['name'] if isinstance(o, dict) else o
                     for o in d.get('options', [])]
            if all('olour' not in str(n) for n in names):
                print(f'  storefront option names: {names}')
                ok_front = True
                break
            print(f'  attempt {attempt + 1}: stale ({names})')
        except Exception as exc:
            print(f'  storefront fetch failed: {str(exc)[:60]}')
        time.sleep(12)

    return 0 if (not left and not fresh_pages and not bad and ok_front) else 1


if __name__ == '__main__':
    sys.exit(main())
