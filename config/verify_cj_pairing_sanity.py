#!/usr/bin/env python3
"""Does each Shopify product's CJ SKU resolve to a CJ product about the same thing?

WHY. `audit_cj_connections.py` proves every SKU RESOLVES in CJ. It cannot tell you
the SKU resolves to the RIGHT thing. On 2026-07-28 the Anti-Spill Floating Water
Bowl was found silently mapped to a cat bed: a perfectly valid SKU, pointing at
merchandise we do not sell. An order would have shipped the wrong item.

The CJ pairing UI shows this as a "Store Product / CJ Product" table, but it
paginates awkwardly and is CJ telling you about CJ. This checks the same thing
from outside: for every product, resolve its SKU through CJ's API and compare the
CJ product name against our title on meaningful words.

A LOW score is not automatically wrong. Our titles are deliberately not CJ's
("Sneaker Chew Buddy" vs "Dog Toys ... Puppy Chew"), so this ranks rather than
judges, and anything weak is printed in full for a human to read. What it is
really looking for is a product about a completely different ANIMAL or CATEGORY.

    python config/verify_cj_pairing_sanity.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api  # noqa: E402

import urllib.request  # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
D, T, V = (env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'],
           env['SHOPIFY_API_VERSION'])

STOP = {'the', 'and', 'for', 'with', 'dog', 'dogs', 'pet', 'pets', 'wagvive',
        'cat', 'cats', 'small', 'medium', 'large', 'puppy', 'supplies',
        'product', 'products', 'toy', 'toys', 'set', 'pcs', 'new'}

# Words that mean "this is for a different animal or a different job entirely".
#
# These only count when the name ALSO barely overlaps our title. CJ listings
# routinely name every compatible species: the Pet Hair Remover Mitt's CJ name
# says "For Dog Cat Rabbit", which is a correct pairing at 100% word overlap, not
# a mismapping. Flagging it would make this audit cry wolf, which is how a real
# alarm gets ignored.
ALARM = {'cat bed', 'litter box', 'kitten', 'aquarium', 'baby socks',
         'suitcase', 'power bank', 'tattoo', 'kimono'}
ALARM_MAX_SCORE = 0.5


def words(s):
    return {w for w in re.findall(r'[a-z]+', (s or '').lower())
            if len(w) > 3 and w not in STOP}


def main():
    rq = urllib.request.Request(
        f'https://{D}/admin/api/{V}/products.json?limit=250&status=active',
        headers={'X-Shopify-Access-Token': T})
    with urllib.request.urlopen(rq, timeout=120) as r:
        prods = json.loads(r.read().decode())['products']

    seen, rows = set(), []
    for p in prods:
        sku = next((v.get('sku') for v in p['variants'] if v.get('sku')), None)
        if not sku:
            continue                      # kits carry no SKU, by design
        spu = sku[:11]
        if spu in seen:
            continue
        seen.add(spu)

        d = (cj_api.call('/product/query', {'productSku': spu}).get('data') or {})
        cj_name = str(d.get('productNameEn') or '')
        ours = p['title']
        ow, cw = words(ours), words(cj_name)
        overlap = ow & cw
        score = len(overlap) / max(1, len(ow))
        alarm = ([a for a in ALARM if a in cj_name.lower()]
                 if score < ALARM_MAX_SCORE else [])
        rows.append((score, ours, cj_name, spu, sorted(overlap), alarm))

    rows.sort()
    print(f'{len(rows)} distinct CJ SPUs behind the active catalogue\n')
    bad = 0
    for score, ours, cj_name, spu, overlap, alarm in rows:
        flag = '!!' if alarm else ('..' if score < 0.2 else 'OK')
        if alarm:
            bad += 1
        print(f'{flag} {score:4.0%}  {ours.replace("Wagvive ", "")[:34]:34} {spu}')
        if score < 0.34 or alarm:
            print(f'        CJ: {cj_name[:110]}')
            print(f'        shared words: {overlap or "NONE"}')
            if alarm:
                print(f'        !! CJ name mentions {alarm}, a different animal '
                      f'or category')
    print('\n' + '=' * 66)
    if bad:
        print(f'{bad} product(s) resolve to a CJ listing for another animal or '
              f'category. Read them above.')
        return 1
    print('No product resolves to a CJ listing for a different animal or '
          'category.')
    print('Low percentages are expected: our titles are deliberately not CJ\'s.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
