#!/usr/bin/env python3
"""
Design kits around what CJ actually charges, using the measurements in
docs/qa/freight-research.json.

Two ideas do the work here.

1. A kit only ships as ONE parcel if a single carrier will take every component.
   The carrier menus from the freight study give that intersection exactly, so
   candidate kits can be filtered before anything is quoted.

2. Within a carrier, freight tracks weight. Fitting price against weight over
   every observation the study made (36 single items plus the quantity ladders)
   gives a predictor good enough to rank thousands of candidate baskets offline.
   Only the winners are then quoted for real, because a fitted number is a guess
   and a quote is a fact.

Kits are built inside their stated theme. A pool per theme is declared below and
combinations are drawn only from it, so a Travel kit never quietly becomes
whatever happens to ship cheapest.

Usage:
    python config/research_kits.py docs/qa/freight-research.json \
                                   docs/qa/kit-designs.json
"""
import itertools, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import (DUTY_PCT, DUTY_PCT_US_WAREHOUSE, FLAT, PCT, SALES_TAX_AVG,
                     RETURNS_RATE, landed)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEE = PCT * (1 + SALES_TAX_AVG)

# What a kit has to earn. Kits are the one place in the catalogue where freight
# is shared, so they should clear a good deal more than a single item.
KIT_FLOOR = 0.45

# Bundle discount off the sum of the components' own recommended prices. 20% is
# the middle of what the pricing study found shoppers expect from a set.
BUNDLE_DISCOUNT = 0.20

SIZE_RANGE = (3, 4)          # items per kit
VERIFY_PER_THEME = 6         # how many candidates get a real quote

# Themes, and the products that legitimately belong in each. A product may
# appear in more than one pool; it may not appear in a kit whose theme it does
# not fit, however good the freight looks.
THEMES = {
    'Grooming Essentials Kit': [
        'Wagvive Self-Cleaning Slicker Brush', 'Wagvive Pet Hair Remover Mitt',
        'Wagvive Quiet Electric Nail Grinder', 'Wagvive Finger Toothbrush',
        'Wagvive Dematting Comb', 'Wagvive LED Nail Clippers',
        'Wagvive Dental & Ear Wipes', 'Wagvive Quick-Dry Bath Robe',
        'Wagvive Cordless Paw Trimmer', 'Wagvive Paw Washing Cup',
    ],
    'Toy Kit': [
        'Wagvive Barnyard Squeaker', 'Wagvive Woodland Rope-Limb Plush',
        'Wagvive Dental Duck Chew Toy', 'Wagvive Watermelon Rope Frisbee',
        'Wagvive Big Squeak Plush', 'Wagvive Crinkle Plush Buddy',
        'Wagvive Squirrel Squeaky Plush', 'Wagvive Jingle Plush Ball',
        'Wagvive Bouncy Egg Squeaker', 'Wagvive Sneaker Chew Buddy',
        'Wagvive Corduroy Squeak Pals', 'Wagvive Screaming Chicken',
        'Wagvive Rope-Limb Puppy Plush',
    ],
    'Dog Enrichment Kit': [
        'Wagvive Slow Feeder Bowl', 'Wagvive Lick Bowl with Ball',
        'Wagvive Talk Button', 'Wagvive Anti-Spill Floating Water Bowl',
        'Wagvive Squirrel Squeaky Plush', 'Wagvive Bouncy Egg Squeaker',
        'Wagvive Sneaker Chew Buddy',
    ],
    'Travel Kit': [
        'Wagvive Travel Water Bottle & Bowl', 'Wagvive LED Waste Bag Dispenser',
        'Wagvive Watermelon Rope Frisbee', 'Wagvive Quick-Dry Bath Robe',
        'Wagvive Paw Washing Cup', 'Wagvive Cooling Comfort Pad',
        'Wagvive Waterproof Snuggle Blanket',
    ],
    'New Puppy Kit': [
        'Wagvive Finger Toothbrush', 'Wagvive LED Waste Bag Dispenser',
        'Wagvive Dental Duck Chew Toy', 'Wagvive Crinkle Plush Buddy',
        'Wagvive Rope-Limb Puppy Plush', 'Wagvive Waterproof Snuggle Blanket',
        'Wagvive Heartbeat Soothing Sloth', 'Wagvive Talk Button',
        'Wagvive Slow Feeder Bowl', 'Wagvive Jingle Plush Ball',
    ],
    # Proposed. The calming products are the highest-contribution items in the
    # catalogue and currently sit in no kit at all.
    'Calm & Comfort Kit (proposed)': [
        'Wagvive Heartbeat Soothing Sloth', 'Wagvive Calming Thunder Wrap',
        'Wagvive Waterproof Snuggle Blanket', 'Wagvive Paw Print Fleece Blanket',
        'Wagvive Cooling Comfort Pad',
    ],
}

# What the five kits contain today, so like is compared with like.
LIVE_KITS = {
    'Grooming Essentials Kit': (85.00, [
        'Wagvive Self-Cleaning Slicker Brush', 'Wagvive Pet Hair Remover Mitt',
        'Wagvive Quiet Electric Nail Grinder', 'Wagvive Finger Toothbrush']),
    'Toy Kit': (65.00, [
        'Wagvive Barnyard Squeaker', 'Wagvive Woodland Rope-Limb Plush',
        'Wagvive Dental Duck Chew Toy', 'Wagvive Watermelon Rope Frisbee']),
    'Dog Enrichment Kit': (98.00, [
        'Wagvive Slow Feeder Bowl', 'Wagvive Anti-Spill Floating Water Bowl',
        'Wagvive Lick Bowl with Ball', 'Wagvive Talk Button']),
    'Travel Kit': (77.00, [
        'Wagvive Travel Water Bottle & Bowl', 'Wagvive LED Waste Bag Dispenser',
        'Wagvive Cooling Comfort Pad', 'Wagvive Watermelon Rope Frisbee']),
    'New Puppy Kit': (79.00, [
        'Wagvive Cooling Comfort Pad', 'Wagvive LED Waste Bag Dispenser',
        'Wagvive Dental Duck Chew Toy']),
}


def log(m):
    print(m, flush=True)


def fit_freight(study):
    """price = a + b * grams, least squares, fitted separately per carrier.

    Observations come from the single-item quotes and from the quantity ladders,
    which is the only place the study varies weight while holding carrier fixed.
    """
    obs = {}
    for p in study['products'].values():
        w = p.get('weight_g')
        if not w or p.get('freight_estimated'):
            continue
        for o in p.get('carrier_menu') or []:
            if o.get('price'):
                obs.setdefault(o['carrier'], []).append((float(w), o['price']))

    for row in study.get('quantity_tests') or []:
        w = row.get('weight_g')
        if not w:
            continue
        for q, r in (row.get('quantities') or {}).items():
            if r.get('cheapest') and r.get('carrier'):
                obs.setdefault(r['carrier'], []).append(
                    (float(w) * int(q), r['cheapest']))

    models = {}
    for carrier, pts in obs.items():
        n = len(pts)
        if n < 3:
            continue
        sx = sum(x for x, _ in pts)
        sy = sum(y for _, y in pts)
        sxx = sum(x * x for x, _ in pts)
        sxy = sum(x * y for x, y in pts)
        denom = n * sxx - sx * sx
        if denom == 0:
            continue
        b = (n * sxy - sx * sy) / denom
        a = (sy - b * sx) / n
        mean = sy / n
        ss_tot = sum((y - mean) ** 2 for _, y in pts)
        ss_res = sum((y - (a + b * x)) ** 2 for x, y in pts)
        models[carrier] = {
            'base': round(a, 3), 'per_gram': round(b, 6), 'n': n,
            'r2': round(1 - ss_res / ss_tot, 3) if ss_tot else None,
        }
    return models


def margin_at(price, goods, freight, duty):
    cost = landed(goods, freight, duty) + FEE * price + FLAT
    return (price - cost) / price if price else 0.0


def min_price(goods, freight, duty, floor):
    return (landed(goods, freight, duty) + FLAT) / (1 - FEE - floor)


def main():
    study_file = sys.argv[1] if len(sys.argv) > 1 else 'docs/qa/freight-research.json'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'docs/qa/kit-designs.json'
    with open(os.path.join(ROOT, study_file), encoding='utf-8') as fh:
        study = json.load(fh)

    by_title = {p['title']: p for p in study['products'].values() if p.get('vid')}

    # Recommended single prices, so a kit can be priced as a discount on the sum
    # of its parts rather than out of the air.
    recs = {}
    rec_path = os.path.join(ROOT, 'docs/qa/pricing-recommendations.json')
    if os.path.exists(rec_path):
        with open(rec_path, encoding='utf-8') as fh:
            for r in json.load(fh):
                recs[r['product']] = r['rec']

    models = fit_freight(study)
    log('freight models, price = base + per_gram * grams')
    for c, m in sorted(models.items(), key=lambda kv: -kv[1]['n'])[:10]:
        log(f"  {c[:34]:36} base ${m['base']:6.2f}  "
            f"${m['per_gram'] * 1000:5.2f}/kg  n={m['n']:3}  r2={m['r2']}")

    out = {'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
           'freight_models': models, 'kit_floor': KIT_FLOOR,
           'bundle_discount': BUNDLE_DISCOUNT}

    def menu(title):
        p = by_title.get(title)
        if not p:
            return set()
        return {o['carrier'] for o in p.get('carrier_menu') or []
                if o.get('price') and o.get('days', 999) <= freight_floor.MAX_DAYS}

    def predict(titles):
        """(freight, carrier) predicted for a basket, or (None, None) if no
        carrier serves every item."""
        shared = set.intersection(*[menu(t) for t in titles]) if titles else set()
        shared = {c for c in shared if c in models}
        if not shared:
            return None, None
        grams = sum((by_title[t].get('weight_g') or 0) for t in titles)
        best, bestc = None, None
        for c in shared:
            m = models[c]
            f = m['base'] + m['per_gram'] * grams
            if best is None or f < best:
                best, bestc = f, c
        return best, bestc

    def evaluate(titles, price=None):
        items = [by_title[t] for t in titles if t in by_title]
        if len(items) != len(titles):
            return None
        goods = sum(i['cost'] for i in items)
        duty = (DUTY_PCT_US_WAREHOUSE
                if all(i['start_country'] == 'US' for i in items) else DUTY_PCT)
        mixed = len({i['start_country'] for i in items}) > 1
        f_pred, carrier = predict(titles)
        singles = sum(i['freight_resolved'] for i in items)
        sum_recs = sum(recs.get(t, 0) for t in titles)
        if price is None:
            price = round(sum_recs * (1 - BUNDLE_DISCOUNT)) - 0.01 if sum_recs else None
        rec = {
            'items': list(titles),
            'goods_cost': round(goods, 2),
            'weight_g': sum((i.get('weight_g') or 0) for i in items),
            'mixed_warehouse': mixed,
            'shared_carrier': carrier,
            'freight_predicted': None if f_pred is None else round(f_pred, 2),
            'freight_as_separate_parcels': round(singles, 2),
            'sum_of_single_prices': round(sum_recs, 2) if sum_recs else None,
            'price': price,
        }
        # If nothing carries the whole basket, CJ ships it as separate parcels
        # and the honest cost is the sum of those shipments.
        eff = f_pred if f_pred is not None else singles
        rec['freight_used'] = round(eff, 2)
        rec['ships_as_one_parcel'] = f_pred is not None
        if price:
            rec['margin'] = round(margin_at(price, goods, eff, duty) * 100, 1)
            rec['contribution'] = round(
                price - (landed(goods, eff, duty) + FEE * price + FLAT), 2)
        rec['min_price_at_floor'] = round(min_price(goods, eff, duty, KIT_FLOOR), 2)
        return rec

    # --- the five live kits, as they stand today -------------------------
    log('\n=== live kits ===')
    live = {}
    for name, (price, titles) in LIVE_KITS.items():
        r = evaluate(titles, price)
        live[name] = r
        if not r:
            log(f'  {name}: components not in study'); continue
        one = 'one parcel' if r['ships_as_one_parcel'] else 'SPLIT PARCELS'
        log(f"  {name[:28]:30} ${price:6.2f}  goods ${r['goods_cost']:5.2f}  "
            f"freight ${r['freight_used']:5.2f} ({one})  margin {r.get('margin')}%")
    out['live_kits'] = live

    # --- candidate designs ------------------------------------------------
    log('\n=== candidate designs ===')
    designs = {}
    for theme, pool in THEMES.items():
        pool = [t for t in pool if t in by_title]
        cands = []
        for n in range(SIZE_RANGE[0], SIZE_RANGE[1] + 1):
            for combo in itertools.combinations(pool, n):
                r = evaluate(combo)
                if r and r.get('margin') is not None:
                    cands.append(r)
        # Rank on contribution per kit, not margin percent: a kit that returns
        # $30 at 48% beats one that returns $18 at 55%.
        cands.sort(key=lambda r: (-r['contribution'], -r['margin']))
        designs[theme] = cands[:20]
        log(f'\n  {theme}  ({len(cands)} on-theme combinations)')
        for r in cands[:5]:
            log(f"    ${r['price']:6.2f}  margin {r['margin']:5.1f}%  "
                f"contrib ${r['contribution']:6.2f}  freight ${r['freight_used']:5.2f}"
                f"{'' if r['ships_as_one_parcel'] else ' SPLIT'}  "
                f"{' + '.join(t.replace('Wagvive ', '') for t in r['items'])}")
    out['candidates'] = designs

    # --- verify the winners with a real quote -----------------------------
    log('\n=== verifying the leaders against live CJ quotes ===')
    verified = []
    seen = set()
    to_check = []
    for theme, cands in designs.items():
        for r in cands[:VERIFY_PER_THEME]:
            key = tuple(sorted(r['items']))
            if key not in seen:
                seen.add(key)
                to_check.append((theme, r))
    for name, (price, titles) in LIVE_KITS.items():
        key = tuple(sorted(titles))
        if key not in seen and all(t in by_title for t in titles):
            seen.add(key)
            to_check.append((f'LIVE {name}', evaluate(titles, price)))

    for theme, r in to_check:
        items = [{'quantity': 1, 'vid': by_title[t]['vid']} for t in r['items']]
        starts = {by_title[t]['start_country'] for t in r['items']}
        start = 'CN' if 'CN' in starts else 'US'
        res = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': start, 'endCountryCode': 'US', 'products': items})
        opts = res.get('data') or []
        freight, carrier, aging, estimated = freight_floor.resolve(opts)
        actual_one_parcel = bool(opts)
        eff = freight if actual_one_parcel else r['freight_as_separate_parcels']
        goods = r['goods_cost']
        duty = DUTY_PCT if 'CN' in starts else DUTY_PCT_US_WAREHOUSE
        v = dict(r)
        v.update({
            'theme': theme,
            'quoted_one_parcel': actual_one_parcel,
            'quoted_freight': round(freight, 2) if actual_one_parcel else None,
            'quoted_carrier': carrier if actual_one_parcel else None,
            'quoted_aging': aging if actual_one_parcel else None,
            'quoted_estimated': estimated,
            'freight_final': round(eff, 2),
            'prediction_error': (None if not actual_one_parcel
                                 or r['freight_predicted'] is None
                                 else round(freight - r['freight_predicted'], 2)),
        })
        if r.get('price'):
            v['margin_verified'] = round(
                margin_at(r['price'], goods, eff, duty) * 100, 1)
            v['contribution_verified'] = round(
                r['price'] - (landed(goods, eff, duty) + FEE * r['price'] + FLAT), 2)
        v['min_price_verified'] = round(min_price(goods, eff, duty, KIT_FLOOR), 2)
        verified.append(v)
        tag = 'one parcel' if actual_one_parcel else 'SPLIT'
        log(f"  {theme[:26]:28} ${r.get('price') or 0:6.2f}  freight ${eff:5.2f} "
            f"({tag})  margin {v.get('margin_verified')}%  "
            f"{' + '.join(t.replace('Wagvive ', '')[:14] for t in r['items'])}")

    out['verified'] = verified

    with open(os.path.join(ROOT, out_file), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    log(f'\nwrote {out_file}')


if __name__ == '__main__':
    main()
