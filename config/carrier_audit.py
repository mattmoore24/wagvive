#!/usr/bin/env python3
"""Is each product shipping on the cheapest carrier that still keeps the promise?

The carrier chosen in the CJ connection is what actually gets booked, and it is
set per product, not per variant - so it has to be the best compromise across
every variant of that product, not just the lightest one. This prices every
variant on every carrier and reports the cheapest option that still delivers
inside the published window, against what is currently selected.

Selected carriers are read from the CJ connection table (see the docstring in
config/margin_guard.py for why that has to be scraped rather than queried).

    python config/carrier_audit.py
"""
import json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
from freight_floor import MAX_DAYS, upper_days

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Preferred upper bound on transit. Sits comfortably inside the published 5-12
# business day promise so real deliveries are not permanently at its edge.
FAST_DAYS = 9

# SPU -> carrier selected in the CJ connection. Single source of truth, shared
# with margin_guard so freight is costed against what actually gets booked.
with open(os.path.join(ROOT, 'config', 'carriers.json'), encoding='utf-8') as _fh:
    SELECTED = json.load(_fh)['carriers']

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


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def quotes(vid, start='CN'):
    r = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    out = {}
    for o in (r.get('data') or []):
        p = o.get('logisticPrice')
        if p is None or p <= 0:
            continue
        out[str(o.get('logisticName')).strip()] = (float(p), o.get('logisticAging'))
    return out


def main():
    # sku -> vid, from CJ, for every SKU live on the store
    live = {}
    for p in api('products.json?limit=250&status=active')['products']:
        for v in p['variants']:
            if v.get('sku'):
                live.setdefault(str(v['sku'])[:11], []).append((p['title'], v['title'], v['sku']))

    total_saving = 0.0
    for spu, rows in live.items():
        selected = SELECTED.get(spu)
        r = cj_api.call('/product/query', {'productSku': spu})
        vids = {v.get('variantSku'): v.get('vid')
                for v in ((r.get('data') or {}).get('variants') or [])}

        title = rows[0][0]
        print(f'{title.encode("ascii", "replace").decode()}   [selected: {selected}]')

        # Price every variant on every carrier, then keep only carriers that can
        # serve ALL variants - a per-product setting cannot use a carrier that
        # one size is ineligible for.
        per_variant, viable = [], None
        for _, vtitle, sku in rows:
            vid = vids.get(sku)
            if not vid:
                print(f'   {vtitle[:26]:28} no vid'); continue
            q = quotes(vid)
            inside = {n: v for n, v in q.items() if upper_days(v[1]) <= MAX_DAYS}
            per_variant.append((vtitle, inside))
            names = set(inside)
            viable = names if viable is None else (viable & names)

        if not per_variant:
            print(); continue
        viable = viable or set()

        def worst(carrier):
            return max(v[carrier][0] for _, v in per_variant if carrier in v)

        def slowest(carrier):
            return max(upper_days(v[carrier][1]) for _, v in per_variant if carrier in v)

        cur_cost = worst(selected) if selected in viable else None
        ranked = sorted(((worst(c), c) for c in viable))

        # The outright cheapest carrier is almost always an 11-12 day line while a
        # 7 day line costs cents more. Buying four days of delivery speed for
        # under a dollar is worth it on a store whose margins are already above
        # 50%, and it keeps real delivery away from the edge of the published
        # promise. So: cheapest inside FAST_DAYS, and only fall back to the
        # cheapest inside MAX_DAYS when nothing fast exists.
        fast = [(c, n) for c, n in ranked if slowest(n) <= FAST_DAYS]
        pick = (fast or ranked)[0] if ranked else None

        for cost, name in ranked[:4]:
            mark = ' <- selected' if name == selected else ''
            print(f'   {cost:7.2f}  {slowest(name):>2}d  {name[:34]}{mark}')
        if cur_cost is None:
            print(f'   !! selected {selected!r} is NOT viable across all variants '
                  f'or misses the {MAX_DAYS}-day window')
        if pick and pick[1] != selected:
            delta = (cur_cost - pick[0]) if cur_cost is not None else None
            total_saving += max(delta or 0, 0)
            d = f'saves ${delta:.2f}' if delta is not None else 'replaces an unusable carrier'
            print(f'   -> use {pick[1]} ({slowest(pick[1])}d, ${pick[0]:.2f})  {d}')
        elif pick:
            print(f'   -> already optimal ({slowest(pick[1])}d)')
        print()

    print(f'Rule: cheapest carrier delivering within {FAST_DAYS} days, '
          f'else cheapest within {MAX_DAYS}.')
    if total_saving:
        print(f'Addressable saving: ${total_saving:.2f} per order across products.')


if __name__ == '__main__':
    main()
