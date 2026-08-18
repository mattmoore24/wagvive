#!/usr/bin/env python3
"""Remove supplier photography from the fall products, leaving only house art.

The fall lineup launched on CJ's own photos so it could be live before
Halloween, then house art was shot and promoted to position 1. That fixed the
product card and the hero and it was tempting to call it done. It was not: the
CJ originals stayed at positions 2 onward, so anyone who opened a gallery still
scrolled through supplier photography, shot on white or in someone's living
room, sitting next to our cream studio shots. 56 of 80 images were still CJ's.

SAFETY. A variant pointing at an image that gets deleted has its `image_id`
silently nulled, and nothing on the storefront complains: the swatch and the
cart thumbnail just fall back to the product's lead image. So this refuses to
delete any image a variant is wired to, and it re-reads every product afterwards
to confirm no variant lost its art.

It also refuses to leave a product with no images at all.

    python config/purge_cj_imagery.py            # show the plan
    python config/purge_cj_imagery.py --apply
"""
import json
import os
import re
import sys
import time
import urllib.error
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
# CJ names files two ways: a bare 8-4-4-4-12 hex UUID, and a bare numeric id
# like `1723569094244044800.jpg`. Missing the numeric form left three CJ
# lifestyle photos live on the Big Dog Costume after a purge that reported
# success.
CJ_NAME = re.compile(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                     r'[0-9a-f]{4}-[0-9a-f]{12}|\d{6,})(_trans)?\.', re.I)


def api(path, method='GET', payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def fall_products():
    """Full product records for the fall collection.

    collections/<id>/products.json does NOT include `variants`, and this script
    depends on them to refuse deleting an image a variant is wired to. So each
    product is re-fetched in full rather than trusting the collection listing.
    """
    ids = []
    for c in api('custom_collections.json?limit=250')['custom_collections']:
        if c['handle'] == SEASONAL_HANDLE:
            ids = [p['id'] for p in
                   api(f"collections/{c['id']}/products.json?limit=250")['products']]
            break
    return [api(f'products/{pid}.json')['product'] for pid in ids]


def main():
    apply = '--apply' in sys.argv
    prods = [p for p in fall_products() if p.get('status') == 'active']
    if not prods:
        print('no active fall products found')
        return 1

    plan, problems = [], []
    for p in sorted(prods, key=lambda x: x['title']):
        cj = [im for im in p['images']
              if CJ_NAME.match(im['src'].split('/')[-1].split('?')[0])]
        keep = [im for im in p['images'] if im not in cj]
        if not cj:
            print(f"{p['title']:44} already clean ({len(keep)} house)")
            continue

        wired = {v.get('image_id') for v in p['variants'] if v.get('image_id')}
        hostage = [im for im in cj if im['id'] in wired]
        if hostage:
            print(f"{p['title']:44} REFUSING: {len(hostage)} CJ image(s) are "
                  f"wired to variants; re-run apply_fall_art.py first")
            problems.append(p['title'])
            continue
        if not keep:
            print(f"{p['title']:44} REFUSING: that would leave no images at all")
            problems.append(p['title'])
            continue

        print(f"{p['title']:44} remove {len(cj)} CJ, keep {len(keep)} house")
        plan.append((p, cj, keep))

    if problems:
        print(f'\n{len(problems)} product(s) blocked; nothing deleted')
        return 1
    if not plan:
        print('\nNothing to remove.')
        return 0
    total = sum(len(c) for _, c, _ in plan)
    print(f'\n{total} CJ image(s) across {len(plan)} product(s)')
    if not apply:
        print('Dry run. Use --apply.')
        return 0

    for p, cj, _ in plan:
        for im in cj:
            api(f"products/{p['id']}/images/{im['id']}.json", 'DELETE')
        print(f"  {p['title']:44} removed {len(cj)}")

    # Re-read: confirm no CJ survives and no variant lost its wiring.
    print('\n--- verify against the live product ---')
    bad = 0
    for p, _, _ in plan:
        fresh = api(f"products/{p['id']}.json")['product']
        left = [im['src'].split('/')[-1].split('?')[0] for im in fresh['images']]
        still = [f for f in left if CJ_NAME.match(f)]
        unwired = [v['title'] for v in fresh['variants'] if not v.get('image_id')]
        state = 'ok'
        if still:
            state = f'{len(still)} CJ REMAIN'
        elif unwired:
            state = f'{len(unwired)} VARIANTS UNWIRED'
        if state != 'ok':
            bad += 1
        print(f"  {fresh['title']:44} {len(left)} images  {state}")
    if bad:
        print(f'\n{bad} product(s) need attention')
        return 1
    print('\nOnly house art remains, and every variant kept its image.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
