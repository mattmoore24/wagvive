#!/usr/bin/env python3
"""Prove every image on the fall products is house art, not CJ photography.

House art is uploaded by `apply_fall_art.py` with a filename that starts with
the product handle, e.g. `wagvive-pumpkin-hoodie__Black.jpg`. Anything CJ
supplied keeps CJ's own name, which is a bare UUID like
`e03b9b5b-1e36-41e9-a1a9-23d32ac56238.jpg`, sometimes with a `_trans` suffix.
That difference is the whole test and it is reliable because we control every
upload path.

WHY THIS AUDIT EXISTS. Promoting house art to position 1 fixed the product card
and the hero, and it was easy to conclude from that the job was done. It was not:
the CJ originals were still sitting at positions 2 onward, so a shopper opening
the gallery still saw supplier photography, on a white or lifestyle background,
next to our cream studio shots.

Reports per product and exits non-zero if any CJ image survives, so it can be
used as a gate.

    python config/audit_fall_imagery.py            # report
    python config/audit_fall_imagery.py --json     # also write a qa log
"""
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
SEASONAL_HANDLE = 'fall-halloween'

# CJ names files TWO ways, and knowing only one of them is how three CJ images
# survived an audit that printed CLEAN: a bare 8-4-4-4-12 hex UUID, and a bare
# numeric id like `1723569094244044800.jpg`. Both may carry a `_trans` suffix.
CJ_NAME = re.compile(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                     r'[0-9a-f]{4}-[0-9a-f]{12}|\d{6,})(_trans)?\.', re.I)

# Our own uploads are always descriptive lowercase words joined by hyphens:
# `wagvive-pumpkin-hoodie__Black.jpg`, `squirplush-master.png`,
# `kit-flatlay-toy-kit.jpg`. Requiring a real word means the NEXT supplier
# naming format nobody has seen yet surfaces as a question, not a pass.
HOUSE_NAME = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)+', re.I)


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


# Products shot in the fall batch that have since left the fall collection.
# Scoping this audit to the collection alone was fine until the Ball Launcher
# and the Steam Grooming Brush were moved to Toys & Play and Grooming, where
# they belong: they silently dropped out of the gate while still carrying art
# from this batch. Membership of a marketing collection is the wrong thing to
# hang an imagery check on, so they are named here.
ALSO_CHECK = ['wagvive-ball-launcher', 'wagvive-steam-grooming-brush']


def fall_products():
    out = []
    for c in api('custom_collections.json?limit=250')['custom_collections']:
        if c['handle'] == SEASONAL_HANDLE:
            out = api(f"collections/{c['id']}/products.json?limit=250")['products']
            break
    seen = {p['id'] for p in out}
    for handle in ALSO_CHECK:
        for p in api(f'products.json?handle={handle}&limit=1')['products']:
            if p['id'] not in seen:
                out.append(p)
    return out


def classify(fname, handle):
    """'CJ', 'house' or 'unknown'. Deliberately not a simple inverse.

    Two earlier versions of this were wrong in opposite directions. Keying on
    `fname.startswith(handle)` was too NARROW and falsely accused
    `squirplush-master.png`, which is genuine house art from an earlier session.
    Replacing that with "anything that is not a UUID is ours" was too LOOSE, and
    it let three CJ files named `1723569094244044800.jpg` sit on the Big Dog
    Costume through an audit that printed CLEAN.

    So: match CJ's known formats, match our own convention, and report anything
    that matches neither as unknown, which fails the audit and gets human eyes.
    """
    if CJ_NAME.match(fname):
        return 'CJ'
    if HOUSE_NAME.match(fname):
        return 'house'
    return 'unknown'


def main():
    prods = fall_products()
    if not prods:
        print('fall collection not found or empty')
        return 1

    log, bad = [], []
    total = house = cj = unknown = 0
    for p in sorted(prods, key=lambda x: x['title']):
        if p.get('status') != 'active':
            continue
        rows = []
        for im in p['images']:
            fname = im['src'].split('/')[-1].split('?')[0]
            kind = classify(fname, p['handle'])
            rows.append({'position': im['position'], 'kind': kind,
                         'file': fname, 'id': im['id'],
                         'alt': im.get('alt')})
            total += 1
            house += kind == 'house'
            cj += kind == 'CJ'
            unknown += kind == 'unknown'
        offenders = [r for r in rows if r['kind'] != 'house']
        if offenders:
            bad.append(p['title'])
        mark = 'CLEAN' if not offenders else f"{len(offenders)} NOT HOUSE"
        print(f"\n{p['title']}  ({len(rows)} images)  {mark}")
        for r in sorted(rows, key=lambda x: x['position']):
            flag = '   ' if r['kind'] == 'house' else '<- '
            print(f"  {flag}pos{r['position']:<2} {r['kind']:8} {r['file'][:58]}")
        log.append({'product': p['title'], 'handle': p['handle'], 'images': rows})

    print('\n' + '=' * 70)
    print(f'{len(log)} active fall products, {total} images: '
          f'{house} house, {cj} CJ, {unknown} unknown')

    if '--json' in sys.argv:
        out = os.path.join(ROOT, 'docs', 'qa',
                           f'fall-imagery-{time.strftime("%Y-%m-%d")}.json')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(log, fh, indent=1, ensure_ascii=False)
        print(f'log -> {os.path.relpath(out, ROOT)}')

    if bad:
        print(f'\n{len(bad)} product(s) still carry non-house imagery:')
        for t in bad:
            print(f'  ! {t}')
        return 1
    print('\nEvery image on every fall product is house art.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
