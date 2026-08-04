#!/usr/bin/env python3
"""
Empirical study of how CJ charges freight, so kits can be built around it.

Everything the money model does with freight rests on assumptions that have
never been measured. This script measures them. It is READ ONLY: it queries CJ
and writes a JSON dump, it changes nothing in the store and nothing at CJ.

Four questions, four phases:

  A. Carrier menu per product. `/logistic/freightCalculate` returns every
     carrier that will take the item. Two items can only ship as ONE parcel if
     at least one carrier serves both, so the intersection of these menus is
     what actually decides kit composition. kit_margins.py already found the
     Grooming kit fails this test.

  B. The consolidation law. Quote the same vid at rising quantity, then quote
     different vids together, then compare against the sum of the singles. That
     separates the three possibilities: per-item charging (kits save nothing),
     per-parcel weight-based (kits save a lot), or a hybrid.

  C. Warehouse geography. Which of our 36 products can ship from a US warehouse,
     what that does to freight and transit, and whether CJ exposes a filter for
     finding US-stocked goods rather than inferring it from the CJBQ prefix.

  D. Replacement candidates. Scan the pet categories for goods that could stand
     in for the nine products the pricing study found unsellable, scored against
     a 15% floor rather than 50%, with real freight resolved through
     freight_floor so a $0.00 quote can never read as free carriage.

Usage:
    python config/research_freight.py docs/qa/freight-research.json
"""
import json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import (DUTY_PCT, DUTY_PCT_US_WAREHOUSE, FLAT, PCT, SALES_TAX_AVG,
                     landed)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEE = PCT * (1 + SALES_TAX_AVG)

# The owner's new floor. 10 to 15% is acceptable at the low end, below that is a
# non-starter, so candidates are scored at 15% and reported down to 10%.
FLOOR_MIN = 0.15
FLOOR_HARD = 0.10

CATS = {
    'Chase toys': '2410110339311602900',
    'Chew toys': '2410110339451623300',
    'Training toys': '2410110340031614900',
    'Sound toys': '2410110340161623400',
    'Toy sets': '2410110340411608400',
    'Plush toys': '2410110340531618900',
    'Trainers': '2410110342161616300',
    'Hair removers and combs': '2410110354491625800',
    'Nail polishers': '2410110355021623200',
    'Shower products': '2410110355151622300',
    'Towels': '2410110355321622400',
    'Pet bowls': '2410110341061612000',
    'Drinking tools': '2410110341331606800',
    'Feeding tools': '2410110341451628800',
    'Pet mats': '2410110357391611900',
    'Blankets and quilts': '2410110358191601900',
}

# What each unsellable product would have to be replaced by, and the market
# ceiling the pricing study established for it.
REPLACE = [
    {'for': 'Crinkle Plush Buddy',        'cat': 'Plush toys',
     'ceiling': 8.00,  'match': r'crinkle|plush|squeak'},
    # Added on the second pass. The delivered-price analysis put these three
    # below their own floor, two of them because they are heavy and one because
    # CJ's freight on liquids jumped 57% in a month.
    {'for': 'Dental & Ear Wipes',         'cat': 'Towels',
     'ceiling': 13.99, 'match': r'wipe|cleaning|grooming|deodoriz'},
    {'for': 'Waterproof Snuggle Blanket', 'cat': 'Blankets and quilts',
     'ceiling': 29.95, 'match': r'blanket|quilt|waterproof|throw|sherpa|flannel'},
    {'for': 'Waterproof Sofa & Furniture Cover', 'cat': 'Pet mats',
     'ceiling': 39.99, 'match': r'sofa|couch|furniture|cover|mat|pad|waterproof'},
    {'for': 'Dental Duck Chew Toy',       'cat': 'Chew toys',
     'ceiling': 10.99, 'match': r'dental|chew|clean.*teeth|toothbrush'},
    {'for': 'Woodland Rope-Limb Plush',   'cat': 'Plush toys',
     'ceiling': 13.00, 'match': r'rope|plush|animal'},
    {'for': 'Screaming Chicken',          'cat': 'Sound toys',
     'ceiling': 13.99, 'match': r'chicken|scream|squeak|sound|vocal'},
    {'for': 'Rope-Limb Puppy Plush',      'cat': 'Plush toys',
     'ceiling': 15.99, 'match': r'rope|plush|puppy'},
    {'for': 'Squirrel Squeaky Plush',     'cat': 'Plush toys',
     'ceiling': 16.23, 'match': r'squirrel|hide|burrow|puzzle|squeak'},
    {'for': 'Lick Bowl with Ball',        'cat': 'Feeding tools',
     'ceiling': 19.00, 'match': r'lick|slow|feed|mat|bowl'},
    {'for': 'Self-Cleaning Slicker Brush', 'cat': 'Hair removers and combs',
     'ceiling': 29.99, 'match': r'slicker|brush|self.?clean|comb'},
    {'for': 'Anti-Spill Floating Water Bowl', 'cat': 'Pet bowls',
     'ceiling': 18.00, 'match': r'water|spill|float|drink|slow'},
]

# Species and formats that are not this catalogue. "Scalp", "eyebrow" and
# "seaming" caught human grooming tools sitting in CJ's pet comb category on the
# first pass; "self pickup" items are warehouse collection only and cannot ship.
REJECT = re.compile(r'kitten|litter|bird|fish|hamster|rabbit|reptile|'
                    r'aquarium|parrot|costume|human|scalp|eyebrow|seaming|'
                    r'self pickup|wig|eyelash|beard|nail art|catnip|'
                    r'\bcat\b|cats\b|feline|\bfor cats\b', re.I)

# ...but keep a listing that names cats only alongside dogs, which is most of
# CJ's catalogue and perfectly sellable to dog owners.
KEEP_ANYWAY = re.compile(r'dog|puppy|pet\b', re.I)


def off_catalogue(name):
    """True when a listing is for a species or a market we do not serve."""
    if not REJECT.search(name):
        return False
    # "Cat And Dog Comb" is fine. "Elevated Cat Bowls Set" is not.
    return not KEEP_ANYWAY.search(name)


def log(msg):
    print(msg, flush=True)


def quote(items, start='CN'):
    """Raw carrier list for a basket. `items` is [{'quantity': n, 'vid': v}]."""
    r = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US', 'products': items})
    return r.get('data') or []


def slim(options):
    """Carrier menu trimmed to the fields that matter, cheapest first."""
    out = []
    for o in options or []:
        p = o.get('logisticPrice')
        out.append({
            'carrier': o.get('logisticName'),
            'price': None if p is None else round(float(p), 2),
            'aging': o.get('logisticAging'),
            'days': freight_floor.upper_days(o.get('logisticAging')),
        })
    return sorted(out, key=lambda x: (x['price'] is None, x['price'] or 0))


def rep_variant(spu):
    """Product record plus the median-cost variant, which is what a kit would
    most likely carry. Returns (product_dict, variant_dict) or (None, None)."""
    d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
    variants = d.get('variants') or []
    if not variants:
        return d or None, None

    def cost(v):
        try:
            return float(str(v.get('variantSellPrice') or '999').split('-')[0])
        except ValueError:
            return 999.0

    return d, sorted(variants, key=cost)[len(variants) // 2]


def stock_rows(sku):
    r = cj_api.call('/product/stock/queryBySku', {'sku': sku})
    data = r.get('data')
    return data if isinstance(data, list) else []


def phase_a_and_c(spus, out):
    """Carrier menu, warehouse and single-item freight for every catalogue SPU."""
    log('\n=== Phase A/C: carrier menu and warehouse, per product ===')
    products = {}
    for i, entry in enumerate(spus, 1):
        spu, title = entry['spu'], entry['title']
        d, v = rep_variant(spu)
        if not v:
            products[spu] = {'title': title, 'error': 'no variants'}
            log(f'{i:2}. {title[:38]:40} NO VARIANTS')
            continue

        sku = v.get('variantSku') or ''
        us_prefix = sku.startswith('CJBQ')
        rows = stock_rows(sku)
        # CJ's true shippable quantity is inventory + factoryInventory summed
        # over every stock row, not totalInventoryNum.
        warehouses = sorted({str(r.get('countryCode') or r.get('areaEn') or '?')
                             for r in rows})
        qty = sum((r.get('storageNum') or 0) + (r.get('factoryInventory') or 0)
                  for r in rows if isinstance(r, dict))

        start = 'US' if us_prefix else 'CN'
        raw = quote([{'quantity': 1, 'vid': v.get('vid')}], start)
        opts = slim(raw)
        grams = v.get('variantWeight') or d.get('productWeight')
        freight, carrier, aging, estimated = freight_floor.resolve(
            raw, weight_g=grams)

        try:
            cost = float(str(v.get('variantSellPrice') or '0').split('-')[0])
        except ValueError:
            cost = 0.0

        products[spu] = {
            'title': title,
            'cj_name': d.get('productNameEn'),
            'vid': v.get('vid'),
            'sku': sku,
            'variant_key': v.get('variantKey'),
            'cost': cost,
            'weight_g': v.get('variantWeight') or d.get('productWeight'),
            'us_warehouse_prefix': us_prefix,
            'stock_warehouses': warehouses,
            'stock_rows': rows[:6],
            'shippable_qty': qty,
            'start_country': start,
            'carrier_menu': opts,
            'freight_resolved': freight,
            'carrier_resolved': carrier,
            'aging_resolved': aging,
            'freight_estimated': estimated,
        }
        log(f'{i:2}. {title[:38]:40} ${cost:6.2f} + ${freight:5.2f} freight  '
            f'{len(opts):2} carriers  wh={",".join(warehouses) or "?"}')

    out['products'] = products
    return products


def phase_b(products, out):
    """The consolidation law: quantity scaling, then multi-item baskets."""
    log('\n=== Phase B1: same item at rising quantity ===')
    usable = [p for p in products.values()
              if p.get('vid') and not p.get('freight_estimated')]
    usable.sort(key=lambda p: p.get('weight_g') or 0)
    # light, middling and heavy, so any weight-break shows up
    picks = [usable[1], usable[len(usable) // 2], usable[-1]] if len(usable) > 3 else usable

    qty_tests = []
    for p in picks:
        row = {'title': p['title'], 'weight_g': p['weight_g'], 'quantities': {}}
        for q in (1, 2, 3, 5, 10):
            opts = slim(quote([{'quantity': q, 'vid': p['vid']}], p['start_country']))
            best = next((o for o in opts if o['price']), None)
            row['quantities'][q] = {
                'cheapest': best['price'] if best else None,
                'carrier': best['carrier'] if best else None,
                'carriers_offered': len(opts),
            }
        f1 = (row['quantities'][1] or {}).get('cheapest')
        for q in (2, 3, 5, 10):
            fq = row['quantities'][q].get('cheapest')
            if f1 and fq:
                row['quantities'][q]['vs_n_singles'] = round(fq / (f1 * q), 3)
                row['quantities'][q]['saving_pct'] = round(
                    (1 - fq / (f1 * q)) * 100, 1)
        qty_tests.append(row)
        log(f"  {p['title'][:34]:36} " + '  '.join(
            f"x{q}=${(row['quantities'][q].get('cheapest') or 0):.2f}"
            for q in (1, 2, 3, 5, 10)))

    out['quantity_tests'] = qty_tests

    log('\n=== Phase B2: different items in one basket ===')
    # Pairs and quads drawn from products that actually belong in a kit together.
    china = [p for p in products.values()
             if p.get('vid') and p.get('start_country') == 'CN']
    by_title = {p['title']: p for p in products.values() if p.get('vid')}

    baskets = []

    def basket(label, titles):
        items = [by_title[t] for t in titles if t in by_title]
        if len(items) != len(titles):
            missing = [t for t in titles if t not in by_title]
            log(f'  {label}: SKIP, missing {missing}')
            return
        starts = {i['start_country'] for i in items}
        if len(starts) > 1:
            note = 'MIXED WAREHOUSE'
        else:
            note = ''
        start = 'CN' if 'CN' in starts else 'US'
        payload = [{'quantity': 1, 'vid': i['vid']} for i in items]
        combined = slim(quote(payload, start))
        best = next((o for o in combined if o['price']), None)
        singles = sum(i['freight_resolved'] for i in items)
        menus = [{o['carrier'] for o in i['carrier_menu'] if o['price']} for i in items]
        shared = set.intersection(*menus) if menus else set()
        rec = {
            'label': label,
            'items': titles,
            'note': note,
            'mixed_warehouse': len(starts) > 1,
            'sum_of_singles': round(singles, 2),
            'combined_cheapest': best['price'] if best else None,
            'combined_carrier': best['carrier'] if best else None,
            'combined_aging': best['aging'] if best else None,
            'carriers_offered': len(combined),
            'shared_carriers': sorted(shared),
            'goods_cost': round(sum(i['cost'] for i in items), 2),
            'weight_g': sum((i.get('weight_g') or 0) for i in items),
        }
        if best and singles:
            rec['saving_vs_singles'] = round(singles - best['price'], 2)
            rec['saving_pct'] = round((1 - best['price'] / singles) * 100, 1)
        baskets.append(rec)
        got = f"${best['price']:.2f} via {best['carrier']}" if best else 'NO COMBINED QUOTE'
        log(f'  {label[:40]:42} singles ${singles:6.2f}  combined {got}')
        return rec

    # The five live kits, as currently composed.
    basket('LIVE Grooming Essentials Kit',
           ['Wagvive Self-Cleaning Slicker Brush', 'Wagvive Dematting Comb',
            'Wagvive LED Nail Clippers', 'Wagvive Dental & Ear Wipes'])
    basket('LIVE Toy Kit',
           ['Wagvive Barnyard Squeaker', 'Wagvive Crinkle Plush Buddy',
            'Wagvive Big Squeak Plush', 'Wagvive Screaming Chicken'])
    basket('LIVE Travel Kit',
           ['Wagvive Travel Water Bottle & Bowl', 'Wagvive LED Waste Bag Dispenser',
            'Wagvive Quick-Dry Bath Robe'])
    basket('LIVE Enrichment Kit',
           ['Wagvive Lick Bowl with Ball', 'Wagvive Slow Feeder Bowl',
            'Wagvive Talk Button'])
    basket('LIVE New Puppy Kit',
           ['Wagvive Rope-Limb Puppy Plush', 'Wagvive Finger Toothbrush',
            'Wagvive Waterproof Snuggle Blanket'])

    # Pairwise probes: does adding a second item cost anything at all?
    seeds = [p for p in china if not p.get('freight_estimated')][:8]
    for a in seeds[:4]:
        for b in seeds[4:6]:
            if a['title'] != b['title']:
                basket(f"PAIR {a['title'][:18]} + {b['title'][:18]}",
                       [a['title'], b['title']])

    out['baskets'] = baskets
    return baskets


def carrier_overlap(products, out):
    """Which products can legally share a parcel, expressed as a matrix."""
    log('\n=== Phase A2: carrier overlap matrix ===')
    menus = {}
    for spu, p in products.items():
        if not p.get('carrier_menu'):
            continue
        menus[p['title']] = {o['carrier'] for o in p['carrier_menu']
                             if o['price'] and o['days'] <= freight_floor.MAX_DAYS}

    # How common is each carrier across the catalogue? The most widely offered
    # carrier is the one a kit should be built around.
    tally = {}
    for s in menus.values():
        for c in s:
            tally[c] = tally.get(c, 0) + 1
    ranked = sorted(tally.items(), key=lambda kv: -kv[1])
    for c, n in ranked[:15]:
        log(f'  {n:3}/{len(menus)}  {c}')

    out['carrier_reach'] = [{'carrier': c, 'products': n, 'of': len(menus)}
                            for c, n in ranked]
    out['carrier_menus'] = {t: sorted(s) for t, s in menus.items()}
    # Products no widely-shared carrier will take are the ones that break kits.
    if ranked:
        top = ranked[0][0]
        out['excluded_from_top_carrier'] = sorted(
            t for t, s in menus.items() if top not in s)
        log(f'  products {top} will NOT take: '
            f'{out["excluded_from_top_carrier"]}')
    return menus


def phase_d(out):
    """Hunt replacements for the unsellable nine, scored at a 15% floor."""
    log('\n=== Phase D: replacement candidates ===')

    # One catalogue scan shared by every brief.
    listings = {}
    for label, cid in CATS.items():
        for pg in (1, 2, 3):
            r = cj_api.call('/product/list',
                            {'categoryId': cid, 'pageSize': 20, 'pageNum': pg})
            lst = ((r.get('data') or {}).get('list') or [])
            if not lst:
                break
            for p in lst:
                p['_cat'] = label
                listings.setdefault(p.get('productSku'), p)
        log(f'  scanned {label}: running total {len(listings)}')
    out['listing_sample'] = list(listings.values())[:2]   # schema probe

    # Does CJ expose a warehouse filter, or must US stock be inferred from the
    # CJBQ prefix? Probe one category both ways and record the difference.
    probe_cid = CATS['Plush toys']
    plain = cj_api.call('/product/list', {'categoryId': probe_cid, 'pageSize': 20,
                                          'pageNum': 1})
    with_us = cj_api.call('/product/list', {'categoryId': probe_cid, 'pageSize': 20,
                                            'pageNum': 1, 'countryCode': 'US'})
    def skus(r):
        return [p.get('productSku') for p in ((r.get('data') or {}).get('list') or [])]
    out['country_filter_probe'] = {
        'plain_total': ((plain.get('data') or {}).get('total')),
        'us_total': ((with_us.get('data') or {}).get('total')),
        'plain_skus': skus(plain),
        'us_skus': skus(with_us),
        'filter_works': skus(plain) != skus(with_us),
    }
    log(f"  countryCode=US filter changes results: "
        f"{out['country_filter_probe']['filter_works']}")

    def listprice(p):
        try:
            return float(str(p.get('sellPrice') or p.get('productSellPrice')
                             or '999').split('-')[0])
        except ValueError:
            return 999.0

    def name(p):
        return str(p.get('productNameEn') or p.get('productName') or '')

    results = []
    for brief in REPLACE:
        pat = re.compile(brief['match'], re.I)
        ceiling = brief['ceiling']
        # Anything whose bare product cost already eats the ceiling is hopeless
        # before freight is added, so filter hard before spending API calls.
        pool = [p for p in listings.values()
                if p.get('_cat') == brief['cat']
                and pat.search(name(p))
                and not off_catalogue(name(p))
                and listprice(p) <= ceiling * 0.35]
        pool.sort(key=listprice)
        log(f"\n  {brief['for']}  ceiling ${ceiling:.2f}  "
            f"{len(pool)} candidates in {brief['cat']}")

        found = []
        for p in pool[:8]:
            spu = p.get('productSku')
            d, v = rep_variant(spu)
            if not v:
                continue
            sku = v.get('variantSku') or ''
            us = sku.startswith('CJBQ')
            start = 'US' if us else 'CN'
            opts = quote([{'quantity': 1, 'vid': v.get('vid')}], start)
            grams = v.get('variantWeight') or d.get('productWeight')
            freight, carrier, aging, estimated = freight_floor.resolve(
                opts, weight_g=grams)
            try:
                cost = float(str(v.get('variantSellPrice') or '999').split('-')[0])
            except ValueError:
                cost = 999.0
            duty = DUTY_PCT_US_WAREHOUSE if us else DUTY_PCT
            base = landed(cost, freight, duty) + FLAT
            need15 = base / (1 - FEE - FLOOR_MIN)
            need10 = base / (1 - FEE - FLOOR_HARD)
            # Margin if we simply sell at the market ceiling.
            m_at_ceiling = ((ceiling - (landed(cost, freight, duty)
                                        + FEE * ceiling + FLAT)) / ceiling * 100)
            rec = {
                'replaces': brief['for'],
                'spu': spu,
                'name': name(p)[:90],
                'category': brief['cat'],
                'cost': round(cost, 2),
                'freight': round(freight, 2),
                'freight_estimated': estimated,
                'carrier': carrier,
                'aging': aging,
                'us_warehouse': us,
                'weight_g': v.get('variantWeight') or d.get('productWeight'),
                'listed_count': p.get('listedNum'),
                'ceiling': ceiling,
                'price_for_15pct': round(need15, 2),
                'price_for_10pct': round(need10, 2),
                'margin_at_ceiling': round(m_at_ceiling, 1),
                'viable_at_15': need15 <= ceiling,
                'viable_at_10': need10 <= ceiling,
                'carrier_menu': slim(opts),
            }
            found.append(rec)
            mark = 'OK ' if rec['viable_at_15'] else ('~  ' if rec['viable_at_10'] else 'no ')
            log(f"    {mark}${cost:5.2f}+${freight:5.2f}fr  need ${need15:6.2f} "
                f"@15%   {rec['margin_at_ceiling']:6.1f}% at ceiling   "
                f"{rec['name'][:44]}")
        found.sort(key=lambda r: -r['margin_at_ceiling'])
        results.extend(found)

    out['replacements'] = results
    return results


def phase_e(out):
    """US-warehouse goods.

    The first pass inferred US stock from the CJBQ SKU prefix and found none in
    our catalogue. It also showed that `/product/list` accepts countryCode: the
    plush category returns 350 products plain and 70 with countryCode=US. So CJ
    does expose the filter, and this phase uses it properly: scan every pet
    category for US-stocked goods, then quote them from the US warehouse to see
    what domestic carriage actually costs against China air freight.
    """
    log('\n=== Phase E: US warehouse goods ===')
    found = {}
    for label, cid in CATS.items():
        for pg in (1, 2):
            r = cj_api.call('/product/list', {'categoryId': cid, 'pageSize': 20,
                                              'pageNum': pg, 'countryCode': 'US'})
            data = r.get('data') or {}
            lst = data.get('list') or []
            if pg == 1:
                log(f'  {label}: {data.get("total")} US-stocked products')
            if not lst:
                break
            for p in lst:
                p['_cat'] = label
                found.setdefault(p.get('productSku'), p)

    def name(p):
        return str(p.get('productNameEn') or p.get('productName') or '')

    def listprice(p):
        try:
            return float(str(p.get('sellPrice') or p.get('productSellPrice')
                             or '999').split('-')[0])
        except ValueError:
            return 999.0

    pool = [p for p in found.values() if not off_catalogue(name(p))]
    pool.sort(key=listprice)
    log(f'  {len(pool)} US-stocked candidates after filtering')

    rows = []
    for p in pool[:30]:
        spu = p.get('productSku')
        d, v = rep_variant(spu)
        if not v:
            continue
        sku = v.get('variantSku') or ''
        grams = v.get('variantWeight') or d.get('productWeight')
        # Quote it both ways. If the US warehouse really holds it, the US quote
        # should be domestic carriage; the CN quote is what we pay today.
        us_opts = quote([{'quantity': 1, 'vid': v.get('vid')}], 'US')
        cn_opts = quote([{'quantity': 1, 'vid': v.get('vid')}], 'CN')
        us_f, us_c, us_a, us_e = freight_floor.resolve(us_opts, weight_g=grams)
        cn_f, cn_c, cn_a, cn_e = freight_floor.resolve(cn_opts, weight_g=grams)
        rows_stock = stock_rows(sku)
        try:
            cost = float(str(v.get('variantSellPrice') or '999').split('-')[0])
        except ValueError:
            cost = 999.0
        rec = {
            'spu': spu, 'name': name(p)[:90], 'category': p.get('_cat'),
            'sku': sku, 'cost': round(cost, 2), 'weight_g': grams,
            'listed_count': p.get('listedNum'),
            'us_freight': round(us_f, 2), 'us_carrier': us_c, 'us_aging': us_a,
            'us_estimated': us_e,
            'cn_freight': round(cn_f, 2), 'cn_carrier': cn_c, 'cn_aging': cn_a,
            'cn_estimated': cn_e,
            'stock_warehouses': sorted({str(r.get('countryCode') or '?')
                                        for r in rows_stock}),
            # US stock was already imported by CJ, so no duty is charged again.
            'price_for_15pct_us': round(
                (landed(cost, us_f, DUTY_PCT_US_WAREHOUSE) + FLAT)
                / (1 - FEE - FLOOR_MIN), 2),
            'price_for_15pct_cn': round(
                (landed(cost, cn_f, DUTY_PCT) + FLAT) / (1 - FEE - FLOOR_MIN), 2),
        }
        rec['us_advantage'] = round(rec['price_for_15pct_cn']
                                    - rec['price_for_15pct_us'], 2)
        rows.append(rec)
        log(f"    ${cost:5.2f} {str(grams or 0):>6}g  US ${us_f:5.2f}"
            f"{'E' if us_e else ' '} vs CN ${cn_f:5.2f}{'E' if cn_e else ' '}  "
            f"advantage ${rec['us_advantage']:6.2f}  {rec['name'][:44]}")

    rows.sort(key=lambda r: -r['us_advantage'])
    out['us_warehouse'] = rows
    return rows


def main():
    out_file = sys.argv[1] if len(sys.argv) > 1 else 'docs/qa/freight-research.json'
    with open(os.path.join(ROOT, 'config', 'audit_spus.json'), encoding='utf-8') as fh:
        spus = json.load(fh)

    out = {'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'floor_min': FLOOR_MIN, 'floor_hard': FLOOR_HARD}

    products = phase_a_and_c(spus, out)
    carrier_overlap(products, out)
    phase_b(products, out)
    phase_d(out)
    phase_e(out)

    os.makedirs(os.path.dirname(os.path.join(ROOT, out_file)), exist_ok=True)
    with open(os.path.join(ROOT, out_file), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    log(f'\nwrote {out_file}')


if __name__ == '__main__':
    main()
