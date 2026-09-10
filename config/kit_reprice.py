#!/usr/bin/env python3
"""What each kit should cost at the 20% floor, and what its compare_at becomes.

Kits were the worst-priced things in the store: the Travel Kit ran 56.9% to
62.5% margin against a 20% standard, because kit prices were set by an older
30% floor and then never revisited when the singles moved.

TWO NUMBERS PER KIT, AND THEY MUST MOVE TOGETHER.

  price       the max of what every VARIANT of that kit needs to clear the
              floor. Taking the average or the cheapest colorway would put the
              dearest colorway under water, and a kit sells at one price.
  compare_at  the honest sum of buying every component separately at its CURRENT
              live retail. It has to be recomputed here because the singles just
              came down: leaving the old compare_at would advertise a saving
              that no longer exists, which is a price representation and an FTC
              exposure, not just untidiness.

This only REPORTS. `config/kit_colorways.py` is the source of truth for both
numbers and is edited by hand from this output, then applied with
`rebuild_kits.py --reprice-only`. That indirection is deliberate: a composition
change IS a price change, and routing both through one file is what stops them
drifting apart.

    python config/kit_reprice.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import kit_margins as KM                     # noqa: E402
import cj_api                                # noqa: E402
import freight_floor                         # noqa: E402
from pricing import (DUTY_PCT, DUTY_PCT_US_WAREHOUSE, landed, FLAT, PCT,
                     SALES_TAX_AVG)          # noqa: E402

BUFFER = 0.02   # aim 2 points above the floor; see price_review.py


def main():
    fee_rate = PCT * (1 + SALES_TAX_AVG)
    target = KM.FLOOR + BUFFER
    prods = KM.api('products.json?limit=250&status=active')['products']
    kits = [p for p in prods if not any(v.get('sku') for v in p['variants'])]
    retail = {p['title'].replace('Wagvive ', ''): float(p['variants'][0]['price'])
              for p in prods if any(v.get('sku') for v in p['variants'])}

    print(f'floor {KM.FLOOR:.0%} + {BUFFER:.0%} buffer = target {target:.0%}\n')
    print(f"{'kit':28}{'now':>8}{'needs':>9}{'->set':>8}{'compare_at':>12}"
          f"{'worst margin now':>18}")
    print('-' * 84)
    blocked = []

    for k in sorted(kits, key=lambda x: x['title']):
        d = KM.gql(KM.BUNDLE_Q, {'id': f"gid://shopify/Product/{k['id']}"})
        pv = (d.get('data') or {}).get('product')
        if not pv:
            print(f"{k['title']}: no bundle data"); continue
        worst_need, worst_margin, comp_names = 0.0, 999.0, set()
        cur = float(pv['variants']['nodes'][0]['price'])
        for var in pv['variants']['nodes']:
            price = float(var['price'])
            comps = var['productVariantComponents']['nodes']
            if not comps:
                continue
            goods, items, china, grams = 0.0, [], False, 0.0
            unresolved = []
            for c in comps:
                sku = c['productVariant']['sku']
                vid, cost, wt = KM.cj_lookup(sku)
                if cost is None:
                    # NEVER SKIP. Dropping an unresolved component takes its
                    # cost and its weight out of the totals, so the kit reads
                    # cheaper and lighter than it is and this tool recommends a
                    # price that is too LOW. That is exactly what happened on
                    # 2026-09-09: run minutes after the Calm & Comfort rebuild,
                    # with the swapped component not yet resolving, it advised
                    # $64.00 for a kit whose true margin at that price is 19.2%
                    # against a 20% floor.
                    unresolved.append(sku)
                    continue
                goods += cost * c['quantity']
                grams += (wt or 0) * c['quantity']
                items.append({'quantity': c['quantity'], 'vid': vid})
                comp_names.add(c['productVariant']['product']['title']
                               .replace('Wagvive ', ''))
                if not str(sku).startswith('CJBQ'):
                    china = True
            if unresolved:
                # Refuse to advise a price from a partial bill of materials.
                # The recommendation would be too LOW, and this tool's whole
                # output is a price somebody then sets.
                blocked.append((k['title'], unresolved))
                continue
            start = 'CN' if china else 'US'
            r = cj_api.call('/logistic/freightCalculate', payload={
                'startCountryCode': start, 'endCountryCode': 'US',
                'products': items})
            combined = r.get('data') or []
            if combined:
                # Weight passed, for the same reason kit_margins.py passes it:
                # without it resolve() cannot run its weight-relative
                # placeholder test and falls back to the flat $11.00 bulky-item
                # constant, which flatters the kit. And when the quote IS
                # rejected, a kit falls back to the invoice-fitted ONE-PARCEL
                # line, not resolve()'s single-item estimate - otherwise the two
                # branches below model the same box two different ways.
                freight, _, _, est = freight_floor.resolve(combined, '', grams)
                if est:
                    freight = freight_floor.combined_estimate(grams) or freight
            else:
                # ONE parcel, estimated from combined weight against the line
                # fitted to real CJ invoices. Summing per-item parcels charges
                # the fixed parcel cost once per item and overstated the Dog
                # Enrichment Kit by 71% ($25.42 modelled vs $14.85 billed).
                freight = freight_floor.combined_estimate(grams) or 0.0
            duty = DUTY_PCT if china else DUTY_PCT_US_WAREHOUSE
            base = landed(goods, freight, duty)
            need = (base + FLAT) / (1 - fee_rate - target)
            m = (price - (base + fee_rate * price + FLAT)) / price * 100
            worst_need = max(worst_need, need)
            worst_margin = min(worst_margin, m)

        new = float(int(worst_need) + 1)           # kits price in whole dollars
        compare = round(sum(retail.get(n, 0.0) for n in comp_names), 2)
        print(f"{k['title'][:26]:28}{cur:>8.2f}{worst_need:>9.2f}{new:>8.2f}"
              f"{compare:>12.2f}{worst_margin:>17.1f}%")
        missing = [n for n in comp_names if n not in retail]
        if missing:
            print(f"    ! no live retail for {missing} - compare_at is short")

    if blocked:
        print('\nNOT PRICED, a component would not resolve at CJ. A price')
        print('advised from a partial bill of materials would be too LOW:')
        for t, miss in blocked:
            print(f'  ? {t[:34]:36} unresolved: {miss}')
        print('Re-run once CJ answers for them.')

    print('\nEdit config/kit_colorways.py with the ->set and compare_at columns,')
    print('then: python config/rebuild_kits.py --reprice-only --apply')
    return 0


if __name__ == '__main__':
    sys.exit(main())
