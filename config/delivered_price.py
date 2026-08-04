#!/usr/bin/env python3
"""
Score every product on DELIVERED price, which is the number that competes.

The pricing study compared our item price against market prices, and treated the
$5.95 the customer pays for shipping on sub-threshold orders as upside outside
the model. Both halves of that are defensible on their own and wrong together:
Amazon and Chewy prices are delivered prices, so an item price is not comparable
to them, and the $5.95 is real revenue against real freight.

This script does the comparison properly. For each product it asks: what is the
lowest DELIVERED price at which this clears a given margin, counting the shipping
the customer pays as revenue, and how does that compare with what the item
actually sells for delivered elsewhere?

    delivered = item + shipping paid by the customer
    cost      = landed(goods, freight) + fee_rate * delivered + FLAT
    margin    = (delivered - cost) / delivered

Solving, the floor is

    delivered >= (landed + FLAT) / (1 - fee_rate - floor)

which is the same shape as pricing.min_price, except the freight is now measured
rather than buffered, and the price it returns is the one a shopper compares.

Offline. Reads the freight study and the pricing recommendations, writes a table.

Usage:
    python config/delivered_price.py docs/qa/freight-research.json \
                                     docs/qa/delivered-price.json
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import DUTY_PCT, FLAT, PCT, SALES_TAX_AVG, landed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEE = PCT * (1 + SALES_TAX_AVG)

# Live Shopify rates, read from the store 2026-08-04.
FLAT_SHIPPING = 5.95
FREE_OVER = 60.00

TIERS = (0.15, 0.25, 0.35)


def floor_price(goods, freight, floor, duty=DUTY_PCT):
    return (landed(goods, freight, duty) + FLAT) / (1 - FEE - floor)


def main():
    study_file = sys.argv[1] if len(sys.argv) > 1 else 'docs/qa/freight-research.json'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'docs/qa/delivered-price.json'

    with open(os.path.join(ROOT, study_file), encoding='utf-8') as fh:
        study = json.load(fh)
    with open(os.path.join(ROOT, 'docs/qa/pricing-recommendations.json'),
              encoding='utf-8') as fh:
        recs = {r['product']: r for r in json.load(fh)}

    rows = []
    for p in study['products'].values():
        if not p.get('vid'):
            continue
        r = recs.get(p['title'], {})
        mkt = r.get('mkt_high')
        goods, freight = p['cost'], p['freight_resolved']
        row = {
            'product': p['title'],
            'cost': goods,
            'freight': freight,
            'weight_g': p.get('weight_g'),
            'freight_estimated': p.get('freight_estimated'),
            'current_price': r.get('now'),
            'recommended_price': r.get('rec'),
            'market_delivered': mkt,
        }
        for t in TIERS:
            row[f'delivered_floor_{int(t*100)}'] = round(floor_price(goods, freight, t), 2)
        # Two ways to reach that delivered floor.
        f15 = row['delivered_floor_15']
        row['item_price_if_customer_pays_shipping'] = round(max(f15 - FLAT_SHIPPING, 0), 2)
        row['item_price_if_free_shipping'] = f15
        if mkt:
            row['headroom_vs_market'] = round(mkt - f15, 2)
            row['viable_as_single'] = f15 <= mkt
            # Margin if we simply sell at the market delivered price.
            cost = landed(goods, freight) + FEE * mkt + FLAT
            row['margin_at_market_delivered'] = round((mkt - cost) / mkt * 100, 1)
        # Marginal economics: what this item costs to ADD to an order that is
        # already shipping, which is the only number that matters for kits,
        # cross-sell and the free-shipping threshold.
        grams = p.get('weight_g') or 0
        row['marginal_freight_in_existing_parcel'] = round(0.01190 * grams, 2)
        row['marginal_landed_in_existing_parcel'] = round(
            (goods * (1 + DUTY_PCT) + 0.01190 * grams) * 1.03, 2)
        rows.append(row)

    rows.sort(key=lambda r: (r.get('headroom_vs_market') is None,
                             r.get('headroom_vs_market', 0)))

    hdr = (f"{'product':38} {'cost':>6} {'frt':>6} {'d15':>7} {'d25':>7} "
           f"{'d35':>7} {'mkt':>7} {'room':>7} {'m@mkt':>7} {'+parcel':>8}")
    print(hdr)
    print('-' * len(hdr))
    for r in rows:
        print(f"{r['product'].replace('Wagvive ',''):38} {r['cost']:6.2f} "
              f"{r['freight']:6.2f} {r['delivered_floor_15']:7.2f} "
              f"{r['delivered_floor_25']:7.2f} {r['delivered_floor_35']:7.2f} "
              f"{(r.get('market_delivered') or 0):7.2f} "
              f"{(r.get('headroom_vs_market') or 0):7.2f} "
              f"{(r.get('margin_at_market_delivered') or 0):6.1f}% "
              f"{r['marginal_landed_in_existing_parcel']:8.2f}")

    viable = [r for r in rows if r.get('viable_as_single')]
    print(f"\n{len(viable)} of {len(rows)} clear 15% as a single at the market "
          f"delivered price.")
    print(f"{sum(1 for r in rows if (r.get('margin_at_market_delivered') or -1) >= 25)}"
          f" of {len(rows)} clear 25%.")

    out = {
        'generated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'flat_shipping': FLAT_SHIPPING, 'free_over': FREE_OVER,
        'note': ('delivered price = item + shipping the customer pays. Market '
                 'prices are delivered prices, so this is the like-for-like '
                 'comparison the pricing study did not make.'),
        'products': rows,
    }
    with open(os.path.join(ROOT, out_file), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(f'\nwrote {out_file}')


if __name__ == '__main__':
    main()
