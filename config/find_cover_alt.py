#!/usr/bin/env python3
"""Find a replacement for the Waterproof Furniture Cover.

The incumbent (CJBQ3005963, $22.99, US warehouse) has three problems:
  * CJ quotes $0.00 freight on every carrier, so its true cost is a guess
  * only 50 units in stock, the thinnest in the catalogue
  * at $76 it clears the floor by 0.4pp, with no room for a freight surprise

A replacement has to beat it on the thing that actually caused the trouble:
verifiable freight. Candidates are scored on real quotes, real stock, and
whether they clear 50% at a price the category will bear.

    python config/find_cover_alt.py
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE, landed, FLAT, PCT, SALES_TAX_AVG

FLOOR = 0.50
# The category tops out around here; above it the product stops selling.
CEILING = 60.00
MAX_WEIGHT_G = 1000        # sourcing rule: reject >1kg from China
MIN_STOCK = 500

QUERIES = [
    'dog bed cover waterproof',
    'pet sofa cover waterproof',
    'dog blanket waterproof',
    'pet furniture protector',
    'dog couch cover',
    'waterproof pet mat blanket',
]

RELEVANT = ('dog', 'pet', 'puppy', 'cat')
KIND = ('cover', 'blanket', 'protector', 'throw', 'mat')
REJECT = ('clothes', 'jacket', 'raincoat', 'shoe', 'collar', 'leash', 'toy',
          'bowl', 'carrier', 'diaper', 'grooming', 'nail', 'car seat', 'seat cover')


def fee_rate():
    return PCT * (1 + SALES_TAX_AVG)


def evaluate(spu):
    """Return a dict of the economics, or None if unusable."""
    r = cj_api.call('/product/query', {'productSku': spu})
    d = r.get('data') or {}
    variants = d.get('variants') or []
    if not variants:
        return None
    v = variants[0]
    try:
        cost = float(str(v.get('variantSellPrice')).split('-')[0])
    except (TypeError, ValueError):
        return None
    weight = v.get('variantWeight') or d.get('productWeight') or 0
    vid = v.get('vid')

    st = cj_api.call('/product/stock/queryBySku', {'sku': v.get('variantSku')})
    stock = 0
    for w in (st.get('data') or []):
        for s in (w.get('stock') or []):
            stock += (s.get('inventory') or 0) + (s.get('factoryInventory') or 0)
        if not (w.get('stock') or []):
            stock += w.get('totalInventoryNum') or 0

    us = str(v.get('variantSku') or '').startswith('CJBQ')
    start = 'US' if us else 'CN'
    fr = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    freight, carrier, aging, estimated = freight_floor.resolve(fr.get('data'))

    duty = DUTY_PCT_US_WAREHOUSE if us else DUTY_PCT
    need = (landed(cost, freight, duty) + FLAT) / (1 - fee_rate() - FLOOR)

    return {'spu': spu, 'name': str(d.get('productNameEn'))[:60], 'cost': cost,
            'weight': weight, 'stock': stock, 'freight': freight,
            'carrier': str(carrier)[:22], 'aging': aging, 'estimated': estimated,
            'need': need, 'origin': start}


def main():
    seen, candidates = set(), []
    for q in QUERIES:
        r = cj_api.call('/product/list', {'productNameEn': q, 'pageSize': 20, 'pageNum': 1})
        for p in ((r.get('data') or {}).get('list') or []):
            name = str(p.get('productNameEn') or '').lower()
            spu = p.get('productSku')
            if not spu or spu in seen:
                continue
            if not any(k in name for k in RELEVANT):
                continue
            if not any(k in name for k in KIND):
                continue
            if any(k in name for k in REJECT):
                continue
            seen.add(spu)
            candidates.append(p)

    print(f'{len(candidates)} on-theme candidate(s) from {len(QUERIES)} queries\n')
    rows = []
    for p in candidates:
        e = evaluate(p['productSku'])
        if not e:
            continue
        rows.append(e)

    rows.sort(key=lambda e: (e['estimated'], e['need']))
    print(f'{"SPU":<15}{"cost":>7}{"frt":>8}{"stock":>9}{"wt(g)":>8}{"min price":>11}  carrier / name')
    for e in rows:
        est = '~' if e['estimated'] else ' '
        ok = ('OK ' if (not e['estimated'] and e['need'] <= CEILING
                        and e['stock'] >= MIN_STOCK
                        and (e['origin'] == 'US' or (e['weight'] or 0) <= MAX_WEIGHT_G))
              else '   ')
        print(f'{ok}{e["spu"]:<15}{e["cost"]:>7.2f}{est}{e["freight"]:>7.2f}'
              f'{e["stock"]:>9}{str(e["weight"] or "?"):>8}{e["need"]:>11.2f}  '
              f'{e["carrier"]} | {e["name"][:40]}')

    print('\nOK = real freight quote, clears 50%% under $%.0f, stock >= %d, '
          'within weight rule' % (CEILING, MIN_STOCK))
    print('~  = freight was estimated, not quoted (same defect as the incumbent)')


if __name__ == '__main__':
    main()
