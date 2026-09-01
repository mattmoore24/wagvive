#!/usr/bin/env python3
"""Create the Dental Chew Stick, the replacement for the retired Dental & Ear Wipes.

WHY THIS PRODUCT. The wipes were dropped because the supplier's tub carried
printed typos and cat photography, and those were on the REAL packaging, so no
retouch could fix them without depicting something the customer never receives.
That left a dental-care hole in the Grooming collection and an empty slot in the
cart cross-sell pool.

WHY THIS SKU. CJ SPU CJGY2091358, listed by 184 CJ stores, which is the demand
proxy this repo uses and 3.3x the next dog-only dental candidate. All eleven of
CJ's own photos were pulled at ORIGINAL resolution and checked before committing:
no packaging appears at all, the toy carries no text or logo of any kind, and
every shot is of dogs. That check is what caught the wipes, and it is the reason
this SKU is safe where that one was not.

It is also deliberately NOT a liquid. CJ's liquid freight rose 57% in a month and
that is what pushed the wipes under their floor; a 140g moulded rubber toy is on
the cheap side of the freight curve.

MONEY. Cost $3.46, freight $6.04 (LuWei Ordinary US, 5 to 11 days, chosen by
freight_floor.resolve() from 27 quoted carriers), landed $10.50. At $14.99 that
is 24.9% margin and $3.73 of contribution, against the wipes' 21.6% on $13.99.
A 50% margin would need $23.02, far above market, and the flat 50% floor is
retired: no product in the catalogue carries a floor at or above 50% and the
median is 16.6%. floor_margin_pct is set to 16.9, which is the achieved 24.9%
less the 8pt drift buffer the other floors use.

    python config/add_dental_chew.py            # report
    python config/add_dental_chew.py --apply
"""
# DELIVERY PROMISE LITERAL. The canonical text lives in
# config/delivery_promise.py; the literal below is a copy because it sits
# inside plain triple-quoted HTML. If they diverge, config/audit_claims.py
# fails against the LIVE store and config/apply_delivery_promise.py repairs
# every product body in one pass.
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))

HANDLE = 'wagvive-dental-chew-stick'
TITLE = 'Wagvive Dental Chew Stick'
PRICE = '14.99'
FLOOR_PCT = 16.9
WEIGHT_G = 140.0
SPU = 'CJGY2091358'
GROOMING_ID = 516731339041          # manual collection, membership needs a collect
SHOP_LOCATION = 113363058977        # canonical; the only location that can sell

# CJ variantKey -> the colour a customer actually receives. CJ calls the teal one
# "Blue"; the barrel is cream and the accents are teal, so it is named for what
# is in the box.
VARIANTS = [
    ('Teal',   'CJGY209135802BY'),
    ('Yellow', 'CJGY209135803CX'),
    ('Green',  'CJGY209135804DW'),
]

BODY = (
    '<p><strong>A chew they choose, that cleans while they do it.</strong></p>'
    '<p>Most dental routines fail because they need your dog to hold still. '
    'This one does not ask. It is a firm rubber stick with a ridged channel down '
    'one side and cone nubs over the rest, so the work happens while they gnaw. '
    'Fill the channel with their toothpaste and the chewing does the brushing.</p>'
    '<ul>\n'
    '<li>\n<strong>Ridged center channel</strong> holds paste against the teeth '
    'as they chew</li>\n'
    '<li>\n<strong>Cone nubs</strong> reach the gum line and rub away soft '
    'plaque</li>\n'
    '<li>\n<strong>Hollow ring end</strong> gives you something to hold for '
    'tug, and them something to carry</li>\n'
    '</ul>'
    '<p>Just under 6 inches long, and firm rather than hard, so it suits '
    'determined chewers without being punishing on teeth. Rinse it under the tap '
    'when you are done. '
    'Chew toys are not indestructible: replace it once the nubs are chewed flat, '
    'and take it away if pieces come loose.</p>'
    '<p><strong>Arrives in 10 to 16 business days.</strong></p>'
)

SEO_TITLE = 'Dog Dental Chew Stick, Rubber Toothbrush Toy'
SEO_DESC = ('A firm rubber chew with a paste channel and gum line nubs, so '
            'brushing happens while your dog gnaws. 6 inches, three colors.')

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
            time.sleep(0.6)                     # REST is capped at 2 calls/second
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
        raise SystemExit(json.dumps(out['errors'])[:600])
    time.sleep(0.4)
    return out


def existing():
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] == HANDLE:
            return p
    return None


def cj_stock():
    """Delegate to sync_inventory, which is the single owner of stock numbers.

    Do NOT reimplement this. CJ returns two different row shapes: some SKUs carry
    nested per-warehouse entries with `inventory` and `factoryInventory`, and
    others carry only `totalInventoryNum` with those fields null. Summing just the
    first pair returns 0 for the second shape, which is how this script first
    created the product with zero stock on all three variants and every variant
    unbuyable. sync_inventory.cj_stock handles both.
    """
    import sync_inventory
    return {sku: sync_inventory.cj_stock(sku) for _, sku in VARIANTS}


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)

    print(f'{TITLE}   handle {HANDLE}')
    print(f'CJ SPU {SPU}   ${PRICE} on every colour   {WEIGHT_G:.0f}g')
    print(f'floor_margin_pct {FLOOR_PCT}   product type Grooming')
    print(f'tags include "toy", so the smart Toys & Play collection picks it up '
          f'as well as manual Grooming\n')
    for colour, sku in VARIANTS:
        print(f'  {colour:8} {sku}')

    already = existing()
    if already:
        print(f'\nproduct already exists: id {already["id"]} '
              f'status {already["status"]}')
    if not apply:
        print('\nDry run. Use --apply to create.')
        return 0

    if already:
        print('\nrefusing to create a second copy; delete or rename first')
        return 1

    print('\nreading CJ stock...')
    stock = cj_stock()
    for sku, q in stock.items():
        print(f'  {sku} {q}')

    # Created as DRAFT so nothing is briefly live without imagery, then flipped
    # to ACTIVE once images, variants and collection are all in place.
    print('\ncreating (draft)...')
    payload = {'product': {
        'title': TITLE, 'handle': HANDLE, 'body_html': BODY,
        'vendor': 'Wagvive', 'product_type': 'Grooming', 'status': 'draft',
        'tags': 'chew, dental, dog, grooming, teeth, toy',
        'options': [{'name': 'Color',
                     'values': [c for c, _ in VARIANTS]}],
        'variants': [{
            'option1': colour, 'sku': sku, 'price': PRICE,
            'grams': WEIGHT_G, 'weight': WEIGHT_G, 'weight_unit': 'g',
            'inventory_management': 'shopify',
            'inventory_policy': 'deny',
            'requires_shipping': True, 'taxable': True,
        } for colour, sku in VARIANTS],
    }}
    prod = api('POST', 'products.json', payload)['product']
    pid = prod['id']
    print(f'  product {pid}')

    gid = f'gid://shopify/Product/{pid}'
    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id }
               userErrors { field message } } }''',
        {'input': {'id': gid, 'metafields': [
            {'namespace': 'global', 'key': 'title_tag', 'type': 'single_line_text_field',
             'value': SEO_TITLE},
            {'namespace': 'global', 'key': 'description_tag',
             'type': 'multi_line_text_field', 'value': SEO_DESC}]}})
    print('  SEO title and description set')

    api('POST', 'collects.json',
        {'collect': {'product_id': pid, 'collection_id': GROOMING_ID}})
    print('  added to the Grooming collection')

    # Stock lives at the canonical Shop location ONLY. Anything written to the
    # legacy cjdropshipping location is inert and double-counts.
    for v in prod['variants']:
        q = stock.get(v['sku'], 0)
        api('POST', 'inventory_levels/set.json', {
            'location_id': SHOP_LOCATION,
            'inventory_item_id': v['inventory_item_id'],
            'available': q})
        print(f"  stock {v['sku']} = {q} at Shop location")

    print(f'\ncreated as DRAFT. Next: add imagery, then run --finish.')
    print(f'PRODUCT_ID={pid}')
    return 0


def finish(apply):
    """Price book, cart cross-sell slot, activation, then verify against live.

    Split from creation because imagery has to land in between: activating a
    product with no photos puts a blank card on the collection page.
    """
    import urllib.parse

    prod = existing()
    if not prod:
        print('product does not exist yet; run --apply first')
        return 1
    pid = prod['id']

    # ---- 1. price book -----------------------------------------------------
    book_path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(book_path, encoding='utf-8'))
    entry = {'title': TITLE, 'price': float(PRICE),
             'variants': {sku: float(PRICE) for _, sku in VARIANTS},
             'floor_margin_pct': FLOOR_PCT}
    in_book = str(pid) in book
    print(f'price_book.json: {"already present" if in_book else "will add"} '
          f'{pid} at ${PRICE}, floor {FLOOR_PCT}%')

    # ---- 2. cart cross-sell pool -------------------------------------------
    SNIPPET = 'snippets/cart-cross-sell.liquid'
    tid = next(t for t in api('GET', 'themes.json')['themes']
               if t['role'] == 'main')['id']
    q = urllib.parse.quote(SNIPPET)
    src = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset']['value']
    # The pool is ordered cheapest first and the snippet relies on that, so the
    # $14.99 chew goes in after the $13.99 slow feeder, which is the slot the
    # $13.99 wipes vacated.
    AFTER = 'wagvive-slow-feeder-bowl'
    already_pooled = HANDLE in src
    new_src = src if already_pooled else src.replace(
        AFTER + ',', f'{AFTER},{HANDLE},', 1)
    print(f'cross-sell pool: {"already listed" if already_pooled else "will insert after " + AFTER}')
    if not already_pooled and new_src == src:
        print(f'  !! could not find {AFTER!r} in the pool, refusing to guess')
        return 1

    print(f'status: {prod["status"]} -> active')
    print(f'images: {len(prod["images"])}   '
          f'variants wired: '
          f'{sum(1 for v in prod["variants"] if v.get("image_id"))}/{len(prod["variants"])}')

    if not apply:
        print('\nDry run. Use --finish --apply to write.')
        return 0

    if not in_book:
        book[str(pid)] = entry
        with open(book_path, 'w', encoding='utf-8') as fh:
            json.dump(book, fh, indent=2)
            fh.write('\n')
        print('  price_book.json updated')

    if not already_pooled:
        api('PUT', f'themes/{tid}/assets.json',
            {'asset': {'key': SNIPPET, 'value': new_src}})
        print('  live theme cross-sell pool updated')
        # keep the repo copy in step; it had drifted because remove_wipes.py
        # edited only the live asset
        local = os.path.join(ROOT, 'config', 'theme-work',
                             'snippets__cart-cross-sell.liquid')
        if os.path.exists(local):
            with open(local, 'w', encoding='utf-8') as fh:
                fh.write(new_src)
            print('  repo copy of the snippet re-synced from live')

    gid = f'gid://shopify/Product/{pid}'
    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id status }
               userErrors { field message } } }''',
        {'input': {'id': gid, 'status': 'ACTIVE'}})
    print('  activated')

    # Admin API creation publishes to whatever the app defaults to, which here is
    # Point of Sale ONLY. Without this the product is ACTIVE, stocked and in the
    # collection, and still 404s on the storefront. Channels are copied from a
    # product known to be live rather than hard-coded.
    PUBQ = '''query($h: String!) { productByHandle(handle: $h) {
      id resourcePublicationsV2(first: 10) {
        nodes { isPublished publication { id name } } } } }'''
    ref = gql(PUBQ, {'h': 'wagvive-sneaker-chew-buddy'})['data']['productByHandle']
    want = [n['publication']['id']
            for n in ref['resourcePublicationsV2']['nodes'] if n['isPublished']]
    mine = gql(PUBQ, {'h': HANDLE})['data']['productByHandle']
    have = {n['publication']['id']
            for n in mine['resourcePublicationsV2']['nodes'] if n['isPublished']}
    missing = [p for p in want if p not in have]
    if missing:
        gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
                 publishablePublish(id: $id, input: $input) {
                   userErrors { field message } } }''',
            {'id': gid, 'input': [{'publicationId': p} for p in missing]})
        print(f'  published to {len(missing)} more sales channel(s)')

    # ---- verify against the live system ------------------------------------
    print('\nverifying...')
    ok = True
    fresh = api('GET', f'products/{pid}.json')['product']
    print(f"  {'OK ' if fresh['status'] == 'active' else 'BAD'} status={fresh['status']}")
    ok &= fresh['status'] == 'active'

    unwired = [v['title'] for v in fresh['variants'] if not v.get('image_id')]
    print(f"  {'OK ' if not unwired else 'BAD'} every variant has an image"
          f"{'' if not unwired else ' -> ' + str(unwired)}")
    ok &= not unwired

    collects = api('GET', f'collects.json?product_id={pid}&limit=250').get('collects', [])
    in_grooming = any(c['collection_id'] == GROOMING_ID for c in collects)
    print(f"  {'OK ' if in_grooming else 'BAD'} in the Grooming collection")
    ok &= in_grooming

    src2 = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset']['value']
    pooled = HANDLE in src2
    print(f"  {'OK ' if pooled else 'BAD'} handle is in the cart cross-sell pool")
    ok &= pooled

    # storefront is the only proof that matters: admin numbers have lied before
    good, d, buyable = False, {'variants': [], 'images': [], 'price': 0}, []
    for attempt in range(8):
        try:
            u = (f'https://wagvive.com/products/{HANDLE}.js'
                 f'?nocache={int(time.time()*1000)}')
            rq = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(rq, timeout=60) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            print(f'  storefront {exc.code}, retrying')
            time.sleep(4 * (attempt + 1))
            continue
        buyable = [v for v in d['variants'] if v['available']]
        good = (d['available'] and len(buyable) == len(d['variants'])
                and len(d['images']) >= 4
                and all(v['price'] == int(float(PRICE) * 100) for v in d['variants']))
        if good:
            break
        time.sleep(4 * (attempt + 1))
    print(f"  {'OK ' if good else 'BAD'} storefront: {len(buyable)}/{len(d['variants'])} "
          f"buyable, {len(d['images'])} images, ${d['price']/100:.2f}")
    ok &= good

    print('\n' + ('launched and verified live' if ok else 'SOMETHING IS WRONG'))
    print('\nSTILL TO DO: pair this product in CJ (browser only, no API).')
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
