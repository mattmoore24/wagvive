#!/usr/bin/env python3
"""
Find Comfort & Health candidates that are actually shippable: light enough that
CJ freight stays near the ~$3 floor, dog-relevant, and in the pet category.

Weight is the binding constraint - the cooling mat (2kg) cost $46 to ship and
the bed (3.75kg) cost $108, which is what killed both.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

PET_CATEGORY = '2409110611570657700'
MAX_WEIGHT_G = 800

QUERIES = [
    'dog cooling bandana', 'pet cooling towel', 'dog cooling collar',
    'dog lick mat', 'pet snuffle mat', 'slow feeder lick pad',
    'collapsible dog bowl', 'dog water bottle travel',
    'dog paw cleaner', 'pet dental brush',
]

DOG_HINT = re.compile(r'\b(dog|pet|puppy|paw|canine)\b', re.I)
NOISE = re.compile(r'(car |kitchen|table|phone|human|baby|necklace|costume|radiator)', re.I)


def low(v):
    """Lowest number in a CJ range string like '27.00-31.00'."""
    m = re.findall(r'[\d.]+', str(v or ''))
    return float(m[0]) if m else None


def main():
    seen = {}
    for q in QUERIES:
        r = cj_api.call('/product/list',
                        {'pageNum': 1, 'pageSize': 40,
                         'categoryId': PET_CATEGORY, 'productName': q})
        d = r.get('data')
        if not isinstance(d, dict):
            print(f'  {q:26} query failed'); continue
        hits = 0
        for p in (d.get('list') or []):
            name = str(p.get('productNameEn') or '')
            wt = low(p.get('productWeight'))
            price = low(p.get('sellPrice'))
            if wt is None or wt > MAX_WEIGHT_G:
                continue
            if not DOG_HINT.search(name) or NOISE.search(name):
                continue
            sku = p.get('productSku')
            if sku in seen:
                continue
            seen[sku] = {'sku': sku, 'pid': p.get('pid'), 'name': name,
                         'weight_g': wt, 'cost': price, 'query': q}
            hits += 1
        print(f'  {q:26} {hits} light dog-relevant hits')

    rows = sorted(seen.values(), key=lambda x: (x['weight_g'] or 0))
    print(f'\n{len(rows)} candidates under {MAX_WEIGHT_G}g\n')
    print('%-58s %-8s %-8s %s' % ('name', 'cost', 'wt(g)', 'sku'))
    for c in rows[:40]:
        n = c['name'][:58].encode('ascii', 'replace').decode()
        print('%-58s $%-7s %-8s %s' % (n, c['cost'], c['weight_g'], c['sku']))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cj_light_candidates.json')
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, indent=2)
    print(f'\n-> {out}')


if __name__ == '__main__':
    main()
