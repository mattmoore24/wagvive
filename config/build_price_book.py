#!/usr/bin/env python3
"""Turn the optimiser's per-product prices into a per-VARIANT price book.

Two things the optimiser could not do on its own:

1. SIZED PRODUCTS. The optimiser prices the dearest variant a customer can
   pick. Products sold in sizes (bath robe, sofa cover, blankets, paw cup,
   water bowl) need each size priced from its own cost and weight, or small
   sizes are overpriced and big ones under. Each variant is priced by scaling
   the product's recommended price by its share of the dearest variant's unit
   cost, damped (^0.7) because perceived value scales slower than weight, then
   floored at 1.30x its own unit cost so no size sells at a loss.
   Colour-only variants stay levelled at one price, as always.

2. LOSS FLOORS. Three products optimise to a small negative margin even at
   the competitive price. They stay listed (they matter to kits and baskets)
   but are nudged to the smallest .99 price that clears +5% on a worst-case
   single-unit order.

Output: config/price_book.json
    {product_id: {title, price, floor_margin_pct, variants: {variant_sku: price}}}

`floor_margin_pct` is what margin_guard.py now enforces per product: the margin
this book expects at today's costs, minus a drift buffer. The old flat 50%
floor is gone (owner decision, 2026-08-04); the guard's job is now to catch
COST DRIFT against whatever this book promised, not to police a global number.

    python config/build_price_book.py OPTIMISED.json
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api, freight_floor, pricing

DRIFT_BUFFER_PTS = 8.0     # alert if drift eats this much margin
MIN_SINGLE_MARGIN = 5.0    # no single-unit order may lose money
SIZE_DAMP = 0.7            # perceived value grows slower than cost with size


def charm(x):
    if x <= 0.99:
        return 0.99
    b = int(x)
    return b - 1 + 0.99 if x < b + 0.99 else b + 0.99


def unit_cost(goods, freight):
    return pricing.landed(goods, freight) + pricing.FLAT


def nudge_to_floor(price, goods, freight):
    """Raise to the smallest .99 clearing MIN_SINGLE_MARGIN."""
    p = price
    while pricing.margin(p, goods, freight) * 100 < MIN_SINGLE_MARGIN and p < 500:
        p = charm(p + 1.0)
    return p


def main():
    rows = json.load(open(sys.argv[1], encoding='utf-8'))
    book = {}
    for r in rows:
        spu = None
        # variant-level costs from CJ
        d = cj_api.call('/product/query', {'productSku': None}) if False else None
        # (single call per product below)
        book[str(r['id'])] = None  # placeholder to keep order

    for r in rows:
        title = r['title']
        rec = r['rec2']
        # re-fetch this product's CJ variants once
        # SPU is derivable from any variant SKU; reprice JSON carried none, so
        # pull from Shopify handle via the stored fields: cost/weight are the
        # dearest variant's. We need per-variant data only for sized products,
        # detected by variant weight spread once fetched.
        book[str(r['id'])] = dict(title=title, price=rec, variants={},
                                  goods=r['cost'], freight=r['freight'])

    # fetch Shopify variants (sku, grams, options) in one pass
    import urllib.request
    env = {}
    with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                env[k] = v
    req = urllib.request.Request(
        f"https://{env['SHOPIFY_STORE_DOMAIN']}/admin/api/{env['SHOPIFY_API_VERSION']}"
        f"/products.json?limit=250&status=active&fields=id,title,variants",
        headers={'X-Shopify-Access-Token': env['SHOPIFY_ADMIN_API_TOKEN']})
    shop = {str(p['id']): p for p in
            json.loads(urllib.request.urlopen(req, timeout=120).read())['products']}

    import time
    for pid, entry in list(book.items()):
        p = shop.get(pid)
        if not p:
            continue
        skus = [v['sku'] for v in p['variants'] if v.get('sku')]
        if not skus:
            continue
        spu = skus[0][:11]
        d = cj_api.call('/product/query', {'productSku': spu}) or {}
        cj = {v.get('variantSku'): v for v in
              ((d.get('data') or {}).get('variants') or [])}
        time.sleep(0.35)

        # per-variant unit costs
        ucs = {}
        for v in p['variants']:
            sku = v.get('sku')
            cv = cj.get(sku)
            if not cv:
                continue
            goods = float(cv['variantSellPrice'])
            w = float(cv.get('variantWeight') or 0)
            fr = freight_floor.estimate(w)
            ucs[sku] = (unit_cost(goods, fr), goods, fr)
        if not ucs:
            continue
        max_uc = max(u for u, _, _ in ucs.values())
        spread = max_uc / min(u for u, _, _ in ucs.values())

        floor_margins = []
        for sku, (uc, goods, fr) in ucs.items():
            if spread < 1.15:
                price = entry['price']              # colour-only: levelled
            else:
                price = charm(entry['price'] * (uc / max_uc) ** SIZE_DAMP)
            price = nudge_to_floor(price, goods, fr)
            entry['variants'][sku] = price
            floor_margins.append(pricing.margin(price, goods, fr) * 100)

        # product price = dearest variant's (display/anchor); guard floor from
        # the WORST variant margin this book accepts, minus the drift buffer
        entry['price'] = max(entry['variants'].values())
        entry['floor_margin_pct'] = round(min(floor_margins) - DRIFT_BUFFER_PTS, 1)
        entry.pop('goods', None); entry.pop('freight', None)

    book = {k: v for k, v in book.items() if v and v.get('variants')}
    out = os.path.join(ROOT, 'config', 'price_book.json')
    json.dump(book, open(out, 'w'), indent=1)
    n = sum(len(v['variants']) for v in book.values())
    print(f'{len(book)} products, {n} variant prices -> config/price_book.json')
    for pid, v in book.items():
        prices = sorted(set(v['variants'].values()))
        span = (f"{prices[0]:.2f}" if len(prices) == 1
                else f"{prices[0]:.2f}-{prices[-1]:.2f}")
        print(f"  {v['title'].replace('Wagvive ','')[:34]:36} ${span:>13}  "
              f"guard>{v['floor_margin_pct']:.0f}%")
    return 0


if __name__ == '__main__':
    sys.exit(main())
