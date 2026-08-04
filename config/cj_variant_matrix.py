#!/usr/bin/env python3
"""
Pull the full variant matrix for every connected Wagvive SKU from the CJ API
and cache it to config/cj_variants.json.

This is the source of truth for the variant build (task 1), the stock sync
(task 2) and the landed-cost / margin rule (task 4) - variant weight is what
the freight calculator needs.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'config', 'cj_variants.json')

# Shopify product id -> (label, CJ SPU) for the 8 connected SKUs.
SKUS = {
    10456336990497: ('Self-Cleaning Slicker Brush',   'CJMY1952185'),
    10456337056033: ('Grooming & Shedding Gloves',    'CJYD2332008'),
    10456337154337: ('Ear & Teeth Cleaning Wipes',    'CJYD2169796'),
    10456337318177: ('Quiet Electric Nail Grinder',   'CJGY2008357'),
    10456337383713: ('Cooling Comfort Mat',           'CJGY1038962'),
    10456337547553: ('Anti-Spill Floating Water Bowl', 'CJGY1025454'),
    10456337613089: ('Slow Feeder Bowl',              'CJGY1748465'),
    10456337711393: ('Orthopedic Comfort Bed',        'CJYD2363003'),
}


def num(v):
    try:
        return float(str(v).split('-')[0])
    except (TypeError, ValueError):
        return None


def main():
    out = {}
    for pid, (label, spu) in SKUS.items():
        res = cj_api.call('/product/query', {'productSku': spu})
        d = res.get('data')
        if not d:
            print(f'{label:32} FAILED  {json.dumps(res)[:140]}')
            continue
        variants = []
        for v in (d.get('variants') or []):
            variants.append({
                'vid': v.get('vid'),
                'sku': v.get('variantSku'),
                'key': (v.get('variantKey') or '').strip(),
                'cost': num(v.get('variantSellPrice')),
                'weight_g': num(v.get('variantWeight')),
                'length': v.get('variantLength'),
                'width': v.get('variantWidth'),
                'height': v.get('variantHeight'),
            })
        out[str(pid)] = {
            'label': label, 'spu': spu, 'pid': d.get('pid'),
            'name_en': d.get('productNameEn'),
            'variants': variants,
        }
        costs = [v['cost'] for v in variants if v['cost'] is not None]
        rng = f'${min(costs):.2f}-{max(costs):.2f}' if costs else 'n/a'
        print(f'{label:32} {spu:14} variants={len(variants):<3} cost {rng}')

    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=2)
    total = sum(len(p['variants']) for p in out.values())
    print(f'\n{len(out)} products, {total} variants total -> config/cj_variants.json')


if __name__ == '__main__':
    main()
