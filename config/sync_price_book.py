#!/usr/bin/env python3
"""Bring price_book.json back in step with live prices and the 20% standard.

WHY THIS IS NEEDED. price_book carries two things per product: the price, and
`floor_margin_pct` - the floor margin_guard enforces. Both were set by the
demand-model optimiser and neither is updated when a price changes by hand.

After the 2026-09-02 store-wide cut the book was badly stale: it still listed
the Talk Button at $16.99 with a 41.7% floor while the live price was $10.99 at
about 24% margin. margin_guard duly reported 68 "breaches" that were nothing of
the kind - products comfortably above the owner's 20% standard but below a
floor set for a price that no longer existed. An alarm that fires on healthy
products is worse than no alarm, because it trains you to ignore it.

WHAT IT DOES
  * price          <- the live price, per variant.
  * floor_margin_pct <- 20.0, the owner's store-wide standard, for every product
    whose worst variant actually clears 20%.
  * products that do NOT clear 20% keep their existing lower floor and are
    listed loudly. Those are real, known thin spots (the Anti-Spill Water Bowl
    runs about 5%), and raising their floor would just make the scheduled job
    fail every six hours without telling anyone anything new. They need a price
    decision, not an alarm.

    python config/sync_price_book.py            # report
    python config/sync_price_book.py --apply
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import margin_guard as MG                    # noqa: E402
import pricing                               # noqa: E402
import freight_floor                         # noqa: E402

STANDARD = 20.0
BOOK = os.path.join(ROOT, 'config', 'price_book.json')


def main():
    apply = '--apply' in sys.argv
    book = json.load(open(BOOK, encoding='utf-8'))
    products = MG.api('GET', 'products.json?limit=250&status=active')['products']
    skus = [v['sku'] for p in products for v in p['variants'] if v.get('sku')]
    print('reading live CJ costs...')
    costs = MG.live_cj_costs(skus)

    updated, thin, missing = [], [], []
    for p in products:
        pid = str(p['id'])
        sku_variants = [v for v in p['variants'] if v.get('sku')]
        if not sku_variants:
            continue                                   # kits: priced elsewhere
        worst = None
        for v in sku_variants:
            sku = v['sku']
            if sku not in costs:
                continue
            vid, cost = costs[sku]
            fr = MG.best_freight(vid, freight_floor.origin_for(sku), sku)
            if not fr.get('answered'):
                continue
            duty = (pricing.DUTY_PCT_US_WAREHOUSE
                    if freight_floor.origin_for(sku) == 'US' else pricing.DUTY_PCT)
            m = MG.margin_at(float(v['price']), cost, fr['price'], duty) * 100
            worst = m if worst is None else min(worst, m)
        if worst is None:
            missing.append(p['title'])
            continue

        entry = book.get(pid, {'title': p['title']})
        old_price = entry.get('price')
        old_floor = entry.get('floor_margin_pct')
        entry['title'] = p['title']
        entry['price'] = float(sku_variants[0]['price'])
        entry['variants'] = {v['sku']: float(v['price']) for v in sku_variants}
        if worst >= STANDARD:
            entry['floor_margin_pct'] = STANDARD
        else:
            thin.append((p['title'], worst, old_floor))
        book[pid] = entry
        if old_price != entry['price'] or old_floor != entry.get('floor_margin_pct'):
            updated.append((p['title'], old_price, entry['price'],
                            old_floor, entry.get('floor_margin_pct'), worst))

    print(f"\n{'product':38}{'price':>16}{'floor':>16}{'worst margin':>14}")
    print('-' * 86)
    for t, op, np_, of, nf, w in sorted(updated):
        print(f'{t[:36]:38}{str(op):>7} -> {np_:<6}{str(of):>7} -> {str(nf):<6}{w:>13.1f}%')
    print(f'\n{len(updated)} entry(ies) change')

    if thin:
        print(f'\n{len(thin)} product(s) BELOW the {STANDARD:.0f}% standard. Floor left '
              f'as-is so the scheduled job stays honest rather than permanently red.')
        print('These need a PRICE decision, not an alarm:')
        for t, w, of in sorted(thin, key=lambda x: x[1]):
            print(f'   ! {t[:40]:42} {w:5.1f}%  (floor kept at {of})')
    if missing:
        print(f'\n{len(missing)} product(s) CJ would not price, left untouched')

    if not apply:
        print('\nReport only. Use --apply.')
        return 0
    json.dump(book, open(BOOK, 'w', encoding='utf-8'), indent=1)
    print(f'\nwrote {BOOK} ({len(book)} products)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
