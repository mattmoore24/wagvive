#!/usr/bin/env python3
"""Fall lineup wave 2: fix the three weak SKUs and add the launcher.

WHAT WAS WRONG WITH WAVE 1, all three confirmed against the source listings:

  * Halloween Squeaky Bones - cartoon printed bones, cheap looking. Retired.
  * Halloween Snuffle Mat - garish purple, and CJ's own copy is a template that
    calls it an "Odor pad" and lists the gift relationship as "lovers,
    classmates". Retired for a better built pumpkin mat with a non-slip base.
  * Glow Skeleton Suit - kept, because it is genuinely good, but its own CJ copy
    says "your small dog" and "your puppy's comfort". Its S to XL is SMALL BREED
    sizing. Rather than pretend otherwise the description now says so, and two
    products are added that cover the rest of the size range.

SIZE COVERAGE IS THE POINT OF THIS WAVE. The Pumpkin Hoodie runs XS to 9XL in
one SKU, and the Big Dog Costume runs 3XL to 8XL, so between them every dog from
a chihuahua to a great dane has something.

Variants are DERIVED FROM CJ at runtime rather than hardcoded. The hoodie alone
is 65 rows and hand-copying that is how a SKU ends up mapped to the wrong
colour.

    python config/add_fall_wave2.py            # report
    python config/add_fall_wave2.py --apply
    python config/add_fall_wave2.py --finish --apply
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                              # noqa: E402
import sync_inventory                                      # noqa: E402
from add_fall_lineup import (api, gql, by_handle, seasonal_collection,  # noqa: E402
                             cj_photos, SHOP_LOCATION, env)

RETIRE = ['wagvive-halloween-squeaky-bones', 'wagvive-halloween-snuffle-mat']
TAG_INTO_FALL = ['wagvive-squirrel-squeaky-plush']

SPECS = [
 {'handle': 'wagvive-ball-launcher', 'spu': 'CJCT2567740',
  'title': 'Wagvive Automatic Ball Launcher',
  'price': '94.99', 'floor': 19.6, 'type': 'Toys & Play',
  'seasonal': False,          # viral-products brief, not the fall lineup
  'tags': 'dog, fetch, interactive, toy, viral',
  'options': None,
  'seo_title': 'Automatic Dog Ball Launcher with 6 Tennis Balls',
  'seo_desc': 'Three distance settings and six balls included. Loads itself, '
              'so fetch keeps going after your arm gives up.',
  'body': """<p><strong>Fetch that outlasts your arm.</strong></p>
<p>Drop the ball in the top and it fires. Three distance settings, six tennis
balls in the box, and most dogs work out how to reload it themselves inside an
afternoon. Ships from inside the US.</p>
<ul>
<li>Three distance settings for indoors or the garden</li>
<li>Six tennis balls included</li>
<li>Runs on mains power or batteries</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-pumpkin-hoodie', 'spu': 'CJGD1828443',
  'title': 'Wagvive Pumpkin Hoodie',
  'price': '21.99', 'floor': 39.8, 'type': 'Apparel',
  'tags': 'apparel, dog, fall, halloween, hoodie, seasonal',
  'options': ['Color', 'Size'], 'split': True,
  'rename': {'Pumpkin Blue': 'Blue', 'Pumpkin Black': 'Black',
             'Pumpkin Red': 'Red', 'Pumpkin Gray': 'Grey',
             'Pumpkin Pink': 'Pink'},
  'seo_title': 'Pumpkin Dog Hoodie, XS to 9XL, Fits Every Size',
  'seo_desc': 'A fleece hoodie with a jack-o-lantern print, in thirteen sizes '
              'from XS to 9XL. Fits everything from a chihuahua to a great dane.',
  'body': """<p><strong>Thirteen sizes, so every dog gets one.</strong></p>
<p>A soft fleece hoodie with a jack-o-lantern on the back. It runs from XS all
the way to 9XL, which is the whole point: most Halloween outfits stop at the
size of a small terrier.</p>
<ul>
<li>Thirteen sizes, XS through 9XL</li>
<li>Five colours, hood that actually stays up</li>
<li>Brushed fleece inside, warm enough for an October walk</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-big-dog-costume', 'spu': 'CJGD1894831',
  'title': 'Wagvive Big Dog Costume',
  'price': '29.99', 'floor': 40.3, 'type': 'Apparel',
  'tags': 'apparel, costume, dog, fall, halloween, large breed, seasonal',
  'options': ['Design', 'Size'], 'split': True,
  'rename': {'Tiger Pet Costume': 'Tiger', 'Grey Rabbit': 'Rabbit',
             'Dinosaur': 'Dinosaur'},
  'seo_title': 'Large Dog Halloween Costume, 3XL to 8XL',
  'seo_desc': 'A hooded costume built for big dogs, 3XL to 8XL. Tiger, dinosaur '
              'or rabbit, each with ears and a tail.',
  'body': """<p><strong>Made for the big ones.</strong></p>
<p>Most dog costumes stop before your dog starts. This runs 3XL to 8XL, with a
hood, ears and a tail, and it fits a golden retriever properly rather than
stretching across the shoulders.</p>
<ul>
<li>Sizes 3XL to 8XL, built for large breeds</li>
<li>Tiger, dinosaur or rabbit, all with ears and a tail</li>
<li>Soft flannel, steps in and fastens along the back</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-pumpkin-snuffle-mat', 'spu': 'CJGY2110859',
  'title': 'Wagvive Pumpkin Snuffle Mat',
  'price': '26.99', 'floor': 35.8, 'type': 'Toys & Play',
  'tags': 'dog, enrichment, fall, halloween, puzzle, seasonal, toy',
  'options': None,
  'seo_title': 'Pumpkin Dog Snuffle Mat with Non-Slip Base',
  'seo_desc': 'Hide dinner in the fleece petals and let a thirty second inhale '
              'become ten minutes of sniffing. Non-slip backing.',
  'body': """<p><strong>Dinner they have to find.</strong></p>
<p>A pumpkin cut from thick fleece, with petals to push food down into. The base
grips the floor so it does not slide across the kitchen while they work at it,
which is the difference between a good snuffle mat and a frustrating one.</p>
<ul>
<li>Deep fleece petals to hide food in</li>
<li>Non-slip backing so it stays put</li>
<li>Machine washable</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-roast-turkey-sniff-toy', 'spu': 'CJGY1276264',
  'title': 'Wagvive Roast Turkey Sniff Toy',
  'price': '22.99', 'floor': 33.3, 'type': 'Toys & Play',
  'tags': 'dog, enrichment, fall, puzzle, seasonal, thanksgiving, toy',
  'options': None,
  'seo_title': 'Thanksgiving Roast Turkey Dog Snuffle Toy',
  'seo_desc': 'A plush roast turkey with removable vegetables to hide treats '
              'inside. Foraging that looks like Thanksgiving dinner.',
  'body': """<p><strong>Thanksgiving dinner they have to work for.</strong></p>
<p>A plush roast turkey with little vegetables that pull out. Tuck a treat into
each one, put them back, and let them nose the whole thing apart. It squeaks,
and the legs are sturdy enough for a proper tug afterwards.</p>
<ul>
<li>Removable vegetables to hide treats inside</li>
<li>Squeaks, and the legs hold up to tugging</li>
<li>Soft enough to carry around after</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},

 {'handle': 'wagvive-pumpkin-chew-toy', 'spu': 'CJGY2138215',
  'title': 'Wagvive Pumpkin Chew Toy',
  'price': '16.99', 'floor': 18.6, 'type': 'Toys & Play',
  'tags': 'chew, dog, fall, halloween, seasonal, toy',
  'options': None,
  'seo_title': 'Tough Pumpkin Dog Chew Toy for Strong Chewers',
  'seo_desc': 'A moulded pumpkin built for dogs that destroy soft toys, with '
              'ridges that work at the gums while they chew.',
  'body': """<p><strong>For the ones that finish a plush toy in a morning.</strong></p>
<p>A moulded pumpkin with deep ridges, firm enough to last a determined chewer
and textured enough to do something useful for their gums on the way.</p>
<ul>
<li>Tough moulded rubber, not stuffing</li>
<li>Ridged surface that works at the gums</li>
<li>Bounces oddly, which keeps solo play interesting</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},
]


def cj_variants(spu):
    d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
    out = []
    for v in (d.get('variants') or []):
        try:
            w = float(v.get('variantWeight') or 0)
        except (TypeError, ValueError):
            w = 0
        out.append((str(v.get('variantKey') or ''), v.get('variantSku'), w))
    return out


def build_rows(spec):
    """(option values tuple, sku, grams) derived from CJ's own variant keys."""
    rows = []
    for key, sku, w in cj_variants(spec['spu']):
        if not sku:
            continue
        if spec.get('options') is None:
            rows.append(((), sku, w))
            continue
        if spec.get('split'):
            head, _, tail = key.rpartition('-')
            head = spec.get('rename', {}).get(head.strip(), head.strip())
            rows.append(((head, tail.strip()), sku, w))
        else:
            val = spec.get('rename', {}).get(key.strip(), key.strip())
            rows.append(((val,), sku, w))
    return rows


def create_one(spec, seasonal_id):
    print(f"\n=== {spec['title']} ===")
    if by_handle(spec['handle']):
        print('  already exists, skipping')
        return
    rows = build_rows(spec)
    print(f"  {len(rows)} variant(s) derived from CJ")

    variants = []
    for opts, sku, w in rows:
        v = {'sku': sku, 'price': spec['price'], 'grams': w, 'weight': w,
             'weight_unit': 'g', 'inventory_management': 'shopify',
             'inventory_policy': 'deny', 'requires_shipping': True,
             'taxable': True}
        for i, val in enumerate(opts):
            v[f'option{i+1}'] = val
        variants.append(v)

    payload = {'product': {
        'title': spec['title'], 'handle': spec['handle'],
        'body_html': spec['body'], 'vendor': 'Wagvive',
        'product_type': spec['type'], 'status': 'draft', 'tags': spec['tags'],
        'variants': variants}}
    if spec.get('options'):
        payload['product']['options'] = [{'name': n} for n in spec['options']]
    prod = api('POST', 'products.json', payload)['product']
    pid = prod['id']
    print(f"  created draft {pid} with {len(prod['variants'])} variant(s)")

    gql('''mutation($input: ProductInput!) {
             productUpdate(input: $input) { product { id }
               userErrors { field message } } }''',
        {'input': {'id': f'gid://shopify/Product/{pid}', 'metafields': [
            {'namespace': 'global', 'key': 'title_tag',
             'type': 'single_line_text_field', 'value': spec['seo_title']},
            {'namespace': 'global', 'key': 'description_tag',
             'type': 'multi_line_text_field', 'value': spec['seo_desc']}]}})
    # `seasonal: False` opts out. The Automatic Ball Launcher belongs to the
    # separate "viral products" brief and is a year round fetch toy; it only
    # ended up in the fall collection because this used to add everything.
    if seasonal_id and spec.get('seasonal', True):
        api('POST', 'collects.json',
            {'collect': {'product_id': pid, 'collection_id': seasonal_id}})
    for i, url in enumerate(cj_photos(spec['spu'])):
        try:
            api('POST', f'products/{pid}/images.json',
                {'image': {'src': url, 'position': i + 1, 'alt': spec['title']}})
        except SystemExit as e:
            print(f'  image {i} rejected: {str(e)[:80]}')
    for v in prod['variants']:
        q = sync_inventory.cj_stock(v['sku']) or 0
        api('POST', 'inventory_levels/set.json',
            {'location_id': SHOP_LOCATION,
             'inventory_item_id': v['inventory_item_id'], 'available': q})
    print('  SEO, collection, imagery and stock done')


def retire(apply):
    """Archive the two weak SKUs. Archived, not deleted: they keep their history
    and can come back if a better photo set appears."""
    for h in RETIRE:
        p = by_handle(h)
        if not p:
            print(f'  {h}: not found')
            continue
        if p['status'] == 'archived':
            print(f'  {h}: already archived')
            continue
        print(f"  {h}: {p['status']} -> archived")
        if apply:
            api('PUT', f"products/{p['id']}.json",
                {'product': {'id': p['id'], 'status': 'archived'}})


def tag_into_fall(apply, seasonal_id):
    """Products we already sell that belong in the fall edit."""
    for h in TAG_INTO_FALL:
        p = by_handle(h)
        if not p:
            print(f'  {h}: not found')
            continue
        tags = [t.strip() for t in (p.get('tags') or '').split(',') if t.strip()]
        for t in ('fall', 'seasonal'):
            if t not in tags:
                tags.append(t)
        print(f"  {h}: tags -> {', '.join(sorted(tags))}")
        if apply:
            api('PUT', f"products/{p['id']}.json",
                {'product': {'id': p['id'], 'tags': ', '.join(sorted(tags))}})
            if seasonal_id:
                try:
                    api('POST', 'collects.json',
                        {'collect': {'product_id': p['id'],
                                     'collection_id': seasonal_id}})
                except SystemExit:
                    pass


def finish(apply):
    from add_fall_lineup import SPECS as WAVE1
    book_path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(book_path, encoding='utf-8'))
    live = by_handle('wagvive-sneaker-chew-buddy')
    chans = gql('''query($id: ID!) { product(id: $id) {
                     resourcePublicationsV2(first: 25) {
                       nodes { publication { id name } } } } }''',
                {'id': f'gid://shopify/Product/{live["id"]}'}
                )['data']['product']['resourcePublicationsV2']['nodes']
    pubs = [{'publicationId': n['publication']['id']} for n in chans]

    for spec in SPECS:
        p = by_handle(spec['handle'])
        if not p:
            print(f"  {spec['handle']}: MISSING")
            continue
        if not apply:
            print(f"  would activate {spec['handle']}")
            continue
        api('PUT', f"products/{p['id']}.json",
            {'product': {'id': p['id'], 'status': 'active'}})
        gql('''mutation($id: ID!, $input: [PublicationInput!]!) {
                 publishablePublish(id: $id, input: $input) {
                   userErrors { field message } } }''',
            {'id': f"gid://shopify/Product/{p['id']}", 'input': pubs})
        book.setdefault(spec['handle'], {})['floor_margin_pct'] = spec['floor']
        print(f"  {spec['handle']}: active + published, floor {spec['floor']}%")
    if apply:
        for h in RETIRE:
            book.pop(h, None)
        with open(book_path, 'w', encoding='utf-8') as fh:
            json.dump(book, fh, indent=1, ensure_ascii=False)
        print('price_book.json updated')
    return 0


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)
    print(f'{len(SPECS)} new products; retiring {len(RETIRE)}; '
          f'tagging {len(TAG_INTO_FALL)} existing into fall\n')
    for s in SPECS:
        n = len(build_rows(s))
        print(f"  {s['title']:38} ${s['price']:>6}  {n:>2} var  "
              f"floor {s['floor']}%  {s['spu']}")
    print('\nretiring:')
    retire(False)
    print('\ntagging into fall:')
    seasonal_id = seasonal_collection()
    tag_into_fall(False, seasonal_id)
    if not apply:
        print('\nDry run. Use --apply.')
        return 0
    seasonal_id = seasonal_collection(create=True)
    for s in SPECS:
        create_one(s, seasonal_id)
    print('\nretiring the weak SKUs...')
    retire(True)
    print('\ntagging existing products into fall...')
    tag_into_fall(True, seasonal_id)
    print('\nDone. Next: --finish --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
