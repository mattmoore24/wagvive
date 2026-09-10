#!/usr/bin/env python3
"""Replace the DELISTED Calming Thunder Wrap with a hooded calming vest.

WHY. CJ answers `code 1602002, "Product has been removed from shelves"` for
CJYD2640786, the Calming Thunder Wrap's SPU. That is not an empty answer that
wants retrying (see the "EMPTY ANSWER" rule in CLAUDE.md) - it is a definitive
negative. The product is unbuyable at source while still active on the
storefront and still a component of all nine Calm & Comfort Kit variants, so it
is the same failure mode as order #1002: a shopper can buy something nobody can
ship.

THE REPLACEMENT IS A DIFFERENT GARMENT, AND IS NAMED HONESTLY. The old item was
not a vest at all: its own copy says "a soft dimpled wrap ... 81 x 61cm", and
its photos are a folded minky BLANKET. Searching CJ on the product NAME turned
up jackets and vests, none of which was the same category - the same trap the
imagery rules warn about. So this is a deliberate category change, and it keeps
the old item's JOB (gentle pressure for storms and fireworks) rather than its
shape. Calling a hooded vest a "wrap" would be a small untruth of exactly the
kind the delivery-promise work removed, so the title changes with the product.

CJPC2963124, "Dog Anxiety Vest With Hood". Sleeveless compression vest, black
binding at the hem and leg openings, two black hook-and-loop straps under the
belly, a reflective strip on each flank, and a tall snood that pulls up over
the ears or scrunches down as a neck warmer. Verified from the CJ gallery, not
from the title.

SIZING. CJ publishes a full chart (chest, back, neck AND weight for 7 sizes) but
hides it in a GALLERY image, not the description and not the API - so the first
sweep of this product reported "no measurements published", which was wrong.
docs/knowledge/cj-size-charts.md said to look inside description <img> tags;
`productImageSet` is a second hiding place and is now recorded there too.

Mapped onto the canonical XS to XL scale on CHEST GIRTH, cross-checked against
weight, which is what size_scale.py requires:

    ours  supplier  garment chest    supplier weight   real breeds at that band
    XS    CJ XS     33 to 43 cm      7 to 11 lb        Chihuahua, Yorkie, Pom
    S     CJ M      45 to 54 cm      17 to 24 lb       Shih Tzu, Pug, Westie
    M     CJ XL     56 to 68 cm      29 to 44 lb       Beagle, Cocker, Frenchie
    L     CJ XXXL   78 to 90 cm      66 to 88 lb       Labrador, Golden, GSD
    XL    -         NOT OFFERED

  * CJ S, L and XXL are retired: each lands in a band already served, and the
    whole point of the scale is that a letter is one obvious choice.
  * Where a band spans two supplier sizes the LARGER is taken, because both
    CJ's chart and our own guides tell a shopper to size up when between two.
  * There is NO XL. CJ's biggest size stops at 88 lb and a 35 in chest, which
    is the top of our L, not the bottom of our XL. Offering XL anyway would
    break the one promise the scale makes - that a letter means the same dog
    everywhere - and would sell a Great Dane owner a vest for a labrador. The
    size guide says so in plain words instead.

MONEY. Goods $4.52 (XS) to $6.73 (L), real CN freight $5.05 to $6.84 quoted per
variant (NOT $0.00, so no missing-data trap here), duty 20%.

    $20.99  worst variant 22.3% (L), best 44.1% (XS)

That is the 20% floor plus the 2 point buffer every other product in the store
now carries. $19.99 puts L at 18.5%, under floor, so $20.99 is the lowest
.99 price that holds the floor on every variant.

    python config/replace_thunder_wrap.py                  # report
    python config/replace_thunder_wrap.py --apply           # create as DRAFT
    python config/replace_thunder_wrap.py --finish --apply  # publish + retire old
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
COMFORT_HEALTH_ID = 516731371809      # manual collection, needs a collect
LIVE_REFERENCE = 'wagvive-quick-dry-bath-robe'   # copy its channel set

OLD_HANDLE = 'wagvive-calming-thunder-wrap'
HANDLE = 'wagvive-calming-hooded-anxiety-vest'
TITLE = 'Wagvive Calming Hooded Anxiety Vest'
SPU = 'CJPC2963124'
PRICE = '20.99'
FLOOR_PCT = 20.0

# (our size, colour) -> (CJ sku, grams). CJ letters are in the docstring table.
VARIANTS = [
    ('Dark Blue', 'XS', 'CJPC296312401AZ', 68),
    ('Dark Blue', 'S',  'CJPC296312403CX', 101),
    ('Dark Blue', 'M',  'CJPC296312405EV', 145),
    ('Dark Blue', 'L',  'CJPC296312407GT', 197),
    ('Dark Grey', 'XS', 'CJPC296312408HS', 68),
    ('Dark Grey', 'S',  'CJPC296312410JQ', 101),
    ('Dark Grey', 'M',  'CJPC296312412LO', 145),
    ('Dark Grey', 'L',  'CJPC296312414NM', 197),
]
OPTIONS = [('Color', ['Dark Blue', 'Dark Grey']), ('Size', ['XS', 'S', 'M', 'L'])]

BODY = (
 '<p><strong>Gentle pressure and a hood that covers the ears, for dogs who '
 'hide from the noise.</strong></p>'
 '<p>It works the way a weighted blanket does. The vest holds light, even '
 'pressure across the chest and back, and a wide adjustable strap under the '
 'belly keeps it snug without pinching. The hood pulls up over the ears to '
 'take the edge off thunder and fireworks, and scrunches down into a soft '
 'neck warmer when your dog would rather just wear the vest.</p>'
 '<ul>'
 '<li><strong>Even, all over pressure</strong> for storms, fireworks, travel '
 'days, vet visits and time alone</li>'
 '<li><strong>Ear covering hood</strong> that folds down, so it is two things '
 'in one</li>'
 '<li><strong>Breathable knit</strong>, light enough to wear indoors without '
 'overheating</li>'
 '<li><strong>Reflective strip on each side</strong> for evening walks</li>'
 '<li><strong>Adjustable belly strap</strong> and an open belly, so nothing '
 'presses where it should not</li>'
 '<li><strong>Machine washable</strong></li>'
 '</ul>'
 '<p>No medicine and nothing to charge. Put it on before the storm arrives '
 'rather than once your dog is already frightened.</p>')

SEO_TITLE = 'Dog Anxiety Vest with Hood, Calming Thunder Jacket | Wagvive'
SEO_DESC = ('A calming compression vest with an ear covering hood, for '
            'thunderstorms, fireworks, travel and time alone. Breathable '
            'knit, adjustable belly strap, reflective strips. Sizes XS to L.')
TAGS = 'anxiety, calming, comfort, dog'


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
            if e.code in (429, 500, 502, 503) and a < tries - 1:
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
    return out


def by_handle(handle):
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] == handle:
            return p
    return None


def cj_stock_for(skus):
    """Never read CJ stock by hand, and never treat an empty answer as zero.

    Both rules are in CLAUDE.md and both were learned by publishing products
    with every variant unbuyable. Retry, then refuse rather than guess.
    """
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
    """A duplicate CJ source slipped through once because the audit compared
    TITLES. Compare sku[:11] across the whole catalogue instead."""
    for p in api('GET', 'products.json?limit=250')['products']:
        if p['handle'] in (HANDLE, OLD_HANDLE):
            continue
        for v in p['variants']:
            if (v.get('sku') or '')[:11] == SPU:
                return p['title']
    return None


def build_payload():
    variants = []
    for colour, size, sku, grams in VARIANTS:
        variants.append({
            'option1': colour, 'option2': size, 'sku': sku,
            'price': PRICE, 'grams': grams,
            'weight': grams, 'weight_unit': 'g',
            'inventory_management': 'shopify',
            'inventory_policy': 'deny',
            'requires_shipping': True, 'taxable': True})
    return {'product': {
        'title': TITLE, 'handle': HANDLE,
        'body_html': BODY + DP.DELIVERY_BLOCK,
        'vendor': 'Wagvive', 'product_type': 'Comfort & Health',
        'status': 'draft', 'tags': TAGS, 'variants': variants,
        'options': [{'name': n, 'values': v} for n, v in OPTIONS]}}


def finish(apply):
    """Activate, publish to the same channels a known-live product uses, retire
    the delisted product, and record the new one in the price book."""
    p = by_handle(HANDLE)
    if not p:
        print(f'{HANDLE} does not exist yet. Run --apply first.')
        return 1

    unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
    if unwired:
        print('REFUSING to publish: these variants have no image wired, so the '
              'colour swatch would not swap the photo and the cart thumbnail '
              'would be blank:')
        for t in unwired:
            print('   ! ' + t)
        print('Run config/apply_wrap_images.py --apply first.')
        return 1

    ref = by_handle(LIVE_REFERENCE)
    chans = gql('''query($id: ID!) { product(id: $id) {
                     resourcePublicationsV2(first: 25) {
                       nodes { publication { id name } } } } }''',
                {'id': f"gid://shopify/Product/{ref['id']}"}
                )['data']['product']['resourcePublicationsV2']['nodes']
    pubs = [{'publicationId': n['publication']['id']} for n in chans]
    print(f"channels copied from {ref['title']}: "
          f"{[n['publication']['name'] for n in chans]}")

    old = by_handle(OLD_HANDLE)
    print(f"\nwould activate {TITLE}")
    print(f"would archive  {old['title'] if old else OLD_HANDLE} "
          f"({old['status'] if old else 'missing'})")
    if not apply:
        print('\nDry run. Use --finish --apply.')
        return 0

    api('PUT', f"products/{p['id']}.json",
        {'product': {'id': p['id'], 'status': 'active'}})
    gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
             publishablePublish(id: $id, input: $input) {
               userErrors { field message } } }''',
        {'id': f"gid://shopify/Product/{p['id']}", 'input': pubs})
    print('activated and published')

    # Archived, not deleted: it keeps its order history, and CJ could relist.
    if old and old['status'] != 'archived':
        api('PUT', f"products/{old['id']}.json",
            {'product': {'id': old['id'], 'status': 'archived'}})
        print(f"archived {old['title']}")

    # price_book is keyed by the NUMERIC product id. A handle-keyed entry never
    # matches margin_guard's str(product['id']) lookup and is silently inert.
    book_path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(book_path, encoding='utf-8'))
    if old:
        book.pop(str(old['id']), None)
    entry = book.setdefault(str(p['id']), {})
    entry['title'] = TITLE
    entry['floor_margin_pct'] = FLOOR_PCT
    entry['variants'] = {v['sku']: float(v['price']) for v in p['variants']}
    entry['price'] = max(entry['variants'].values())
    with open(book_path, 'w', encoding='utf-8') as fh:
        json.dump(book, fh, indent=1, ensure_ascii=False)
    print(f"price_book.json: added {p['id']}, dropped the old entry")

    print('\n--- verify, re-fetched ---')
    fresh = api('GET', f"products/{p['id']}.json")['product']
    print(f"  status {fresh['status']}   {len(fresh['variants'])} variants   "
          f"{len(fresh['images'])} images")
    for v in fresh['variants']:
        print(f"    {v['title']:16} ${v['price']:>6}  {v['sku']:18} "
              f"img={'yes' if v.get('image_id') else 'NO'}")
    return 0


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)

    dup = duplicate_spu()
    if dup:
        print(f'REFUSING: CJ SPU {SPU} is already the source for "{dup}".')
        return 1

    print(f'{TITLE}\n  handle {HANDLE}\n  CJ {SPU}   ${PRICE}   '
          f'floor {FLOOR_PCT}%   {len(VARIANTS)} variants')
    for colour, size, sku, grams in VARIANTS:
        print(f'    {colour:10} {size:3} {sku:18} {grams:>4} g')

    existing = by_handle(HANDLE)
    if existing:
        print(f"\nEXISTS id={existing['id']} status={existing['status']}")
        if not apply:
            return 0
    old = by_handle(OLD_HANDLE)
    print(f"\nreplacing: {old['title'] if old else 'MISSING'} "
          f"({old['status'] if old else '-'}, "
          f"{len(old['variants']) if old else 0} variants)")

    if not apply:
        print('\nWould create as DRAFT. Use --apply.')
        return 0
    if existing:
        print('Already created. Next: imagery, then --finish --apply.')
        return 0

    stock = cj_stock_for([v[2] for v in VARIANTS])
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
        {'collect': {'product_id': pid, 'collection_id': COMFORT_HEALTH_ID}})
    print('  added to Comfort & Health (manual collection needs the collect; '
          'Calming & Enrichment is smart and picks up the "calming" tag)')

    for v in prod['variants']:
        api('POST', 'inventory_levels/set.json',
            {'location_id': SHOP_LOCATION,
             'inventory_item_id': v['inventory_item_id'],
             'available': stock.get(v['sku'], 0)})
    print(f"  stock written for {len(prod['variants'])} variants at "
          f'Shop location only')
    print('\nDraft created. Next: imagery, then --finish --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
