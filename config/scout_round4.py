#!/usr/bin/env python3
"""Sourcing round 4: bolster toys (cheap + social-video-friendly), grooming,
and comfort/health by ~5 items each.

New selection lens on top of the standing rules (50% floor with real freight,
<1kg from China, stock depth, listedNum rank, eyeball-the-images gate):
products must DEMO well in short-form video - motion, interaction, a visible
before/after, or a surprise. Static commodities don't earn clicks.
"""
import json, re, sys
sys.path.insert(0, 'config')
import cj_api
from scout import economics, REJECT, CAT_ONLY

CATS = {
    'toys': {
        'Chase': '2410110339311602900', 'Chew': '2410110339451623300',
        'Training': '2410110340031614900', 'Sound': '2410110340161623400',
        'Toy Set': '2410110340411608400', 'Plush': '2410110340531618900',
    },
    'trainers': {'Trainers': '2410110342161616300'},
    'groom_hair': {'Hair Removers & Combs': '2410110354491625800'},
    'groom_nail': {'Nail Polishers': '2410110355021623200'},
    'groom_shower': {'Shower Products': '2410110355151622300'},
    'groom_towel': {'Towels': '2410110355321622400'},
    'bowls': {'Pet Bowls': '2410110341061612000'},
    'drinking': {'Drinking Tools': '2410110341331606800'},
    'feeding': {'Feeding Tools': '2410110341451628800'},
    'mats': {'Pet Mats': '2410110357391611900'},
    'blankets': {'Blankets & Quilts': '2410110358191601900'},
}

# motion / interaction / transformation - what reads on camera
SOCIAL = re.compile(
    r'interactive|electric|automatic|smart|self[- ]?(play|moving|rolling)|'
    r'mov(ing|e)|roll|jump|danc|walk|flip|flap|launch|shoot|chas|bounc|crawl|'
    r'wiggle|vibrat|rotat|spin|usb|recharge|suction|tug|crab|duck|laser|'
    r'wicked|crazy|magic|glow|led|light', re.I)


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


def pick(rows, name_re=None, price_max=None, min_listed=25, allow_nondog=False, top=10):
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
        e['social'] = bool(SOCIAL.search(str(p.get('productNameEn') or '')))
        flag = ' [SOCIAL]' if e['social'] else ''
        if need_cap and e['need'] > need_cap: flag += f' <<over cap {need_cap}'
        if e['stock'] < 800: flag += ' <<low stock'
        print(f"  {spu}  listed={e['listed']:>5} cost=${e['cost']:<6} fr=${e['freight']:<6} "
              f"w={e['weight']!s:>5} stock={e['stock']:>6} need=${e['need']:.2f} "
              f"imgs={e['images']} {e['name'][:40]}{flag}")
        res.append(e)
    return res


def main():
    out = {}

    toys = scan(CATS['toys'], pages=7) + scan(CATS['trainers'], pages=4)
    out['toys_social'] = econ_table(
        'TOYS: social-motion names, cost <= 3.5',
        pick(toys, name_re=SOCIAL, price_max=3.5, min_listed=25, top=16), need_cap=20)
    out['toys_cheap'] = econ_table(
        'TOYS: any cheap (cost <= 2.0), catch what the regex missed',
        pick(toys, price_max=2.0, min_listed=40, top=10), need_cap=17)

    groom = (scan(CATS['groom_hair'], pages=6) + scan(CATS['groom_nail'], pages=3)
             + scan(CATS['groom_shower'], pages=5) + scan(CATS['groom_towel'], pages=3))
    out['grooming'] = econ_table(
        'GROOMING: cost <= 12',
        pick(groom, price_max=12, min_listed=25, allow_nondog=True, top=18), need_cap=46)

    comfort = (scan(CATS['bowls'], pages=4) + scan(CATS['drinking'], pages=4)
               + scan(CATS['feeding'], pages=4) + scan(CATS['mats'], pages=5)
               + scan(CATS['blankets'], pages=4))
    out['comfort'] = econ_table(
        'COMFORT & HEALTH: cost <= 12, weight rule bites here',
        pick(comfort, price_max=12, min_listed=25, top=18), need_cap=48)
    out['comfort_named'] = econ_table(
        'COMFORT: snuffle/calming/heartbeat/fountain names',
        pick(comfort + toys,
             name_re=re.compile(r'snuffle|sniff|calming|heartbeat|anxiety|fountain|puzzle.*feed|lick.*mat', re.I),
             min_listed=10, top=10), need_cap=48)

    with open('config/scout_round4_results.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, default=str)
    print('\nsaved -> config/scout_round4_results.json')


if __name__ == '__main__':
    main()
