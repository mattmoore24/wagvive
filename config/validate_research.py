#!/usr/bin/env python3
"""Check the 2026-08-04 research data against the variants we ACTUALLY sell.

Why this exists: the shipping study scored the Anti-Spill Floating Water Bowl at
1,833g and $11.69, which is CJ's THREE-PACK sku. The single bowl we sell is 620g
and $4.13. That one substitution made the Dog Enrichment Kit look like a 24.1%
loss-maker (it measures 57.5% live) and put the bowl on the drop list.

CJ lists multipacks as ordinary variants of the same SPU, so any script that
picks a representative variant by position, or by max weight, or by "the one
with a price", can silently grab a 3-pack. This compares the study's per-product
weight and cost against the live Shopify variants for the same product and flags
anything that does not match.

    python config/validate_research.py
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

# A study weight this much above the heaviest thing we sell is a wrong-variant
# pick, not a rounding difference.
TOLERANCE = 1.25


def shopify_products():
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/products.json'
        f'?limit=250&status=active&fields=id,title,variants',
        headers={'X-Shopify-Access-Token': TOKEN})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())['products']


def main():
    dp_path = os.path.join(ROOT, 'docs', 'qa', 'delivered-price.json')
    study = json.load(open(dp_path, encoding='utf-8'))['products']
    live = {p['title']: p for p in shopify_products()}

    bad, ok, missing = [], 0, []
    for row in study:
        title = row['product']
        p = live.get(title)
        if not p:
            missing.append(title)
            continue
        weights = [v['grams'] for v in p['variants'] if v.get('grams')]
        if not weights:
            missing.append(title)
            continue
        heaviest = max(weights)
        study_w = row.get('weight_g') or 0
        if study_w > heaviest * TOLERANCE:
            bad.append((title, study_w, min(weights), heaviest,
                        row.get('cost'), row.get('freight'),
                        row.get('margin_at_market_delivered')))
        else:
            ok += 1

    print(f'{len(study)} products in the study, {ok} consistent with what we sell\n')
    if bad:
        print('WRONG VARIANT (study weight exceeds anything we stock):')
        print(f"  {'product':38}{'study g':>9}{'ours min':>10}{'ours max':>10}"
              f"{'cost':>8}{'freight':>9}{'mgn@mkt':>9}")
        for t, sw, lo, hi, c, f, m in bad:
            print(f'  {t[:36]:38}{sw:>9.0f}{lo:>10.0f}{hi:>10.0f}'
                  f'{c if c is not None else 0:>8.2f}{f if f is not None else 0:>9.2f}'
                  f'{m if m is not None else 0:>8.1f}%')
        print('\nEvery figure derived from these rows is wrong: delivered floors,'
              '\nmargin at market, viability, and any kit containing them.')
    else:
        print('No wrong-variant rows found.')
    if missing:
        print(f'\nnot matched to a live product ({len(missing)}): '
              + ', '.join(m[:28] for m in missing[:8]))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
