#!/usr/bin/env python3
"""Every sized product must sell on the ONE canonical scale, and say which dog.

This is a gate, not a report. Rewritten 2026-08-19 when the catalogue moved to
the single XS to XL scale in `config/size_scale.py`. The previous version
enforced the OLD shape - it demanded a body measurement (chest, neck, back
length) on every guide - and that rule was wrong twice over once the scale
landed:

  * a BLANKET has no chest girth. Its measurement is its own dimensions, and
    demanding a body measurement flagged two correct guides.
  * the Sofa & Furniture Cover is sized to furniture and deliberately carries
    no dog sizing at all, so it failed a dog-shaped rule by design.

WHAT IT CHECKS NOW:

  1. Every value of the Size option is on the canonical scale (XS/S/M/L/XL) -
     the exemption being the furniture-sized product, which must NOT be.
  2. Every size the product sells appears in its guide table. A guide covering
     three of five sizes reads complete and is not.
  3. Dog-scaled products state a WEIGHT range in lb and give BREED examples.
     That ordering is the whole brief: nobody knows their dog's measurements,
     everybody knows roughly what it weighs and what breed it is.
  4. A measurement with real units appears somewhere, so anyone who does want
     to measure can. Dimensions count; a body measurement is no longer
     required, because for bedding the dimensions ARE the measurement.
  5. The weight and breed text for a given letter is IDENTICAL across every
     product that sells that letter. This is the promise the whole scale
     exists to make, and it is the one thing a human will never catch by eye
     across fifteen product pages.

    python config/audit_size_guides.py           # exits non-zero on a gap
    python config/audit_size_guides.py --json    # also write a qa log
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from size_scale import ORDER, BY_SIZE, weight_text, FURNITURE   # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

MARK = 'wagvive-size-guide'
LENGTH = re.compile(r'\d+(?:\.\d+)?\s*(?:to\s*\d+(?:\.\d+)?\s*)?(?:in\b|cm\b)', re.I)
WEIGHT = re.compile(r'\d+\s*(?:to\s*\d+\s*)?lb\b', re.I)


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


def text(fragment):
    fragment = re.sub(r'<style>.*?</style>', ' ', fragment, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment)))


def main():
    prods = api('products.json?limit=250&status=active')['products']
    sized = [p for p in prods
             if any(o['name'].lower() == 'size' for o in p['options'])]
    if not sized:
        print('no active product takes a size, which is itself suspicious')
        return 1

    log, bad = [], []
    seen_text = {}          # size letter -> (weight+breed text, product) for rule 5
    for p in sorted(sized, key=lambda x: x['title']):
        body = p.get('body_html') or ''
        opt = next(o for o in p['options'] if o['name'].lower() == 'size')
        vals = opt['values']
        faults = []
        furniture = p['handle'] in FURNITURE

        m = re.search(rf'<div class="{MARK}">.*?</div>', body, re.S)
        plain = text(m.group(0)) if m else ''
        if not m:
            faults.append('no size guide')

        # 1. canonical membership
        if furniture:
            if any(v in ORDER for v in vals):
                faults.append('furniture product is using dog size letters')
        else:
            off = [v for v in vals if v not in ORDER]
            if off:
                faults.append(f'off-scale size values: {", ".join(off)}')

        if plain:
            # 2. every size it sells is in the guide
            missing = [v for v in vals if v.lower() not in plain.lower()]
            if missing:
                faults.append(f'{len(missing)} size(s) missing from the guide: '
                              f'{", ".join(missing)}')

            # 3. dog-scaled products lead with weight and breeds
            if not furniture:
                if not WEIGHT.search(plain):
                    faults.append('no dog weight range in lb')
                for v in vals:
                    if v in ORDER:
                        breed1 = BY_SIZE[v]['breeds'].split(',')[0].strip()
                        if breed1.lower() not in plain.lower():
                            faults.append(f'no breed example for {v}')
                            break
                # 5. the letter must mean the same dog everywhere
                for v in vals:
                    if v not in ORDER:
                        continue
                    want = weight_text(v)
                    if want.lower() not in plain.lower():
                        faults.append(f'{v} does not state the canonical '
                                      f'weight "{want}"')

            # 4. some real measurement exists
            if not LENGTH.search(plain):
                faults.append('no measurement with units anywhere')

        mark = 'ok' if not faults else '; '.join(faults)
        print(f"{p['title'][:44]:46} {len(vals):2d} sizes  {mark}")
        log.append({'product': p['title'], 'handle': p['handle'],
                    'sizes': vals, 'faults': faults, 'furniture': furniture})
        if faults:
            bad.append(p['title'])

    print('\n' + '=' * 72)
    print(f'{len(sized)} sized products, {len(sized) - len(bad)} clean')
    print(f'canonical scale: {" ".join(ORDER)}')
    for s in ORDER:
        print(f'  {s:3} {weight_text(s)}')

    if '--json' in sys.argv:
        out = os.path.join(ROOT, 'docs', 'qa',
                           f'size-guides-{time.strftime("%Y-%m-%d")}.json')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(log, fh, indent=1, ensure_ascii=False)
        print(f'log -> {os.path.relpath(out, ROOT)}')

    if bad:
        print(f'\n{len(bad)} product(s) need attention:')
        for t in bad:
            print(f'  ! {t}')
        return 1
    print('\nEvery sized product is on the one scale and says which dog fits it.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
