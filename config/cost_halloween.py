#!/usr/bin/env python3
"""Cost the Halloween sweep's best candidates on LIVE CJ data, and fetch their
reference photos for the eye check.

Input: config/scout_halloween_results.json (from scout_halloween.py).
Output: config/scout_halloween_costed.json, plus images under $HALLOWEEN_IMG_DIR
(which must be OUTSIDE the repo: the repo is public and these are CJ's photos).

For each candidate:
  * /product/query for the real variants, costs and weights (the listing's
    price range hides multipacks and oversizes, the classic trap)
  * a live freight quote for the MOST EXPENSIVE variant and the HEAVIEST
    variant, resolved through freight_floor.resolve() inside the 12 day carrier
    ceiling, with the placeholder test applied
  * the lowest price that clears the 20% standard on the worse of the two,
    because colour variants are priced identically (levelled to the dearest)
  * over 1 kg from China is flagged, per the sourcing rules

Nothing here is a verdict. It is the evidence the eye check and the market
check work from.

    HALLOWEEN_IMG_DIR=/path/outside/repo python config/cost_halloween.py [N]
"""
import json
import math
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api            # noqa: E402
import freight_floor     # noqa: E402
import margin_guard as MG  # noqa: E402
import pricing           # noqa: E402
from scout_halloween import existing_spus  # noqa: E402

IN = os.path.join(ROOT, 'config', 'scout_halloween_results.json')
OUT = os.path.join(ROOT, 'config', 'scout_halloween_costed.json')
STANDARD = 0.20
MAX_CN_WEIGHT_G = 1000

BUCKETS = {
    'costume': re.compile(r'costume|cosplay|dress.?up|transform|cape|cloak|'
                          r'wing|suit|outfit|jumpsuit', re.I),
    'wearable': re.compile(r'bandana|scarf|collar|bow|tie|hat|headband|horn|'
                           r'sweater|hoodie|shirt|pajama|dress|clothes|coat',
                           re.I),
    'toy': re.compile(r'toy|squeak|plush|chew|ball|rope|snuffle|puzzle|treat',
                      re.I),
}


def bucket(name):
    for b, rx in BUCKETS.items():
        if rx.search(name):
            return b
    return 'other'


def pick(cands, top_overall, top_per_bucket):
    """The best-listed overall, plus the best of each kind, so a strong toy is
    not crowded out by forty costumes."""
    chosen, ids = [], set()
    for c in cands[:top_overall]:
        chosen.append(c)
        ids.add(c['spu'])
    for b in list(BUCKETS) + ['other']:
        for c in [c for c in cands if bucket(c['name']) == b][:top_per_bucket]:
            if c['spu'] not in ids:
                chosen.append(c)
                ids.add(c['spu'])
    return chosen


def f(x, default=None):
    try:
        return float(str(x).split('-')[0].strip())
    except (TypeError, ValueError):
        return default


def images_of(d):
    raw = d.get('productImageSet') or d.get('productImage') or []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = [u for u in re.split(r'[,\s]+', raw) if u.startswith('http')]
    gallery = [u for u in raw if isinstance(u, str) and u.startswith('http')]
    desc = str(d.get('description') or '')
    charts = re.findall(r'src="(https?://[^"]+?\.(?:jpe?g|png|webp)[^"]*)"', desc,
                        re.I)
    return gallery, charts


def fetch(url, path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(path, 'wb') as fh:
            fh.write(data)
        return path
    except Exception:
        return None


def quote(vid, start):
    """Carrier options, retried: an empty answer from CJ is not evidence."""
    for attempt in range(3):
        r = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': start, 'endCountryCode': 'US',
            'products': [{'quantity': 1, 'vid': vid}]})
        opts = r.get('data') or []
        if opts:
            return opts
        time.sleep(1.5 * (attempt + 1))
    return []


def cost_one(c, img_dir):
    spu = c['spu']
    r = cj_api.call('/product/query', {'productSku': spu})
    d = r.get('data') or {}
    if not d:
        return {**c, 'error': f"no product record: {str(r)[:160]}"}
    variants = []
    for v in d.get('variants') or []:
        cost = f(v.get('variantSellPrice'))
        w = f(v.get('variantWeight'))
        if cost is None:
            continue
        variants.append({'sku': v.get('variantSku'), 'vid': v.get('vid'),
                         'name': v.get('variantNameEn') or v.get('variantKey'),
                         'key': v.get('variantKey'), 'cost': cost, 'weight_g': w})
    if not variants:
        return {**c, 'error': 'no priced variants'}

    start = freight_floor.origin_for(variants[0]['sku'])
    duty = pricing.DUTY_PCT_US_WAREHOUSE if start == 'US' else pricing.DUTY_PCT
    dearest = max(variants, key=lambda v: v['cost'])
    heaviest = max(variants, key=lambda v: v['weight_g'] or 0)
    graded = []
    for v in {id(dearest): dearest, id(heaviest): heaviest}.values():
        opts = quote(v['vid'], start)
        price, name, aging, estimated = freight_floor.resolve(
            opts, v['sku'], v['weight_g'] if start != 'US' else None)
        inside = any(freight_floor.upper_days(o.get('logisticAging'))
                     <= freight_floor.MAX_DAYS for o in opts)
        need = MG.floor_price(v['cost'], price, duty, STANDARD)
        graded.append({'sku': v['sku'], 'variant': v['name'], 'cost': v['cost'],
                       'weight_g': v['weight_g'], 'freight': round(price, 2),
                       'carrier': name, 'aging': aging,
                       'freight_estimated': estimated, 'answered': bool(opts),
                       'carrier_inside_12_days': inside,
                       'price_for_20pct': round(need, 2)})
    need = max(g['price_for_20pct'] for g in graded)
    charm = math.ceil(need + 0.01) - 0.01        # lowest x.99 at or above need

    gallery, charts = images_of(d)
    folder = os.path.join(img_dir, spu)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for i, u in enumerate(([c.get('image')] if c.get('image') else []) + gallery[:7]):
        p = fetch(u, os.path.join(folder, f'gallery_{i:02d}.jpg'))
        if p:
            saved.append(p)
    chart_files = []
    for i, u in enumerate(charts[:6]):
        p = fetch(u, os.path.join(folder, f'desc_{i:02d}.jpg'))
        if p:
            chart_files.append(p)

    weights = [v['weight_g'] for v in variants if v['weight_g']]
    return {
        **c,
        'bucket': bucket(c['name']),
        'title_cj': d.get('productNameEn'),
        'status': d.get('status'),
        'origin': start,
        'n_variants': len(variants),
        'variant_names': [v['name'] for v in variants][:40],
        'cost_range': [min(v['cost'] for v in variants),
                       max(v['cost'] for v in variants)],
        'weight_range_g': [min(weights), max(weights)] if weights else None,
        'over_1kg_from_china': bool(start != 'US' and weights
                                    and max(weights) > MAX_CN_WEIGHT_G),
        'graded': graded,
        'price_for_20pct': round(need, 2),
        'charm_price_for_20pct': round(charm, 2),
        'description_text': re.sub(r'<[^>]+>', ' ', str(d.get('description') or ''))[:1500],
        'images': saved,
        'description_images': chart_files,
    }


def main():
    img_dir = os.environ.get('HALLOWEEN_IMG_DIR')
    if not img_dir or os.path.abspath(img_dir).startswith(ROOT):
        raise SystemExit('Set HALLOWEEN_IMG_DIR to a folder OUTSIDE the repo '
                         '(the repo is public).')
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    data = json.load(open(IN, encoding='utf-8'))
    have = existing_spus()
    print(f'{len(have)} catalogue SPUs (any status) excluded')
    cands = [c for c in data['candidates'] if c['spu'][:11] not in have]
    print(f"{len(data['candidates'])} sweep candidates, {len(cands)} not already ours")
    chosen = pick(cands, n, 10)
    print(f'costing {len(chosen)}\n')

    done = {}
    if os.path.exists(OUT):                       # resumable across a quota wall
        for row in json.load(open(OUT, encoding='utf-8')).get('costed', []):
            if not row.get('error'):
                done[row['spu']] = row
    out = []
    try:
        for i, c in enumerate(chosen, 1):
            row = done.get(c['spu']) or cost_one(c, img_dir)
            out.append(row)
            if row.get('error'):
                print(f"  {i:>3} {c['spu']:14} ERROR {row['error']}")
            else:
                print(f"  {i:>3} {c['spu']:14} {row['listed']:>6} lists  "
                      f"{row['origin']}  {row['n_variants']:>3} var  "
                      f"w {row['weight_range_g']}  needs ${row['price_for_20pct']:>6.2f}  "
                      f"{row['name'][:48]}")
    except cj_api.CJQuotaExhausted as exc:
        print(f'\nSTOPPED on the CJ points quota; {len(out)} costed and saved. {exc}')
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump({'costed_on': '2026-09-14', 'standard': STANDARD,
                   'costed': out}, fh, ensure_ascii=False, indent=1)
    print(f'saved -> {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
