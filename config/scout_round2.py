#!/usr/bin/env python3
"""Sourcing round 2: cheap toys, enrichment and travel kit components, and a
possible upgrade for the hair remover mitt.

Reuses scout.py's pipeline: category scan -> name/listedNum prefilter ->
economics() (real freight, stock summed correctly, min viable price at the 50%
floor). Everything prints as a table per slot; `need` is the minimum retail
price that holds the floor, which is the number that decides if a "cheap toy"
is actually cheap.

Slots and what qualifies:
  cheap-toys   need <= 13 so it can retail at 9.99-12.99
  roller       reusable pet hair remover roller (furniture story, video-friendly)
  treat-toy    treat dispensing / puzzle / snuffle enrichment
  bottle       portable dog water bottle
  collapsible  folding travel bowl
  pouch        treat pouch
"""
import json, re, sys
sys.path.insert(0, 'config')
import cj_api
from scout import scan, prefilter, economics, TOY_CATEGORIES, GROOM_CATEGORIES, PUPPY_CATEGORIES

TRAVEL_CATEGORIES = {
    'Bowls': '2410110341061612000',
    'Hair Removers & Combs': '2410110354491625800',
}


def keyword_scan(keyword, pages=3):
    seen = {}
    for pg in range(1, pages + 1):
        r = cj_api.call('/product/list',
                        {'productNameEn': keyword, 'pageSize': 20, 'pageNum': pg})
        lst = ((r.get('data') or {}).get('list') or [])
        if not lst:
            break
        for p in lst:
            p['_cat'] = keyword
            seen.setdefault(p.get('productSku'), p)
    return list(seen.values())


def run_slot(label, rows, extra=None, top=6, need_cap=None):
    hits = prefilter(rows, extra=extra)
    print(f'\n===== {label}: {len(hits)} candidates after prefilter =====')
    out = []
    for p in hits[:top]:
        spu = p.get('productSku')
        try:
            e = economics(spu)
        except Exception as exc:
            print(f'  {spu} econ failed: {str(exc)[:60]}'); continue
        if not e:
            continue
        e['listed'] = p.get('listedNum')
        flag = ''
        if need_cap and e['need'] > need_cap:
            flag = f'  << over {need_cap} cap'
        if e['stock'] < 800:
            flag += '  << low stock'
        print(f"  {spu}  listed={e['listed']:>5} cost=${e['cost']:<6} "
              f"freight=${e['freight']:<6} stock={e['stock']:>6} "
              f"need=${e['need']:.2f}  imgs={e['images']}  {e['name'][:38]}{flag}")
        out.append(e)
    return out


def main():
    results = {}

    toys = scan(TOY_CATEGORIES, pages=3)
    results['cheap_toys'] = run_slot(
        'CHEAP TOYS (retail 9.99-12.99)', toys, top=12, need_cap=13)

    groom = scan({'Hair Removers & Combs': GROOM_CATEGORIES['Hair Removers & Combs']}, pages=3)
    results['roller'] = run_slot(
        'HAIR REMOVER ROLLER', groom,
        extra=re.compile(r'roller|lint|reusable.*remov', re.I), top=6)

    results['treat_toy'] = run_slot(
        'TREAT DISPENSER / ENRICHMENT', toys,
        extra=re.compile(r'treat|dispens|puzzle|iq\b|snuffle|slow.*feed|lick', re.I), top=8)

    results['bottle'] = run_slot(
        'DOG WATER BOTTLE', keyword_scan('dog water bottle portable'), top=6)

    results['collapsible'] = run_slot(
        'COLLAPSIBLE TRAVEL BOWL', keyword_scan('collapsible dog bowl'), top=6)

    results['pouch'] = run_slot(
        'TREAT POUCH', keyword_scan('dog treat pouch training'), top=6)

    with open('config/scout_round2_results.json', 'w', encoding='utf-8') as fh:
        json.dump(results, fh, indent=1)
    print('\nresults -> config/scout_round2_results.json')


if __name__ == '__main__':
    main()
