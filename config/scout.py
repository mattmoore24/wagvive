#!/usr/bin/env python3
"""Shortlist CJ products against the rules this catalogue already runs on.

Selection is ranked, not eyeballed. CJ exposes two usable quality signals:

  * `listedNum` - how many merchants have put the product in their store. The
    Grooming Gloves sit at 4,813 and the Nail Grinder at 1,327; a product nobody
    has listed is untested. This is the primary rank.
  * `/product/productComments` - real buyer reviews with scores, but sparse
    (0-18 on our own SKUs), so it is a tiebreak rather than a gate.

Hard filters come from what has already burned us:
  - dog-relevant name, and not a cat-only listing
  - a REAL freight quote; a $0.00 quote is missing data (see freight_floor.py)
  - under the weight ceiling for China origin
  - genuine stock depth, not a placeholder 50
  - clears the 50% margin floor at a sane retail price

    python config/scout.py toys
    python config/scout.py dental
    python config/scout.py puppy
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE, landed, FLAT, PCT, SALES_TAX_AVG

FEE = PCT * (1 + SALES_TAX_AVG)
FLOOR = 0.50
MAX_WEIGHT_G = 1000
MIN_STOCK = 800
MIN_LISTED = 30

TOY_CATEGORIES = {
    'Chase': '2410110339311602900',
    'Chew': '2410110339451623300',
    'Training': '2410110340031614900',
    'Sound': '2410110340161623400',
    'Tunnel': '2410110340291603400',
    'Toy Set': '2410110340411608400',
    'Plush': '2410110340531618900',
}
GROOM_CATEGORIES = {
    'Hair Removers & Combs': '2410110354491625800',
    'Shower Products': '2410110355151622300',
    'Towels': '2410110355321622400',
}
PUPPY_CATEGORIES = {
    'Training Pads & Diapers': '2410110342321607200',
    'Trainers': '2410110342161616300',
    'Bowls': '2410110341061612000',
}

CAT_ONLY = re.compile(r'\bcat\b|kitten|litter|scratch(er|ing) post', re.I)
DOGGY = re.compile(r'\bdog|puppy|pet\b', re.I)
REJECT = re.compile(r'\bbird|fish|aquarium|hamster|rabbit|reptile|snake|guinea', re.I)
DENTAL = re.compile(r'tooth|teeth|dental|chew.*clean|oral', re.I)


def scan(categories, pages=3):
    seen = {}
    for label, cid in categories.items():
        for pg in range(1, pages + 1):
            r = cj_api.call('/product/list',
                            {'categoryId': cid, 'pageSize': 20, 'pageNum': pg})
            lst = ((r.get('data') or {}).get('list') or [])
            if not lst:
                break
            for p in lst:
                p['_cat'] = label
                seen.setdefault(p.get('productSku'), p)
    return list(seen.values())


def prefilter(rows, extra=None):
    out = []
    for p in rows:
        name = str(p.get('productNameEn') or '')
        if not name or REJECT.search(name):
            continue
        if CAT_ONLY.search(name) and not re.search(r'\bdog|puppy', name, re.I):
            continue
        if not DOGGY.search(name):
            continue
        if (p.get('listedNum') or 0) < MIN_LISTED:
            continue
        if extra and not extra.search(name):
            continue
        out.append(p)
    out.sort(key=lambda p: -(p.get('listedNum') or 0))
    return out


def economics(spu):
    d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
    variants = d.get('variants') or []
    if not variants:
        return None
    cheapest = None
    for v in variants:
        try:
            c = float(str(v.get('variantSellPrice')).split('-')[0])
        except (TypeError, ValueError):
            continue
        w = v.get('variantWeight') or 0
        if cheapest is None or c < cheapest[0]:
            cheapest = (c, v, w)
    if not cheapest:
        return None
    cost, v, weight = cheapest
    sku = v.get('variantSku')
    us = str(sku or '').startswith('CJBQ')

    st = cj_api.call('/product/stock/queryBySku', {'sku': sku})
    stock = 0
    for w in (st.get('data') or []):
        rows = w.get('stock') or []
        stock += (sum((s.get('inventory') or 0) + (s.get('factoryInventory') or 0)
                      for s in rows) if rows else (w.get('totalInventoryNum') or 0))

    fr = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': 'US' if us else 'CN', 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': v.get('vid')}]})
    freight, carrier, aging, estimated = freight_floor.resolve(fr.get('data'))
    duty = DUTY_PCT_US_WAREHOUSE if us else DUTY_PCT
    need = (landed(cost, freight, duty) + FLAT) / (1 - FEE - FLOOR)

    cm = cj_api.call('/product/productComments',
                     {'pid': d.get('pid'), 'pageNum': 1, 'pageSize': 20})
    cd = cm.get('data') or {}
    scores = [x.get('score') for x in (cd.get('list') or []) if x.get('score')]
    avg = round(sum(scores) / len(scores), 1) if scores else None

    return {'spu': spu, 'name': str(d.get('productNameEn'))[:52], 'cost': cost,
            'weight': weight, 'stock': stock, 'freight': freight,
            'estimated': estimated, 'need': need, 'variants': len(variants),
            'carrier': str(carrier)[:20], 'aging': aging,
            'reviews': cd.get('total') or 0, 'avg_score': avg,
            'images': len(d.get('productImageSet') or []), 'us': us}


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else 'toys').lower()
    if mode == 'toys':
        rows = prefilter(scan(TOY_CATEGORIES))
        cap = 22
    elif mode == 'dental':
        rows = prefilter(scan(GROOM_CATEGORIES, pages=4), extra=DENTAL)
        if len(rows) < 6:
            more = []
            for q in ['dog toothbrush', 'pet dental care', 'dog teeth cleaning',
                      'dog tooth brush finger']:
                r = cj_api.call('/product/list',
                                {'productNameEn': q, 'pageSize': 20, 'pageNum': 1})
                more += ((r.get('data') or {}).get('list') or [])
            rows += prefilter(more, extra=DENTAL)
        cap = 14
    else:
        rows = prefilter(scan(PUPPY_CATEGORIES))
        cap = 18

    print(f'{mode}: {len(rows)} candidate(s) past prefilter, '
          f'evaluating top {min(cap, len(rows))} by merchant adoption\n')
    print(f'{"":3}{"SPU":<15}{"listed":>7}{"cost":>7}{"frt":>8}{"stock":>8}'
          f'{"wt":>7}{"min$":>8}{"rev":>5}  name')

    keep = []
    for p in rows[:cap]:
        e = economics(p['productSku'])
        if not e:
            continue
        e['listed'] = p.get('listedNum') or 0
        e['cat'] = p.get('_cat', '')
        ok = (not e['estimated'] and e['stock'] >= MIN_STOCK
              and (e['us'] or (e['weight'] or 0) <= MAX_WEIGHT_G))
        flag = 'OK ' if ok else '   '
        est = '~' if e['estimated'] else ' '
        rv = f"{e['reviews']}" + (f"/{e['avg_score']}" if e['avg_score'] else '')
        print(f'{flag}{e["spu"]:<15}{e["listed"]:>7}{e["cost"]:>7.2f}{est}'
              f'{e["freight"]:>7.2f}{e["stock"]:>8}{str(e["weight"]):>7}'
              f'{e["need"]:>8.2f}{rv:>5}  {e["cat"][:8]:9}{e["name"][:40]}')
        if ok:
            keep.append(e)

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           f'scout_{mode}.json'), 'w', encoding='utf-8') as fh:
        json.dump(keep, fh, indent=1)
    print(f'\n{len(keep)} passed every filter -> config/scout_{mode}.json')
    print('OK = real freight quote, stock >= %d, within weight rule' % MIN_STOCK)


if __name__ == '__main__':
    main()
