#!/usr/bin/env python3
"""Second Halloween sourcing sweep (2026-09-14), on CJ's listV2 search.

WHY A SECOND SWEEP, AND WHY IT CAN BE WIDER THAN THE FIRST. The 2026-08-18
sweep (`scout_fall.py`) walked 27 categories through `/product/list`, which has
no working keyword search and no sort, so it saw whatever CJ listed first.
`/product/listV2` does both: `keyWord` is a real search and `orderBy=1,
sort=desc` sorts by `listedNum`, the number of other stores that list the
product, which is the best demand signal CJ exposes. It also returns 100 rows a
page and stock and warehouse fields the old endpoint lacked.

COST. listV2 costs 50 CJ points a call (measured 2026-09-14 from the response's
own `pointsInfo`), against a daily budget of about 58,900 that the 6-hourly job
also draws on. This sweep makes roughly 150 calls, about 7,500 points. The
remaining balance is printed at the end. A quota wall raises
`cj_api.CJQuotaExhausted` and the partial result is still saved.

WHAT COUNTS AS A CANDIDATE. Halloween themed by name, meant for a dog (a
"dog cat costume" is fine, a cat-only one is not), not something a PERSON wears
or hangs on a porch, and not an SPU the catalogue already uses, active or
archived. Everything else is judged later, by eye and by live freight.

NOTE the old `scout.REJECT` pattern drops any title containing "rabbit", which
would throw away bunny COSTUMES for dogs. Not reused here for that reason.

Scan only. Writes config/scout_halloween_results.json. Creates nothing and
buys nothing.

    python config/scout_halloween.py            # 3 pages per keyword
    python config/scout_halloween.py 2          # cheaper
    python config/scout_halloween.py --refilter # re-filter the saved sweep, no CJ calls
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api  # noqa: E402

OUT = os.path.join(ROOT, 'config', 'scout_halloween_results.json')

KEYWORDS = [
    # costumes, by the shapes that sell
    'halloween dog costume', 'dog costume', 'funny dog costume',
    'large dog costume', 'small dog halloween costume', 'dog cosplay',
    'dog pumpkin costume', 'dog skeleton costume', 'glow in the dark dog',
    'dog witch costume', 'dog witch hat', 'dog vampire cape', 'dog cape',
    'dog bat wings', 'pet bat wings', 'dog devil horns', 'dog ghost costume',
    'dog spider costume', 'dog dinosaur costume', 'dog shark costume',
    'dog lion mane', 'dog hot dog costume', 'dog pirate costume',
    'dog wizard costume', 'dog bee costume', 'dog superhero costume',
    'dog rider costume', 'dog cowboy costume', 'dog clown costume',
    # wearables that are not full costumes
    'halloween dog bandana', 'halloween dog collar', 'halloween dog bow tie',
    'halloween dog hat', 'halloween dog sweater', 'halloween dog hoodie',
    'halloween dog pajamas', 'halloween dog shirt',
    # toys and treats
    'halloween dog toy', 'halloween squeaky toy', 'pumpkin dog toy',
    'halloween plush dog toy', 'halloween chew toy', 'halloween snuffle',
    'halloween treat dog', 'dog treat bucket', 'halloween dog bed',
]

# Pet categories searched with keyWord="halloween", which catches listings that
# never say "dog" in the title. IDs from /product/getCategory, 2026-09-14.
CATEGORIES = {
    'Pet Clothings':        '2410110349471606300',
    'Pet Clothing Sets':    '2410110350161600700',
    'Pet Jumpsuits':        '2410110349201623700',
    'Pet Tops':             '2410110348271614500',
    'Pet Sweaters':         '2410110348401611500',
    'Pet Hoodies':          '2410110348531624100',
    'Pet Pajamas':          '2410110349341618600',
    'Pet Coats & Jackets':  '2410110349061619800',
    'Pet Dresses':          '2410110348131619300',
    'Pet Scarves':          '2410110350591620800',
    'Pet Bows & Ties':      '2410110351401621300',
    'Pet Headwears':        '2410110352051607900',
    'Pet Hair Accessories': '2410110351231616600',
    'Pet Collars':          '2410110352331629800',
    'Pet Glasses':          '2410110352191611200',
    'Pet Chew Toys':        '2410110339451623300',
    'Pet Sound Toys':       '2410110340161623400',
    'Pet Plush Toys':       '2410110340531618900',
    'Pet Toy Set':          '2410110340411608400',
    'Pet Feeding Tools':    '2410110341451628800',
    'Pet Beds':             '2410110358051626100',
    'Pet Blankets & Quilts': '2410110358191601900',
}

# FIRST RUN LESSON (2026-09-14). This pattern once also matched "luminous",
# "glow in the dark", "dinosaur", "shark" and "hot dog" on their own, and the
# candidate test never required the product to be FOR A DOG. The kept list came
# back led by a dinosaur night light, LED collars, shark slippers, handbags and
# a hot-dog roasting machine, and the costing stage started spending CJ points
# on them. Now a theme word only counts when it is actually Halloween, and a
# candidate must name a dog or pet or sit in CJ's Pet Supplies tree.
HALLOWEEN = re.compile(
    r'hallowe?en|costume|cosplay|dress.?up|skeleton|skull|ghost|witch|'
    r'vampire|dracula|\bbats?\b|bat.?wing|spider|devil|mummy|zombie|'
    r'pumpkin|jack.?o|candy.?corn|spooky|trick.?or.?treat|\bboo\b|'
    r'\bcape\b|cloak|wizard|pirate|transform',
    re.I)
CHRISTMAS = re.compile(r'christmas|xmas|santa|\belf\b|reindeer|snowman', re.I)
DOG = re.compile(r'\bdogs?\b|pupp(y|ies)|\bpets?\b|canine|doggy|doggie', re.I)
NOT_DOG = re.compile(r'\bcats?\b|kitten|\bbird|parrot|\bfish|aquarium|hamster|'
                     r'reptile|guinea|chinchilla|ferret|hedgehog', re.I)
# Things a PERSON wears or a house displays, which the "dog" keyword drags in.
HUMAN = re.compile(
    r'\b(women|womens|men|mens|adults?|kids|child(ren)?|girls?|boys?|baby|'
    r'toddler|parent)\b|house flag|garden flag|throw pillow|pillow ?case|'
    r'decorations?\b|\bporch\b|\byard\b|\bwall\b|\bmug\b|\bsocks for|'
    r'latex|head ?mask|\bmask\b|inflatable|\bsign\b|ornament|sticker|'
    r'blanket for (men|women)|t-?shirt for|keychain|earrings|necklace for',
    re.I)


def existing_spus():
    """Every SPU the catalogue uses, ANY status. Archived counts: the Halloween
    Squeaky Bones and first Snuffle Mat were archived for being poor, and
    re-proposing them would repeat a decision already made."""
    env = {}
    with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k] = v
    # NO `status` parameter. REST products.json does not accept `status=any`
    # (that is GraphQL's vocabulary): it silently returns ZERO products, and the
    # first run of this sweep reported "0 SPUs already in the catalogue". Left
    # off, it returns every status, which is what the duplicate check needs.
    url = (f"https://{env['SHOPIFY_STORE_DOMAIN']}/admin/api/"
           f"{env['SHOPIFY_API_VERSION']}/products.json?limit=250"
           f"&fields=id,title,status,variants")
    req = urllib.request.Request(url, headers={
        'X-Shopify-Access-Token': env['SHOPIFY_ADMIN_API_TOKEN']})
    with urllib.request.urlopen(req, timeout=120) as r:
        prods = json.loads(r.read().decode())['products']
    out = {}
    for p in prods:
        for v in p['variants']:
            if v.get('sku'):
                out[v['sku'][:11]] = f"{p['title']} ({p['status']})"
    return out


def num(x, default=0.0):
    try:
        return float(str(x).split('--')[0].split('-')[0].strip())
    except (TypeError, ValueError):
        return default


def search(params, pages):
    """Yield product rows for one query, best-listed first."""
    for pg in range(1, pages + 1):
        r = cj_api.call('/product/listV2', {**params, 'page': pg, 'size': 100,
                                            'orderBy': 1, 'sort': 'desc'})
        if not r.get('result'):
            yield ('error', r)
            return
        d = r.get('data') or {}
        lst = ((d.get('content') or [{}])[0] or {}).get('productList') or []
        for p in lst:
            yield ('row', p)
        SEARCH_POINTS.append((r.get('pointsInfo') or {}))
        if len(lst) < 100 or pg >= (d.get('totalPages') or 0):
            return


SEARCH_POINTS = []


def main():
    if '--refilter' in sys.argv:
        return refilter()
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    have = existing_spus()
    print(f'{len(have)} SPUs already in the catalogue (any status)')

    seen, errors, queries = {}, [], []
    plan = ([(f'kw:{k}', {'keyWord': k}) for k in KEYWORDS] +
            [(f'cat:{n}', {'keyWord': 'halloween', 'categoryId': c})
             for n, c in CATEGORIES.items()])
    try:
        for label, params in plan:
            n = 0
            for kind, p in search(params, pages if label.startswith('kw') else 2):
                if kind == 'error':
                    errors.append((label, str(p)[:200]))
                    break
                n += 1
                spu = p.get('sku')
                if not spu:
                    continue
                row = seen.setdefault(spu, {
                    'spu': spu, 'name': str(p.get('nameEn') or ''),
                    'listed': int(p.get('listedNum') or 0),
                    'price_from': num(p.get('sellPrice'), 999.0),
                    'price_text': str(p.get('sellPrice')),
                    'warehouse_inventory': p.get('warehouseInventoryNum'),
                    'verified_inventory': p.get('totalVerifiedInventory'),
                    'verified_warehouse': p.get('verifiedWarehouse'),
                    'delivery_cycle': p.get('deliveryCycle'),
                    'category': ' > '.join(x for x in (
                        p.get('oneCategoryName'), p.get('twoCategoryName'),
                        p.get('threeCategoryName')) if x),
                    'variant_keys': p.get('variantKeyEn'),
                    'image': p.get('bigImage'),
                    'supplier': p.get('supplierName'),
                    'created': p.get('createAt'),
                    'found_by': [],
                })
                if label not in row['found_by']:
                    row['found_by'].append(label)
            queries.append((label, n))
            print(f'  {label:36} {n:>4} rows   running unique {len(seen)}')
    except cj_api.CJQuotaExhausted as exc:
        errors.append(('QUOTA', str(exc)))
        print(f'\nSTOPPED: CJ points quota exhausted. Partial result saved. {exc}')

    kept, dropped = select(seen.values(), have)
    pts = SEARCH_POINTS[-1] if SEARCH_POINTS else {}
    report_and_save(kept, dropped, len(seen), queries, errors, pages, pts)
    return 2 if errors and not kept else 0


def select(rows, have):
    """(kept, dropped counts). Kept rows are Halloween, for a dog, not worn by a
    person or hung on a house, and not an SPU the catalogue already uses."""
    kept = []
    dropped = {'already_ours': 0, 'not_halloween': 0, 'christmas_only': 0,
               'not_for_dogs': 0, 'not_a_pet_product': 0, 'human_or_decor': 0}
    for row in rows:
        name = row['name']
        petcat = str(row.get('category') or '').startswith('Pet')
        if row['spu'][:11] in have:
            dropped['already_ours'] += 1
            continue
        if not HALLOWEEN.search(name):
            dropped['not_halloween'] += 1
            continue
        if CHRISTMAS.search(name) and not re.search(r'hallowe?en', name, re.I):
            dropped['christmas_only'] += 1
            continue
        if NOT_DOG.search(name) and not DOG.search(name):
            dropped['not_for_dogs'] += 1
            continue
        if not (DOG.search(name) or petcat):
            dropped['not_a_pet_product'] += 1
            continue
        if HUMAN.search(name):
            dropped['human_or_decor'] += 1
            continue
        kept.append(row)
    kept.sort(key=lambda r: -r['listed'])
    return kept, dropped


def report_and_save(kept, dropped, n_seen, queries, errors, pages, pts):
    print(f'\n{n_seen} unique products seen across {len(queries)} queries; '
          f'{len(kept)} candidates kept. Dropped: {dropped}')
    if errors:
        print(f'{len(errors)} query error(s): {errors[:5]}')
    for r in kept[:60]:
        print(f"  {r['listed']:>6} lists  ${r['price_from']:>6.2f}  {r['spu']:14} "
              f"{r['name'][:72]}")
    print(f'\nCJ points after sweep: {json.dumps(pts)}')
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump({'swept': '2026-09-14', 'pages_per_keyword': pages,
                   'queries': queries, 'errors': errors, 'dropped': dropped,
                   'n_seen': n_seen, 'points_after': pts, 'candidates': kept},
                  fh, ensure_ascii=False, indent=1)
    print(f'saved -> {OUT}')


def refilter():
    """Re-apply select() to a saved sweep with NO CJ calls. Valid because the
    saved list is what an older, looser filter kept, and select() only ever
    narrows."""
    data = json.load(open(OUT, encoding='utf-8'))
    have = existing_spus()
    print(f'{len(have)} SPUs already in the catalogue (any status)')
    kept, dropped = select(data['candidates'], have)
    report_and_save(kept, dropped, data.get('n_seen', len(data['candidates'])),
                    data['queries'], data['errors'], data['pages_per_keyword'],
                    data.get('points_after'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
