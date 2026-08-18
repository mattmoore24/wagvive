#!/usr/bin/env python3
"""Bring the 10 fall/viral launch prices down to the lowest end of a reasonable
range, now that real market comps exist for categories `market_bands.py` never
covered (none of these 10 products were in it - they launched after the
2026-08-04 band study).

WHY THESE WERE HIGH. Every one of these was launched at a single "looks about
right" .99 price chosen against COST alone (see add_fall_lineup.py /
add_fall_wave2.py), never checked against what the unbranded/volume seller
actually charges for the same thing. Margins came out at 40-53%, twice what the
rest of the catalogue runs (price_book median floor is 16.6%), because nothing
forced them down to a competitive number.

METHODOLOGY, matching market_bands.py's own rule: compare against the cheapest
CREDIBLE volume seller, not the premium brand, because we are a zero-review
store and cannot hold a premium-brand price. Comps pulled live 2026-08-18 from
Walmart marketplace search (the least gated source for this - Amazon blocks
automated fetches), which surfaces the same long tail of unbranded sellers CJ
dropshippers compete against. See the `note` field on each row for the specific
listings.

For each product: the recommended price is
    max(market_low, min_price(worst_variant_cost, worst_variant_freight,
                              duty, floor=0.25))
rounded UP to the next .99 (never down - the floor is a floor). 0.25 is not
arbitrary: it is margin_guard.DEFAULT_FLOOR, the number ALREADY governing these
SKUs today, because none of them were ever added to price_book.json. Every
number here is live: CJ product cost and a live freight quote through the same
`freight_floor.resolve()` the rest of the pricing stack uses, on the single
WORST-margin variant per product (the whole product shares one price, so the
worst variant is what has to clear the floor).

THREE ARE HELD, NOT CUT:
  * Big Dog Costume and Pumpkin Snuffle Mat are already AT their market
    comparable ($29.99 vs a $32.99-36.99 direct comp; $26.99 vs an identical
    $26.99 competing product). Cutting further would just be underpricing a
    correctly-matched product, not chasing "reasonable".
  * Pumpkin Chew Toy's floor price already equals its current $16.99, so there
    is no room below today's price without breaching the floor.

BALL LAUNCHER IS DELIBERATELY NOT CUT, DESPITE THE FORMULA SAYING $91.99.
Its freight is CJ's own $0.00 domestic quote (missing data) falling back to a
flat $11 estimate that is only proven accurate for a 450g reference item - this
SKU is 1800g, 4x heavier, and nobody has confirmed real domestic freight for
that weight class with an actual order. A second code path in this repo
(recheck_products.py's weight-aware call) would price the same $0 quote at
$26.20 instead of $11, which would put TODAY's $94.99 price at ~11% margin, not
27.6%. Cutting a product with that large an unresolved cost swing is the
opposite of prudent. Flagged separately; held at $94.99 here.

    python config/reprice_fall_lineup.py            # show the plan (default)
    python config/reprice_fall_lineup.py --apply    # write the 6 approved cuts
"""
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                              # noqa: E402
import freight_floor                                       # noqa: E402
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE, margin, min_price  # noqa: E402

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
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')

FLOOR = 0.25   # margin_guard.DEFAULT_FLOOR - already governs these SKUs today

# handle -> (market low, note, hold). `hold=True` means show the analysis but
# do not write, for the reasons in the module docstring.
PLAN = {
 'wagvive-steam-grooming-brush': (9.99, False,
   'Walmart marketplace 3-in-1 steam grooming brushes, real transacted prices: '
   'TIJITY $13.98, generic $9.99, Steamy Pet Brush $12.59.'),
 'wagvive-glow-skeleton-suit': (11.99, False,
   'Flat bone-print skeleton suits (non-3D), Walmart marketplace: $11.18-11.99 '
   'basic; 3D/dinosaur-style runs $20-33. Ours is a flat bone-print jumpsuit.'),
 'wagvive-pumpkin-hoodie': (9.98, False,
   'Walmart marketplace extended-size dog hoodies (XL-5XL, the comparable '
   'range): Walbest/GASTROPOD $9.98-12.09, "Premium Dog Hoodie" S/M/L $12.99.'),
 'wagvive-roast-turkey-sniff-toy': (14.99, False,
   'Midlee (established pet brand) Roasted Thanksgiving Turkey Plush '
   '$14.99-19.99, the closest comp for a pull-out-veggie turkey toy.'),
 'wagvive-jack-o-lantern-sweater': (9.21, False,
   'Walmart marketplace pumpkin/Halloween knit sweaters, non-clearance: '
   'YVNAURA $9.21-10.11, M Buder $13.79, generic $15.90-18.99.'),
 'wagvive-thanksgiving-turkey-coat': (10.49, False,
   'Amazon Thanksgiving turkey costumes from $10.49; Walmart turkey dog '
   'sweatshirt $16.90; Target Boots & Barkley turkey hoodie $10.00.'),
 'wagvive-ball-launcher': (58.49, True,
   'Elevon (unbranded) $58.49, All For Paws $75.59, iFetch (premium) $129.99. '
   'HELD: freight for this weight class is unverified, see module docstring.'),
 'wagvive-big-dog-costume': (29.99, True,
   'Direct comp: Dinosaur/T-Rex Skeleton Dog Costume for Medium & Large Dogs '
   '(Walmart) $32.99-36.99. Already at/under the direct comp.'),
 'wagvive-pumpkin-snuffle-mat': (26.99, True,
   'Direct comp: "6 Pack Pumpkin Slices with Peel Snuffle Mat" (Walmart, '
   'Nocciola) $26.99 - identical concept, identical price.'),
 'wagvive-pumpkin-chew-toy': (9.99, True,
   'Walmart marketplace durable pumpkin squeaker/chew toys: $9.99 generic, '
   '$11.99-15.99 "for Aggressive Chewers" tier. Already at its margin floor.'),
}


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


def ceil99(x):
    """Smallest N.99 >= x. Rounding DOWN (as optimise_prices.charm() does for an
    already-safe contribution-optimal price) is wrong here: x can BE the margin
    floor, and rounding it down would silently sell under it."""
    n = math.floor(x)
    cand = round(n + 0.99, 2)
    if cand < x - 1e-9:
        cand = round(cand + 1, 2)
    return cand


def worst_variant(product):
    """(price, cost, freight, duty, sku) for the variant with the lowest margin.
    Every product here shares one price across variants, so the worst variant
    is what actually has to clear the floor."""
    rows = []
    for v in product['variants']:
        sku = v.get('sku')
        if not sku:
            continue
        spu = sku[:11]
        data = cj_api.call('/product/query', {'productSku': spu}).get('data') or {}
        cv = next((c for c in (data.get('variants') or [])
                  if c.get('variantSku') == sku), None)
        if not cv:
            continue
        cost = float(str(cv.get('variantSellPrice') or '0').split('-')[0])
        weight = cv.get('variantWeight')
        start = freight_floor.origin_for(sku)
        duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
        opts = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': start, 'endCountryCode': 'US',
            'products': [{'quantity': 1, 'vid': cv.get('vid')}]}).get('data') or []
        # Match margin_guard's own production call: no weight passed, so a $0
        # domestic quote falls back to the flat estimate, not the
        # internationally-fitted per-gram curve. See the Ball Launcher note.
        frt, _, _, _ = freight_floor.resolve(opts)
        price = float(v['price'])
        m = margin(price, cost, frt, duty)
        rows.append((m, price, cost, frt, duty, sku))
        time.sleep(0.2)
    return min(rows, key=lambda r: r[0])


def main():
    apply = '--apply' in sys.argv
    plan, held = [], []

    for handle, (low, hold, note) in PLAN.items():
        ps = api(f'products.json?handle={handle}&status=active')['products']
        if not ps:
            print(f'  ! {handle}: not found/active, skipping')
            continue
        p = ps[0]
        m_worst, cur, cost, frt, duty, sku = worst_variant(p)
        floor_price = min_price(cost, frt, duty, floor=FLOOR)
        rec = ceil99(max(low, floor_price))
        m_rec = margin(rec, cost, frt, duty) * 100

        row = dict(product=p, handle=handle, title=p['title'], cur=cur, rec=rec,
                  low=low, floor_price=round(floor_price, 2),
                  m_cur=round(m_worst * 100, 1), m_rec=round(m_rec, 1),
                  note=note, sku=sku, cost=cost, frt=frt)
        if hold or rec >= cur:
            held.append(row)
        else:
            plan.append(row)

    print(f"{'product':42}{'current':>9}{'rec':>8}{'delta':>8}{'m@cur':>8}{'m@rec':>8}")
    for r in plan:
        print(f"  {r['title'][:40]:42}{r['cur']:>9.2f}{r['rec']:>8.2f}"
              f"{r['rec']-r['cur']:>+8.2f}{r['m_cur']:>7.1f}%{r['m_rec']:>7.1f}%")
        print(f"      {r['note']}")

    if held:
        print(f"\n{len(held)} held, not written:")
        for r in held:
            print(f"  {r['title'][:40]:42}{r['cur']:>9.2f}  (floor allows "
                  f"${r['floor_price']:.2f}, market says hold)")
            print(f"      {r['note']}")

    if not plan:
        print('\nNothing to apply.')
        return 0
    if not apply:
        print(f'\n{len(plan)} price cut(s) planned. Dry run, use --apply.')
        return 0

    for r in plan:
        for v in r['product']['variants']:
            api(f"variants/{v['id']}.json", 'PUT',
                {'variant': {'id': v['id'], 'price': f"{r['rec']:.2f}"}})
        print(f"  wrote {r['title']}: ${r['cur']:.2f} -> ${r['rec']:.2f}")

    print('\n--- verify against the live storefront ---')
    bad = 0
    for r in plan:
        url = (f"https://{SHOP}/products/{r['handle']}.js"
               f"?nocache={int(time.time()*1000)}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                d = json.loads(resp.read().decode())
            prices = {v['price'] / 100 for v in d['variants']}
            ok = prices == {r['rec']}
        except Exception as e:
            ok, prices = False, str(e)
        print(f"  {r['title'][:40]:42} {prices}  {'OK' if ok else 'MISMATCH'}")
        bad += not ok
        time.sleep(0.3)

    if bad:
        print(f'\n{bad} product(s) did not verify. Check before trusting this.')
        return 1
    print('\nAll 6 prices confirmed live on the storefront.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
