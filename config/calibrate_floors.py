#!/usr/bin/env python3
"""Denominate price_book floors in the units margin_guard actually measures.

build_price_book.py computed floor_margin_pct with the fitted freight curve
and pricing.margin(). The guard measures with the SELECTED carrier's live
quote and a card fee charged on the taxed total. Those two models differ by
more than the 8pt drift buffer on light items (a 30g toothbrush's fitted
freight is a fraction of its cheapest bookable carrier), so a floor computed
in one model false-alarms in the other even when nothing drifted.

This recalibrates: for every variant, measure today's margin exactly the way
margin_guard does, then

  * if a variant clears less than MIN_SINGLE (real money-loss risk once tax
    variance hits), nudge its price to the smallest .99 that clears it, write
    that to the store AND the book;
  * set each product's floor_margin_pct to today's worst variant margin minus
    the drift buffer, clamped at 2% - so the guard fires on genuine cost
    drift, not on model mismatch.

    python config/calibrate_floors.py            # dry run
    python config/calibrate_floors.py --apply    # write store + book
"""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import margin_guard as mg
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE

MIN_SINGLE = 5.0        # %; no single-unit order may risk selling at a loss
BUFFER = 8.0            # pts of drift the floor tolerates before alerting
FLOOR_MIN = 2.0


def charm(x):
    b = int(x)
    return b - 1 + 0.99 if x < b + 0.99 else b + 0.99


def main():
    apply = '--apply' in sys.argv
    path = os.path.join(ROOT, 'config', 'price_book.json')
    book = json.load(open(path, encoding='utf-8'))

    products = mg.api('GET', 'products.json?limit=250&status=active')['products']
    costs = mg.live_cj_costs([v.get('sku') for p in products
                              for v in p['variants']])

    nudges = []
    for p in products:
        entry = book.get(str(p['id']))
        if not entry:
            continue
        margins = []
        for v in p['variants']:
            sku = v.get('sku')
            if not sku or sku not in entry['variants'] or sku not in costs:
                continue
            vid, cost = costs[sku]
            start = 'US' if str(sku).startswith('CJBQ') else 'CN'
            duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
            fr = mg.best_freight(vid, start, sku)
            price = entry['variants'][sku]
            m = mg.margin_at(price, cost, fr['price'], duty) * 100
            if m < MIN_SINGLE:
                new = price
                while (mg.margin_at(new, cost, fr['price'], duty) * 100
                       < MIN_SINGLE and new < 500):
                    new = charm(new + 1.0)
                nudges.append((p['id'], v['id'], sku, entry['title'],
                               price, new))
                entry['variants'][sku] = new
                m = mg.margin_at(new, cost, fr['price'], duty) * 100
            margins.append(m)
        if not margins:
            continue
        old = entry.get('floor_margin_pct')
        entry['floor_margin_pct'] = max(round(min(margins) - BUFFER, 1),
                                        FLOOR_MIN)
        entry['price'] = max(entry['variants'].values())
        t = entry['title'].replace('Wagvive ', '')[:34]
        print(f'  {t:36} worst today {min(margins):5.1f}%   floor '
              f'{old:>5} -> {entry["floor_margin_pct"]}')

    if nudges:
        print(f'\n{len(nudges)} variant(s) under {MIN_SINGLE:.0f}% today, '
              f'nudged in the book:')
        for pid, vid, sku, title, old, new in nudges:
            print(f'  {title.replace("Wagvive ", ""):36} {sku}  '
                  f'${old:.2f} -> ${new:.2f}')

    if not apply:
        print('\nDry run. Use --apply to write store + book.')
        return 0

    for pid, vid, sku, title, old, new in nudges:
        mg.api('PUT', f'variants/{vid}.json',
               {'variant': {'id': vid, 'price': f'{new:.2f}'}})
        time.sleep(0.55)
    json.dump(book, open(path, 'w'), indent=1)
    print(f'\nbook rewritten; {len(nudges)} store price(s) nudged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
