#!/usr/bin/env python3
"""Choose each kit's composition to maximise contribution, on-theme.

THE PHYSICS. Freight is a parcel charge: ~$4.40 fixed + $12.11/kg (fitted
2026-08-04, worst residual $1.56). A kit pays the fixed cost ONCE. So the ideal
kit member is light and carries a high single price: the Finger Toothbrush is
30g and sells for $10.99, so putting it in a kit adds ~$0.36 of freight and
$0.36 of goods against $10.99 of perceived value at full singles pricing. Heavy
items do the opposite, which is how the old Enrichment Kit went wrong in the
(mis-measured) study.

METHOD. For each themed kit: enumerate every 4- and 5-item combination from
that theme's pool (pools are hand-curated for coherence; the optimiser is not
allowed to put a nail grinder in the Toy Kit). Kit price is 20% off the sum of
the NEW single prices from price_book.json, rounded to .00 (house style for
kits). Contribution and margin computed with worst-case component costs (the
dearest variant a customer can select) and freight from the fitted curve on
summed weight. The winner per theme must clear MIN_MARGIN and sit inside the
AOV band; among those, maximum contribution wins.

Winners should be re-quoted live before anything is written, because the fitted
curve is a model and freight is perishable:

    python config/optimise_kits.py            # table
    python config/optimise_kits.py --json OUT
"""
import itertools, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import pricing, freight_floor

MIN_MARGIN = 30.0          # a kit below this is not worth its complexity
PRICE_LO, PRICE_HI = 45.0, 110.0   # 2026 pet AOV band, and above free-ship
DISCOUNT = 0.20            # kits sell at 20% off the singles sum

# Theme pools. Names must match price_book titles minus the "Wagvive " prefix.
# 'core' members are what makes the kit ITS kit and must be present.
THEMES = {
    'New Puppy Kit': dict(
        core=['Cuddle Companion Teddy', 'Finger Toothbrush'],
        pool=['Sneaker Chew Buddy', 'Corduroy Squeak Pals', 'Jingle Plush Ball',
              'Slow Feeder Bowl', 'Paw Print Fleece Blanket',
              'LED Waste Bag Dispenser', 'Bouncy Egg Squeaker']),
    'Toy Kit': dict(
        core=[],
        pool=['Dental Duck Chew Toy', 'Barnyard Squeaker', 'Screaming Chicken',
              'Woodland Rope-Limb Plush', 'Watermelon Rope Frisbee',
              'Sneaker Chew Buddy', 'Bouncy Egg Squeaker', 'Jingle Plush Ball',
              'Corduroy Squeak Pals', 'Crinkle Plush Buddy']),
    'Grooming Essentials Kit': dict(
        # A grooming "essentials" kit without nail care is not credible,
        # whatever the contribution table says. Grinder is core.
        core=['Self-Cleaning Slicker Brush', 'Quiet Electric Nail Grinder'],
        pool=['Pet Hair Remover Mitt', 'Quiet Electric Nail Grinder',
              'LED Nail Clippers', 'Dematting Comb', 'Finger Toothbrush',
              'Dental & Ear Wipes', 'Quick-Dry Bath Robe', 'Paw Washing Cup']),
    'Dog Enrichment Kit': dict(
        # Talk button + lick bowl ARE the enrichment; without both this
        # collapses into a second toy kit and cannibalises it.
        core=['Talk Button', 'Lick Bowl with Ball'],
        pool=['Slow Feeder Bowl', 'Screaming Chicken',
              'Bouncy Egg Squeaker',
              'Anti-Spill Floating Water Bowl']),
    'Travel Kit': dict(
        core=['Travel Water Bottle & Bowl'],
        pool=['LED Waste Bag Dispenser', 'Watermelon Rope Frisbee',
              'Cooling Comfort Pad', 'Paw Washing Cup', 'Quick-Dry Bath Robe',
              'Paw Print Fleece Blanket']),
    'Calm & Comfort Kit': dict(
        core=['Heartbeat Soothing Sloth'],
        pool=['Calming Thunder Wrap', 'Paw Print Fleece Blanket',
              'Waterproof Snuggle Blanket', 'Cooling Comfort Pad',
              'Cuddle Companion Teddy', 'Big Squeak Plush']),
}


def load_costs():
    """title -> (dearest goods cost, heaviest weight, new single price)."""
    scr = json.load(open(os.path.join(
        os.environ.get('SCRATCH', ROOT), 'reprice2.json')
        if os.environ.get('SCRATCH') else
        os.path.join(ROOT, 'docs', 'qa', 'recost-2026-08-04.json'),
        encoding='utf-8'))
    book = json.load(open(os.path.join(ROOT, 'config', 'price_book.json'),
                          encoding='utf-8'))
    price = {v['title'].replace('Wagvive ', ''): max(v['variants'].values())
             for v in book.values()}
    out = {}
    for r in scr:
        t = r['title'].replace('Wagvive ', '')
        if t in price:
            out[t] = (r['cost'], r['weight'], price[t])
    return out


def charm00(x):
    """Kits use whole-dollar prices."""
    return float(max(int(round(x)), 1))


def main():
    costs = load_costs()
    results = {}
    for kit, spec in THEMES.items():
        best = None
        pool = [p for p in spec['pool'] if p in costs and p not in spec['core']]
        core = [p for p in spec['core'] if p in costs]
        for n in (4, 5):
            take = n - len(core)
            if take < 0:
                continue
            for combo in itertools.combinations(pool, take):
                items = core + list(combo)
                goods = sum(costs[t][0] for t in items)
                weight = sum(costs[t][1] for t in items)
                singles = sum(costs[t][2] for t in items)
                price = charm00(singles * (1 - DISCOUNT))
                if not (PRICE_LO <= price <= PRICE_HI):
                    continue
                freight = freight_floor.estimate(weight)
                m = pricing.margin(price, goods, freight) * 100
                if m < MIN_MARGIN:
                    continue
                contrib = price * (1 - pricing.PCT) - (
                    pricing.landed(goods, freight) + pricing.FLAT)
                cand = dict(items=items, goods=goods, weight=weight,
                            singles=singles, price=price, freight=freight,
                            margin=m, contrib=contrib)
                if not best or cand['contrib'] > best['contrib']:
                    best = cand
        results[kit] = best

    for kit, b in results.items():
        print(f"\n=== {kit} ===")
        if not b:
            print("  NO composition clears the constraints")
            continue
        for t in b['items']:
            c, w, pr = costs[t]
            print(f"   {t:34} ${pr:>6.2f} single   {w:>5.0f}g  goods ${c:.2f}")
        print(f"   singles ${b['singles']:.2f} -> kit ${b['price']:.2f}  "
              f"({DISCOUNT*100:.0f}% off)   weight {b['weight']:.0f}g  "
              f"freight ~${b['freight']:.2f}")
        print(f"   margin {b['margin']:.1f}%   contribution ${b['contrib']:.2f}")

    if '--json' in sys.argv:
        json.dump(results, open(sys.argv[sys.argv.index('--json') + 1], 'w'),
                  indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
