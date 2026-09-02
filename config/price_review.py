#!/usr/bin/env python3
"""Find every product priced ABOVE the floor and say what it should cost.

margin_guard answers "is anything under the floor". This answers the opposite
and, for a store with no traction, the more commercially urgent question: what
are we overcharging for?

The trigger was a real basket. An LED Halo Collar plus two costumes came to
$84.97 while costing $33.56 delivered, about 57% margin. At a 20% floor the same
basket is roughly $46, and that difference is the gap between a shopper buying
and a shopper leaving.

TARGET, NOT FLOOR. The owner's rule is a 20% MINIMUM. This prices AT that
minimum plus a small buffer, because a price set at exactly 20% breaches the
moment CJ moves freight by a cent, and this store has already had a scheduled
job fail 14 runs straight for exactly that reason. BUFFER_PCT is that headroom.

WHAT IT WILL NOT DO
  * It will not touch a variant CJ would not price. An unanswered SKU is
    UNKNOWN, never an invitation to guess a cost.
  * It will not raise anything. Under-floor items are margin_guard's job; this
    only ever lowers.
  * It will not reprice kits. A kit price is bound to its compare_at in
    kit_colorways.py and the two must move together, so kits go through that
    file and rebuild_kits.py --reprice-only.

ONE PRICE PER PRODUCT. Colour variants of a product are priced identically
(house rule, so the storefront never shows odd per-colour pricing), so the new
price is the HIGHEST of the variants' ideal prices. Taking the average or the
cheapest would drag a dearer variant under the floor.

    python config/price_review.py                 # report
    python config/price_review.py --apply         # lower them
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import margin_guard as MG                    # noqa: E402
import pricing                               # noqa: E402
import freight_floor                         # noqa: E402

TARGET = 0.20        # the owner's floor, and now also the target
BUFFER_PCT = 0.02    # aim 2 points above so a freight wobble is not a breach
MIN_DROP = 0.50      # ignore smaller changes; churn is not a saving


def sane(x):
    """Round UP to a .99 price point. Never rounds down past the target."""
    s = math.floor(x) + 0.99
    return round(s if s >= x else s + 1, 2)


def duty_for(sku):
    return (pricing.DUTY_PCT_US_WAREHOUSE
            if freight_floor.origin_for(sku) == 'US' else pricing.DUTY_PCT)


def main():
    apply = '--apply' in sys.argv
    products = MG.api('GET', 'products.json?limit=250&status=active')['products']
    skus = [v['sku'] for p in products for v in p['variants'] if v.get('sku')]
    print(f'{len(products)} active products, {len(skus)} SKU-carrying variants')
    print('reading live CJ costs...')
    costs = MG.live_cj_costs(skus)
    print(f'{len(costs)} SKUs priced by CJ\n')

    rows, unknown, kits = [], [], []
    for p in sorted(products, key=lambda x: x['title']):
        if p.get('product_type') == 'Bundles & Kits':
            kits.append(p)
            continue
        for v in p['variants']:
            sku = v.get('sku')
            if not sku or sku not in costs:
                if sku:
                    unknown.append((p['title'], v['title'], sku))
                continue
            vid, cost = costs[sku]
            fr = MG.best_freight(vid, freight_floor.origin_for(sku), sku)
            if not fr.get('answered'):
                unknown.append((p['title'], v['title'], sku))
                continue
            freight, duty = fr['price'], duty_for(sku)
            price = float(v['price'])
            rows.append(dict(
                product=p['title'], pid=p['id'], vid=v['id'], variant=v['title'],
                sku=sku, price=price, cost=cost, freight=freight, duty=duty,
                margin=MG.margin_at(price, cost, freight, duty) * 100,
                ideal=sane(MG.floor_price(cost, freight, duty,
                                          TARGET + BUFFER_PCT))))

    by_product = {}
    for r in rows:
        by_product.setdefault(r['pid'], []).append(r)

    plan = []
    for pid, rs in by_product.items():
        new = max(r['ideal'] for r in rs)
        cur = max(r['price'] for r in rs)
        if cur - new >= MIN_DROP:
            plan.append(dict(
                pid=pid, title=rs[0]['product'], cur=cur, new=new,
                drop=round(cur - new, 2),
                margin_now=min(r['margin'] for r in rs),
                margin_new=min(MG.margin_at(new, r['cost'], r['freight'],
                                            r['duty']) * 100 for r in rs),
                variants=rs))
    plan.sort(key=lambda x: -x['drop'])

    print(f"{'product':40}{'now':>8}{'new':>9}{'save':>8}{'margin now':>12}{'new':>8}")
    print('-' * 86)
    for x in plan:
        print(f"{x['title'][:38]:40}{x['cur']:>8.2f}{x['new']:>9.2f}{x['drop']:>8.2f}"
              f"{x['margin_now']:>11.1f}%{x['margin_new']:>7.1f}%")
    print(f"\n{len(plan)} product(s) can come down. "
          f"Total per-unit reduction ${sum(x['drop'] for x in plan):.2f}")

    held = [r for r in rows if r['pid'] not in {x['pid'] for x in plan}]
    if held:
        names = sorted({r['product'] for r in held})
        print(f'\n{len(names)} product(s) already at or near the target, unchanged:')
        for n in names[:12]:
            m = min(r['margin'] for r in held if r['product'] == n)
            print(f'   = {n[:44]:46} {m:.1f}%')
    if unknown:
        print(f'\n{len(unknown)} variant(s) CJ would not price, left alone '
              f'(UNKNOWN, not a finding)')
    if kits:
        print(f'\n{len(kits)} kit(s) NOT repriced here (price is bound to '
              f'compare_at in kit_colorways.py):')
        for k in kits:
            print(f"   - {k['title'][:40]:42} ${k['variants'][0]['price']}")

    out = os.path.join(ROOT, 'docs', 'qa', 'price-review.json')
    json.dump(plan, open(out, 'w', encoding='utf-8'), indent=1, default=str)
    print(f'\nlog -> {out}')

    if not apply:
        print('Report only. Use --apply to lower these.')
        return 0

    print('\napplying...')
    for x in plan:
        for r in x['variants']:
            MG.api('PUT', f"variants/{r['vid']}.json",
                   {'variant': {'id': r['vid'], 'price': f"{x['new']:.2f}"}})
        print(f"  {x['title'][:40]:42} ${x['cur']:.2f} -> ${x['new']:.2f}")

    # Re-fetch the SPECIFIC variant by id. The product list endpoint serves a
    # stale embedded variants array for minutes after a write that landed.
    print('\n--- verify each variant by ID ---')
    bad = n = 0
    for x in plan:
        for r in x['variants']:
            n += 1
            got = MG.api('GET', f"variants/{r['vid']}.json")['variant']['price']
            if abs(float(got) - x['new']) > 0.001:
                bad += 1
                print(f"  ! {x['title'][:34]} {r['variant']}: ${got}")
    print(f'{n - bad}/{n} variants confirmed at the new price')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
