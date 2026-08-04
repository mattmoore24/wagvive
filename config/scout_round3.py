#!/usr/bin/env python3
"""Sourcing round 3, slot-specific.

Round 2 lessons: /product/list has no working keyword search, rollers are not
named "dog" anything, and cheap toys only exist where the item is light enough
that freight collapses. So: scan the right categories, filter on list-row price
and listedNum first (cheap), and only then spend API budget on economics().
"""
import json, re, sys
sys.path.insert(0, 'config')
import cj_api
from scout import economics, REJECT, CAT_ONLY

CATS = {
    'drinking': {'Pet Drinking Tools': '2410110341331606800'},
    'bowls': {'Pet Bowls': '2410110341061612000'},
    'feeding': {'Pet Feeding Tools': '2410110341451628800'},
    'outdoor_bags': {'Pet Bags (Outdoor)': '2410110342571606700'},
    'trainers': {'Trainers': '2410110342161616300'},
    'hair': {'Hair Removers & Combs': '2410110354491625800'},
    'toys': {
        'Chase': '2410110339311602900', 'Chew': '2410110339451623300',
        'Training': '2410110340031614900', 'Sound': '2410110340161623400',
        'Toy Set': '2410110340411608400', 'Plush': '2410110340531618900',
    },
}


def scan(categories, pages):
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


def listprice(p):
    try:
        return float(str(p.get('sellPrice') or p.get('productSellPrice') or '999').split('-')[0])
    except ValueError:
        return 999.0


def pick(rows, name_re=None, price_max=None, min_listed=30, allow_nondog=False, top=6):
    out = []
    for p in rows:
        name = str(p.get('productNameEn') or '')
        if not name or REJECT.search(name):
            continue
        if not allow_nondog and CAT_ONLY.search(name) and not re.search(r'\bdog|puppy', name, re.I):
            continue
        if (p.get('listedNum') or 0) < min_listed:
            continue
        if name_re and not name_re.search(name):
            continue
        if price_max and listprice(p) > price_max:
            continue
        out.append(p)
    out.sort(key=lambda p: -(p.get('listedNum') or 0))
    return out[:top]


def econ_table(label, cands, need_cap=None):
    print(f'\n===== {label} =====')
    res = []
    for p in cands:
        spu = p.get('productSku')
        try:
            e = economics(spu)
        except Exception as exc:
            print(f'  {spu} econ failed: {str(exc)[:50]}'); continue
        if not e:
            continue
        e['listed'] = p.get('listedNum')
        flag = ''
        if need_cap and e['need'] > need_cap: flag = f' <<over cap {need_cap}'
        if e['stock'] < 800: flag += ' <<low stock'
        print(f"  {spu}  listed={e['listed']:>5} cost=${e['cost']:<6} fr=${e['freight']:<6} "
              f"stock={e['stock']:>6} need=${e['need']:.2f} imgs={e['images']} {e['name'][:36]}{flag}")
        res.append(e)
    return res


def main():
    out = {}

    toys = scan(CATS['toys'], pages=5)
    cheap = pick(toys, price_max=2.2, min_listed=25, top=10)
    out['cheap_toys'] = econ_table('CHEAP TOYS (list cost <= 2.2)', cheap, need_cap=16)

    hair = scan(CATS['hair'], pages=4)
    out['roller'] = econ_table('HAIR ROLLER (name-based, non-dog names allowed)',
        pick(hair, name_re=re.compile(r'roller|lint', re.I), min_listed=20, allow_nondog=True, top=6))

    feed = scan(CATS['feeding'], pages=4) + toys
    out['treat_toy'] = econ_table('TREAT DISPENSER / ENRICHMENT',
        pick(feed, name_re=re.compile(r'treat|dispens|puzzle|iq\b|snuffle|leak|lick|slow', re.I),
             min_listed=25, top=8))

    drink = scan(CATS['drinking'], pages=4)
    out['bottle'] = econ_table('DOG WATER BOTTLE (portable)',
        pick(drink, name_re=re.compile(r'bottle|portable|travel|outdoor', re.I), min_listed=20, top=6))

    bowls = scan(CATS['bowls'], pages=4)
    out['collapsible'] = econ_table('COLLAPSIBLE BOWL',
        pick(bowls, name_re=re.compile(r'collaps|fold|silicone.*travel|travel.*bowl', re.I),
             min_listed=15, allow_nondog=True, top=6))

    bags = scan(CATS['outdoor_bags'], pages=4) + scan(CATS['trainers'], pages=3)
    out['pouch'] = econ_table('TREAT POUCH',
        pick(bags, name_re=re.compile(r'treat.*(pouch|bag)|snack.*(pouch|bag)|training.*(pouch|bag)|waist', re.I),
             min_listed=15, allow_nondog=True, top=6))

    with open('config/scout_round3_results.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)
    print('\nsaved -> config/scout_round3_results.json')


if __name__ == '__main__':
    main()
