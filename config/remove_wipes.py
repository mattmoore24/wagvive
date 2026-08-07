#!/usr/bin/env python3
"""Remove the Dental & Ear Wipes from the store, everywhere it is referenced.

WHY. The supplier's tub carries printed typos ("Unsented", "Freshman Breath",
"Generate For Cats And Dogs") and cat photography on a dog-exclusive store. The
typos are on the REAL packaging, not our render, so they cannot be corrected
without depicting a product the customer will never receive. The owner's call was
to drop the SKU rather than sell something that signals bad quality.

ARCHIVED, NOT DELETED. Order #1001 contains this product. Deleting it would break
that order's history and is irreversible; archiving makes it unbuyable and hides
it from every channel, which is what "remove from the store" actually needs to
mean. Archiving also leaves the door open if a better-packaged equivalent turns
up under the same CJ SPU.

Five places referenced it, and missing any one leaves a broken storefront:
  1. the product record itself
  2. the Grooming collection
  3. the FAQ page, which had a "How often should I use the wipes?" entry
  4. snippets/cart-cross-sell.liquid, which named the handle in its pool
  5. CJ's pairing, which has NO API and is a browser job (see the note printed
     at the end)

    python config/remove_wipes.py            # report
    python config/remove_wipes.py --apply
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID = 10456337154337
GID = f'gid://shopify/Product/{PID}'
HANDLE = 'wagvive-ear-teeth-cleaning-wipes'
COLLECTION_ID = 516731339041          # Grooming
FAQ_PAGE_ID = 172458737953
SNIPPET = 'snippets/cart-cross-sell.liquid'

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
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read().decode()
            time.sleep(0.6)
            return json.loads(b) if b.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise
    return {}


def gql(q, v=None):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit(json.dumps(out['errors'])[:500])
    time.sleep(0.4)
    return out


def main():
    apply = '--apply' in sys.argv
    steps = []

    # ---- 1. collection membership -------------------------------------------
    collects = api('GET', f'collects.json?product_id={PID}&limit=250').get('collects', [])
    steps.append(('Grooming collection',
                  f'{len(collects)} collect(s) to delete',
                  [c['id'] for c in collects]))

    # ---- 2. FAQ entry -------------------------------------------------------
    page = api('GET', f'pages/{FAQ_PAGE_ID}.json')['page']
    body = page['body_html']
    pat = re.compile(r'\s*<h3>[^<]*wipes[^<]*</h3>\s*<p>.*?</p>', re.I | re.S)
    m = pat.search(body)
    steps.append(('FAQ page',
                  f'{"found" if m else "NOT FOUND"} the wipes Q&A '
                  f'({len(m.group(0)) if m else 0} chars)', bool(m)))

    # ---- 3. cart cross-sell pool -------------------------------------------
    q = urllib.parse.quote(SNIPPET)
    tid = next(t for t in api('GET', 'themes.json')['themes']
               if t['role'] == 'main')['id']
    src = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset']['value']
    in_pool = HANDLE in src
    steps.append((SNIPPET, 'handle present in pool' if in_pool else 'clean', in_pool))

    # ---- 4. the product -----------------------------------------------------
    prod = api('GET', f'products/{PID}.json')['product']
    steps.append(('product status', f"{prod['status']} -> ARCHIVED", True))

    print(f"Removing: {prod['title']}  ({HANDLE})\n")
    for name, detail, _ in steps:
        print(f'  {name:34} {detail}')

    if not apply:
        print('\nDry run. Use --apply to remove.')
        return 0

    print('\napplying...')

    for cid in [c['id'] for c in collects]:
        api('DELETE', f'collects/{cid}.json')
    print(f'  removed from {len(collects)} collection(s)')

    if m:
        api('PUT', f'pages/{FAQ_PAGE_ID}.json',
            {'page': {'id': FAQ_PAGE_ID, 'body_html': pat.sub('', body)}})
        print('  removed the FAQ entry')

    if in_pool:
        new = re.sub(rf',?{re.escape(HANDLE)},?', lambda mm:
                     ',' if mm.group(0).startswith(',') and mm.group(0).endswith(',')
                     else '', src)
        api('PUT', f'themes/{tid}/assets.json',
            {'asset': {'key': SNIPPET, 'value': new}})
        print('  removed the handle from the cart cross-sell pool')

    # Archive last: while it is still ACTIVE the other writes are easier to
    # reason about, and if anything above fails the product is still findable.
    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id status }
               userErrors { field message } } }''',
        {'input': {'id': GID, 'status': 'ARCHIVED'}})
    print('  archived the product')

    # ---- verify against the live system -------------------------------------
    print('\nverifying...')
    ok = True
    fresh = api('GET', f'products/{PID}.json')['product']
    print(f"  {'OK ' if fresh['status'] == 'archived' else 'BAD'} status={fresh['status']}")
    ok &= fresh['status'] == 'archived'

    left = api('GET', f'collects.json?product_id={PID}&limit=250').get('collects', [])
    print(f"  {'OK ' if not left else 'BAD'} collections: {len(left)}")
    ok &= not left

    pg = api('GET', f'pages/{FAQ_PAGE_ID}.json')['page']['body_html']
    gone = 'wipe' not in pg.lower()
    print(f"  {'OK ' if gone else 'BAD'} FAQ no longer mentions wipes")
    ok &= gone

    src2 = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset']['value']
    gone2 = HANDLE not in src2
    print(f"  {'OK ' if gone2 else 'BAD'} cross-sell pool clean")
    ok &= gone2

    for attempt in range(6):
        try:
            u = f'https://wagvive.com/products/{HANDLE}?nocache={int(time.time()*1000)}'
            urllib.request.urlopen(urllib.request.Request(
                u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60)
            code = 200
        except urllib.error.HTTPError as e:
            code = e.code
        if code == 404:
            break
        time.sleep(3 * (attempt + 1))
    print(f"  {'OK ' if code == 404 else 'BAD'} storefront returns {code} for the product page")
    ok &= code == 404

    print('\n' + ('removed and verified' if ok else 'SOMETHING IS STILL REFERENCED'))
    print('\nSTILL TO DO BY HAND: unpair the product inside CJ. CJ pairing lives in\n'
          'its Angular app and has no API. This is cosmetic now, because an\n'
          'archived product can never appear on an order for CJ to fulfil, but the\n'
          'stale mapping should be cleared next time you are in CJ.')
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
