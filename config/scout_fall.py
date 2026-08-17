#!/usr/bin/env python3
"""Sourcing sweep for the fall/Halloween/Thanksgiving lineup, plus viral devices.

TWO BRIEFS, deliberately kept in one sweep because they share the scan cost:

  A. FALL LINEUP. Halloween costumes are the priority (a glow in the dark
     skeleton is the proven viral shape), then an ENRICHMENT toy that hides
     treats, a fall squeaky toy, pyjamas/sweater/bandana, a pumpkin spice spray,
     and Thanksgiving/turkey gear.
  B. VIRAL DEVICES. Things that demo in a five second video: automatic massager,
     all-in-one grooming vacuum with trimmer and brush.

TIMING MATTERS AND IT IS TIGHT. Halloween is 31 October. The promise is 5 to 12
business days, so a customer ordering later than roughly 10 October misses it.
Working back through listing, art and ads, anything not live by mid September is
decoration rather than revenue.

Standing rules this applies (see CLAUDE.md):
  * reject over 1kg from China, freight is the real constraint
  * freight resolved through freight_floor.resolve inside the 12 day promise
  * per-product margin floor, checked against the LIVE quote not a curve
  * every image eyeballed against the CJ reference before anything is created
  * duplicate-source check on sku[:11] against the existing catalogue

Scan only. Writes config/scout_fall_results.json for the costing stage; it
creates nothing and buys nothing.
"""
import json
import re
import sys

sys.path.insert(0, 'config')
import cj_api
from scout import REJECT

CATS = {
    # apparel: where costumes actually live
    'Pet Clothings':        '2410110349471606300',
    'Pet Clothing Sets':    '2410110350161600700',
    'Pet Jumpsuits':        '2410110349201623700',
    'Pet Dresses':          '2410110348131619300',
    'Pet Tops':             '2410110348271614500',
    'Pet Sweaters':         '2410110348401611500',
    'Pet Hoodies':          '2410110348531624100',
    'Pet Pajamas':          '2410110349341618600',
    'Pet Functional Cloth': '2410110350021615300',
    'Pet Coats & Jackets':  '2410110349061619800',
    'Pet Scarves':          '2410110350591620800',
    'Pet Bows & Ties':      '2410110351401621300',
    'Pet Headwears':        '2410110352051607900',
    'Pet Hair Accessories': '2410110351231616600',
    # toys
    'Pet Chew Toys':        '2410110339451623300',
    'Pet Sound Toys':       '2410110340161623400',
    'Pet Plush Toys':       '2410110340531618900',
    'Pet Training Toys':    '2410110340031614900',
    'Pet Toy Set':          '2410110340411608400',
    'Pet Chase Toys':       '2410110339311602900',
    # enrichment / treat dispensing
    'Pet Feeding Tools':    '2410110341451628800',
    'Pet Bowls':            '2410110341061612000',
    # grooming + spray
    'Hair Removers & Combs': '2410110354491625800',
    'Pet Shower Products':  '2410110355151622300',
    'Pet Nail Polishers':   '2410110355021623200',
    'Pet Towels':           '2410110355321622400',
    'Pet Blankets & Quilts': '2410110358191601900',
}

THEMES = {
    'halloween_costume': re.compile(
        r'halloween|costume|skeleton|skull|ghost|witch|vampire|bat\b|spider|'
        r'devil|dracula|mummy|zombie|cosplay|dress ?up|glow.{0,12}dark|luminous',
        re.I),
    'fall_theme': re.compile(
        r'pumpkin|maple|autumn|fall\b|acorn|harvest|leaf|leaves|scarecrow|'
        r'sunflower|plaid|tartan', re.I),
    'thanksgiving': re.compile(r'thanksgiving|turkey|pilgrim|cornucopia', re.I),
    'treat_enrichment': re.compile(
        r'treat.{0,14}(dispens|hid|ball|toy|puzzle)|puzzle|snuffle|sniff|'
        r'foraging|slow.{0,6}feed|interactive.{0,14}(feed|treat|puzzle)|'
        r'iq\b|leak(ing|y)? ?food|food.{0,10}leak|hide.{0,10}treat', re.I),
    'viral_device': re.compile(
        r'massag|vacuum|suction.{0,10}(groom|hair)|groom.{0,14}(kit|vacuum|set)|'
        r'electric.{0,14}(brush|comb|clipper|trimmer)|5 ?in ?1|3 ?in ?1|'
        r'4 ?in ?1|all.{0,3}in.{0,3}one|automatic|self.{0,8}clean', re.I),
    'scent_spray': re.compile(
        r'perfume|cologne|fragrance|deodor|spray|scent|freshen', re.I),
}

CAT_ONLY = re.compile(r'\bcat(s)?\b|kitten|litter box|scratch(ing)? post', re.I)


def scan(pages=14):
    seen = {}
    for label, cid in CATS.items():
        for pg in range(1, pages + 1):
            try:
                r = cj_api.call('/product/list',
                                {'categoryId': cid, 'pageSize': 20, 'pageNum': pg})
            except Exception:
                break
            lst = ((r.get('data') or {}).get('list') or [])
            if not lst:
                break
            for p in lst:
                p.setdefault('_cats', []).append(label) if p.get('productSku') in seen \
                    else p.update({'_cats': [label]})
                if p.get('productSku') not in seen:
                    seen[p['productSku']] = p
        print(f'  scanned {label:22} running total {len(seen)}')
    return list(seen.values())


def listed(p):
    try:
        return int(p.get('listedNum') or 0)
    except (TypeError, ValueError):
        return 0


def price(p):
    try:
        return float(str(p.get('sellPrice') or '999').split('-')[0])
    except ValueError:
        return 999.0


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    print(f'scanning {len(CATS)} categories, {pages} pages each...')
    rows = scan(pages)
    print(f'\n{len(rows)} unique products seen\n')

    out = {}
    for theme, rx in THEMES.items():
        hits = []
        for p in rows:
            name = str(p.get('productNameEn') or '')
            if not name or REJECT.search(name):
                continue
            if CAT_ONLY.search(name) and not re.search(r'\bdog|puppy', name, re.I):
                continue
            if rx.search(name):
                hits.append({'spu': p.get('productSku'), 'name': name[:88],
                             'listed': listed(p), 'price': price(p),
                             'cats': p.get('_cats')})
        hits.sort(key=lambda x: -x['listed'])
        out[theme] = hits
        print(f'===== {theme.upper()}  ({len(hits)} candidates) =====')
        for h in hits[:18]:
            print(f"  {h['listed']:>5} lists  ${h['price']:>7.2f}  {h['spu']:14} "
                  f"{h['name'][:70]}")
        print()

    with open('config/scout_fall_results.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print('saved -> config/scout_fall_results.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
