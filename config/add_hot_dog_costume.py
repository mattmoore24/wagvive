#!/usr/bin/env python3
"""Add the Padded Hot Dog Costume (CJ CJJJCWGD00035). Owner request 2026-09-14.

WHAT IT IS, FROM THE PHOTOS, not the title. A padded tan bun dotted with tiny
cream sesame seeds that wraps around the dog's middle, a plush red sausage
along the back with one wavy yellow mustard line, and shiny green ruffled
lettuce trim down both sides. It fastens with hook and loop tape ("magic
stickers" in CJ's copy). CJ photographs it on a real Golden Retriever and a
Bichon, which is why it was the pick of the second Halloween sweep
(docs/halloween-sweep-2026-09.md): the only costume found in real large-dog
sizes, and large-dog costumes are what this store's customers actually buy.

A HYPHENATED SKU. Its variants are CJJJCWGD00035-8, CJJJCWGD00035-Size18 and
so on, under a 13 character SPU. The repo assumed `sku[:11]` everywhere, which
would have made this product "CJJJCWGD000" to the margin guard, the shipping
guard and the CJ audit. config/cj_sku.py fixes that for all of them.

SIZES, placed on size_scale.SCALE by chest girth. Maker chart (CJ description
text, repeated on CJ's product page):

    ours  CJ       bust cm    back cm   typical dog
    S     8        40 to 50   23        Shih Tzu, Pug, Westie
    M     12       61 to 80   32        Beagle, Cocker Spaniel, Frenchie
    L     14       70 to 82   39        Labrador, Golden Retriever
    XL    Size18   90 to 102  55        Great Dane, Mastiff

  * Size6 exists as a SKU but is on no chart anywhere, so it is not sold. The
    owner chose "XS only if its measurements can be confirmed"; they cannot.
  * CJ 10 and 16 land between bands already served and are retired, as the
    scale requires, so each letter is one obvious choice.

MONEY. Live LuWei Ordinary US quotes, 2026-09-14, 20% duty:

    S   $19.99   goods $6.76  freight $5.75   24.0%
    M   $20.99   goods $6.76  freight $6.46   24.0%
    L   $20.99   goods $6.76  freight $6.44   24.1%
    XL  $25.99   goods $9.56  freight $7.10   22.1%

  The lowest .99 prices that clear 20% ($18.99, $19.99, $19.99) would leave S,
  M and L at 20.1 to 20.4%, only 2 to 8 cents of freight from the floor, so an
  ordinary wobble in CJ's quote would fail the 6-hourly margin check. One step
  up gives 77 to 83 cents of headroom. XL's lowest clearing price already has
  54 cents. Sizes are priced separately because they cost differently; there
  are no colours to level.

  ONE CARRIER per CJ connection. LuWei Ordinary US is the cheapest on all four
  sizes, so it is what the pairing must select and what carriers.json records.

    python config/add_hot_dog_costume.py                    # report
    python config/add_hot_dog_costume.py --apply            # create as DRAFT
    python config/add_hot_dog_costume.py --finish --apply   # publish
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise as DP                      # noqa: E402
import cj_sku                                      # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

SHOP_LOCATION = 113363058977          # canonical; the ONLY one that can sell
FALL_COLLECTION_ID = 517682135329     # fall-halloween, MANUAL: needs a collect
LIVE_REFERENCE = 'wagvive-big-dog-costume'   # copy its channel set

HANDLE = 'wagvive-hot-dog-costume'
TITLE = 'Wagvive Hot Dog Costume'
SPU = 'CJJJCWGD00035'
CARRIER = 'LuWei Ordinary US'
FLOOR_PCT = 20.0

# (our size, CJ sku, grams, price). CJ sizes are in the docstring table.
VARIANTS = [
    ('S',  'CJJJCWGD00035-8',      120, '19.99'),
    ('M',  'CJJJCWGD00035-12',     170, '20.99'),
    ('L',  'CJJJCWGD00035-14',     210, '20.99'),
    ('XL', 'CJJJCWGD00035-Size18', 260, '25.99'),
]
OPTIONS = [('Size', ['S', 'M', 'L', 'XL'])]

BODY = (
 '<p><strong>A hot dog, with the dog included.</strong></p>'
 '<p>A padded bun wraps around your dog’s middle, with a plump sausage, a '
 'squiggle of mustard and a ruffle of lettuce running along the back. It '
 'fastens with hook and loop tape, so it goes on in seconds and there is '
 'nothing to pull over the head.</p>'
 '<ul>'
 '<li>Sizes S to XL, from a Shih Tzu to a Great Dane</li>'
 '<li>Soft padded bun with sesame dots, a plush sausage with mustard, and '
 'green lettuce trim</li>'
 '<li>Hook and loop fastening, and the head, legs and tail stay free</li>'
 '</ul>')

SEO_TITLE = 'Hot Dog Costume for Dogs, Sizes S to XL | Wagvive'
SEO_DESC = ('A padded hot dog bun costume for dogs, with a plush sausage, '
            'mustard and lettuce trim. Hook and loop fastening. Sizes S to XL, '
            'from small breeds to giant breeds.')
TAGS = 'apparel, costume, dog, fall, halloween, large breed, seasonal'


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                raw = r.read().decode()
            time.sleep(0.6)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503, 504) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {body}')
    return {}


def gql(query, variables=None):
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json',
        data=json.dumps({'query': query,
                         'variables': variables or {}}).encode(),
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=240) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.6)
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:300])
    return out


def all_products():
    # No `status` parameter: REST ignores `status=any` and returns NOTHING.
    return api('GET', 'products.json?limit=250')['products']


def by_handle(handle):
    return next((p for p in all_products() if p['handle'] == handle), None)


def cj_stock_for(skus):
    """Never read CJ stock by hand, and never treat an empty answer as zero."""
    import sync_inventory
    out = {}
    for sku in skus:
        n = None
        for attempt in range(3):
            try:
                n = sync_inventory.cj_stock(sku)
                if n is not None:
                    break
            except Exception:
                pass
            time.sleep(1.5 * (attempt + 1))
        if n is None:
            raise SystemExit(f'CJ would not report stock for {sku} after 3 '
                             f'tries. Refusing to create a product with an '
                             f'unknown quantity; re-run later.')
        out[sku] = n
    return out


def duplicate_spu():
    """Compare SPUs across the whole catalogue, any status, never titles."""
    for p in all_products():
        if p['handle'] == HANDLE:
            continue
        for v in p['variants']:
            if v.get('sku') and cj_sku.spu(v['sku']) == SPU:
                return f"{p['title']} ({p['status']})"
    return None


def build_payload():
    variants = [{
        'option1': size, 'sku': sku, 'price': price, 'grams': grams,
        'weight': grams, 'weight_unit': 'g',
        'inventory_management': 'shopify', 'inventory_policy': 'deny',
        'requires_shipping': True, 'taxable': True}
        for size, sku, grams, price in VARIANTS]
    return {'product': {
        'title': TITLE, 'handle': HANDLE,
        'body_html': BODY + DP.DELIVERY_BLOCK,
        'vendor': 'Wagvive', 'product_type': 'Apparel',
        'status': 'draft', 'tags': TAGS, 'variants': variants,
        'options': [{'name': n, 'values': v} for n, v in OPTIONS]}}


def record_books(p):
    """price_book keyed by the NUMERIC id (a handle key is silently inert), and
    carriers.json keyed by the real SPU, which is what margin_guard prices on."""
    book_path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(book_path, encoding='utf-8'))
    entry = book.setdefault(str(p['id']), {})
    entry['title'] = TITLE
    entry['variants'] = {v['sku']: float(v['price']) for v in p['variants']}
    entry['price'] = max(entry['variants'].values())
    entry['floor_margin_pct'] = FLOOR_PCT
    with open(book_path, 'w', encoding='utf-8') as fh:
        json.dump(book, fh, indent=1, ensure_ascii=False)

    car_path = os.path.join(ROOT, 'config', 'carriers.json')
    car = json.load(open(car_path, encoding='utf-8'))
    car['carriers'][SPU] = CARRIER
    with open(car_path, 'w', encoding='utf-8') as fh:
        json.dump(car, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print(f'  price_book.json: {p["id"]} floor {FLOOR_PCT}%   '
          f'carriers.json: {SPU} -> {CARRIER}')


def finish(apply):
    """Activate and publish to the same channels a live costume uses."""
    p = by_handle(HANDLE)
    if not p:
        print(f'{HANDLE} does not exist yet. Run --apply first.')
        return 1
    unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
    if unwired:
        print('REFUSING to publish, variants with no image (blank cart '
              f'thumbnail): {unwired}. Run config/apply_hot_dog_images.py '
              '--apply first.')
        return 1
    # THE SIZE GUIDE IS WRITTEN HERE, not by apply_size_guides.py --apply,
    # because that script walks ACTIVE products only and so skipped this one
    # while it was a draft, while this step refused to publish without a
    # guide: a deadlock. Its own guide_for() and insert() are used, so the
    # table is byte-for-byte the house format, and once the product is active
    # apply_size_guides.py sees it as already current.
    if 'wagvive-size-guide' not in (p.get('body_html') or ''):
        import apply_size_guides as SG
        sizes = [v['option1'] for v in p['variants']]
        body = SG.insert(p.get('body_html') or '', SG.guide_for(HANDLE, sizes))
        print(f'size guide: {sizes} from size_scale + apply_size_guides.FIT')
        if not apply:
            print('\nDry run. Use --finish --apply.')
            return 0
        api('PUT', f"products/{p['id']}.json",
            {'product': {'id': p['id'], 'body_html': body}})
        p = api('GET', f"products/{p['id']}.json")['product']
        if 'wagvive-size-guide' not in (p.get('body_html') or ''):
            raise SystemExit('size guide did not land; not publishing')
        print('  size guide written and re-read')

    ref = by_handle(LIVE_REFERENCE)
    chans = gql('''query($id: ID!) { product(id: $id) {
                     resourcePublicationsV2(first: 25) {
                       nodes { publication { id name } } } } }''',
                {'id': f"gid://shopify/Product/{ref['id']}"}
                )['data']['product']['resourcePublicationsV2']['nodes']
    # NOT TikTok. The reference costume sits on a "TikTok" publication, but the
    # owner said on 2026-09-14 to hold on TikTok, and products on that channel
    # can feed TikTok Shop listings, which docs/knowledge/tiktok-shop-us-2026-09.md
    # shows China-shipped stock may not use. Copying channels blindly would
    # have put this product there.
    kept = [n for n in chans if 'tiktok' not in n['publication']['name'].lower()]
    pubs = [{'publicationId': n['publication']['id']} for n in kept]
    print(f"channels copied from {ref['title']}: "
          f"{[n['publication']['name'] for n in kept]}  (TikTok held back)")
    if not apply:
        print('\nDry run. Use --finish --apply.')
        return 0

    api('PUT', f"products/{p['id']}.json",
        {'product': {'id': p['id'], 'status': 'active'}})
    res = gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
                   publishablePublish(id: $id, input: $input) {
                     userErrors { field message } } }''',
              {'id': f"gid://shopify/Product/{p['id']}", 'input': pubs})
    errs = res['data']['publishablePublish']['userErrors']
    if errs:
        raise SystemExit(f'publish errors: {errs}')
    print('activated and published')

    print('\n--- verify, re-fetched ---')
    fresh = api('GET', f"products/{p['id']}.json")['product']
    print(f"  status {fresh['status']}   {len(fresh['variants'])} variants   "
          f"{len(fresh['images'])} images")
    for v in fresh['variants']:
        vv = api('GET', f"variants/{v['id']}.json")['variant']
        print(f"    {vv['title']:4} ${vv['price']:>6}  {vv['sku']:22} "
              f"img={'yes' if vv.get('image_id') else 'NO'}")
    return 0


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)

    dup = duplicate_spu()
    if dup:
        print(f'REFUSING: CJ SPU {SPU} is already the source for "{dup}".')
        return 1

    print(f'{TITLE}\n  handle {HANDLE}\n  CJ {SPU} on {CARRIER}   '
          f'floor {FLOOR_PCT}%   {len(VARIANTS)} variants')
    for size, sku, grams, price in VARIANTS:
        print(f'    {size:3} {sku:22} {grams:>4} g   ${price}')

    existing = by_handle(HANDLE)
    if existing:
        print(f"\nEXISTS id={existing['id']} status={existing['status']}. "
              f'Next: images, size guide, then --finish --apply.')
        return 0
    if not apply:
        print('\nWould create as DRAFT. Use --apply.')
        return 0

    stock = cj_stock_for([v[1] for v in VARIANTS])
    print('CJ stock:', stock)
    prod = api('POST', 'products.json', build_payload())['product']
    pid = prod['id']
    print(f'\ncreated id={pid} (draft)')

    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id }
               userErrors { field message } } }''',
        {'input': {'id': f'gid://shopify/Product/{pid}', 'metafields': [
            {'namespace': 'global', 'key': 'title_tag',
             'type': 'single_line_text_field', 'value': SEO_TITLE},
            {'namespace': 'global', 'key': 'description_tag',
             'type': 'multi_line_text_field', 'value': SEO_DESC}]}})
    print('  SEO set')

    api('POST', 'collects.json',
        {'collect': {'product_id': pid, 'collection_id': FALL_COLLECTION_ID}})
    print('  added to Fall and Halloween (manual collection)')

    for v in prod['variants']:
        api('POST', 'inventory_levels/set.json',
            {'location_id': SHOP_LOCATION,
             'inventory_item_id': v['inventory_item_id'],
             'available': stock.get(v['sku'], 0)})
    print(f"  stock written for {len(prod['variants'])} variants at "
          f'Shop location only')
    record_books(prod)
    print('\nDraft created. Next: apply_hot_dog_images.py --apply, '
          'apply_size_guides.py --apply, then --finish --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
