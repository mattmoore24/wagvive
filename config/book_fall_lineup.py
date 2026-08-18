#!/usr/bin/env python3
"""Add the 10 fall/viral launch products to price_book.json.

None of the ten were ever in the book. reprice_fall_lineup.py just cut six of
them to a competitive price and held the other four; until they are in the
book, margin_guard.py grades all ten against DEFAULT_FLOOR (25%), a number
that has nothing to do with what any of them actually cost today. This gives
each one a real floor_margin_pct, computed the same way calibrate_floors.py
computes every other product's: today's worst-variant margin minus an 8 point
drift buffer, clamped at 2%.

Deliberately narrow. This does NOT run build_price_book.py's full pipeline
(which re-derives prices for the whole 47-product book from an optimiser
pass) - it only inserts entries for the ten handles listed here, at their
CURRENT live prices, and refuses to touch a product ID already in the book.

    python config/book_fall_lineup.py            # show the plan
    python config/book_fall_lineup.py --apply
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api                                              # noqa: E402
import freight_floor                                       # noqa: E402
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE, margin  # noqa: E402

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

BOOK_PATH = os.path.join(ROOT, 'config', 'price_book.json')
BUFFER = 8.0       # same drift buffer calibrate_floors.py uses
FLOOR_MIN = 2.0

HANDLES = [
    'wagvive-steam-grooming-brush', 'wagvive-glow-skeleton-suit',
    'wagvive-pumpkin-hoodie', 'wagvive-roast-turkey-sniff-toy',
    'wagvive-jack-o-lantern-sweater', 'wagvive-thanksgiving-turkey-coat',
    'wagvive-ball-launcher', 'wagvive-big-dog-costume',
    'wagvive-pumpkin-snuffle-mat', 'wagvive-pumpkin-chew-toy',
]


def api(path):
    import urllib.request
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


class QuotaExhausted(Exception):
    pass


def cj_query(spu):
    """/product/query, but distinguishes a genuinely empty result from CJ
    REFUSING the call outright.

    CJ's daily API points quota (config/cj_api.py has no concept of this - it
    only retries HTTP 429s) can hit zero mid-session: a 200 response comes back
    with `result: false, code: 16900500, message: "Insufficient API points..."`
    and `data: null`. Every earlier version of this retry loop read that as
    "no CJ product record" and kept retrying it 4 times per SKU, which cannot
    ever succeed once the quota is at zero - it wastes the whole retry budget
    AND, worse, produces a plausible-looking but WRONG margin figure, computed
    from whichever handful of variants happened to resolve before the quota
    ran out (confirmed live: the Skeleton Suit reported "worst margin 53.4%"
    from a single surviving variant out of four, when the real worst margin,
    from a fully-resolved run earlier the same session, was 27.8%).

    So: raise immediately and let the whole run stop, rather than retrying
    into a wall and reporting confident numbers built on partial data.
    """
    r = cj_api.call('/product/query', {'productSku': spu})
    if r.get('result') is False and 'Insufficient API points' in str(r.get('message')):
        raise QuotaExhausted(r['message'])
    return r


def resolve_product(p):
    """Margin-derived book entry for one product, or None if CJ could not
    price any of its variants. Raises QuotaExhausted if the daily points
    budget dies partway through - the caller decides what to do with whatever
    OTHER products already succeeded before this one."""
    margins, unresolved, spu_cache = {}, {}, {}
    for v in p['variants']:
        sku = v.get('sku')
        if not sku:
            continue
        spu = sku[:11]
        # One /product/query per SPU returns EVERY variant of that SPU in
        # one response - the Pumpkin Hoodie's single call already returned
        # all 65 rows (confirmed earlier this session: "65 CJ variant
        # records for CJGD1828443" from ONE query). The first draft of
        # this script queried per VARIANT instead, so a single 65-variant
        # product spent 65x the points a single product needed - a real
        # cost given CJ enforces a daily points BUDGET, not just a rate
        # limit (docs/knowledge/cj-api-points-quota.md). Cached per SPU,
        # per product, so a re-run of this script still re-fetches fresh
        # data rather than trusting something from an earlier run.
        #
        # CJ's API also answers empty on a fraction of calls for no
        # discernible reason - confirmed live while building this: four
        # identical freightCalculate calls for the same vid returned 27
        # real carrier options three times running, then zero on the
        # fourth. A single empty read is not evidence the product is
        # uncarriageable, it is evidence CJ hiccuped, so this retries
        # before being believed. Skipping this cost the first draft of
        # this script a spurious 13.2% "worst margin" on the Pumpkin
        # Hoodie that a retry resolved to 27.9%+.
        if spu not in spu_cache:
            variants_by_sku = {}
            for attempt in range(4):
                data = cj_query(spu).get('data') or {}
                variants_by_sku = {c.get('variantSku'): c
                                  for c in (data.get('variants') or [])}
                if variants_by_sku:
                    break
                time.sleep(1.5 * (attempt + 1))
            spu_cache[spu] = variants_by_sku
        cv = spu_cache[spu].get(sku)
        if not cv:
            unresolved[sku] = 'no CJ product record after 4 tries'
            continue

        cost = float(str(cv.get('variantSellPrice') or '0').split('-')[0])
        start = freight_floor.origin_for(sku)
        duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
        opts = []
        for attempt in range(4):
            opts = cj_api.call('/logistic/freightCalculate', payload={
                'startCountryCode': start, 'endCountryCode': 'US',
                'products': [{'quantity': 1, 'vid': cv.get('vid')}]}).get('data') or []
            if opts:
                break
            time.sleep(1.5 * (attempt + 1))
        if not opts:
            unresolved[sku] = 'no freight quote after 4 tries'
            continue
        frt, _, _, _ = freight_floor.resolve(opts)   # matches margin_guard's own call
        price = float(v['price'])
        margins[sku] = margin(price, cost, frt, duty) * 100
        time.sleep(0.2)

    if unresolved:
        print(f"  ? {p['title']}: {len(unresolved)} variant(s) CJ would not "
              f"answer for even after retrying: {unresolved}")
    if not margins:
        print(f"  ! {p['title']}: no CJ-matched variants, skipping")
        return None

    worst = min(margins.values())
    floor_pct = max(round(worst - BUFFER, 1), FLOOR_MIN)
    variants = {v.get('sku'): float(v['price']) for v in p['variants']
               if v.get('sku')}
    print(f"  {p['title']:44} worst margin today {worst:5.1f}%   "
          f"floor -> {floor_pct}%")
    return {'title': p['title'], 'price': max(variants.values()),
           'variants': variants, 'floor_margin_pct': floor_pct}


def main():
    apply = '--apply' in sys.argv
    book = json.load(open(BOOK_PATH, encoding='utf-8'))

    # The daily points budget has proven too tight today to price all ten
    # products in one pass (confirmed live: two consecutive attempts each
    # died partway through, at 108850 and then 108930 points used - only
    # about 80 points of trickle between them, against ~1230 needed for a
    # full pass). If the run dies partway, whatever it DID fully resolve
    # before that point is still real, verified data and should not be
    # thrown away. So the interruption is caught HERE rather than at the top
    # level, keeping whatever `entries` were completed before it hit. Because
    # `if str(p['id']) in book: skip` below already guards every handle, each
    # partial APPLY permanently banks progress and the next run only has to
    # pay for what is still missing - repeated small attempts through the day
    # converge on all ten instead of each one re-paying for the same handful
    # that happen to resolve first. (A dry run does not book anything, so it
    # gets no benefit from this and should not be run right before --apply -
    # that doubles the CJ calls for the same information, which is exactly
    # what emptied the quota a second time earlier today.)
    entries, interrupted, already_booked, not_found = {}, False, 0, 0
    for handle in HANDLES:
        ps = api(f'products.json?handle={handle}&status=active')['products']
        if not ps:
            print(f'  ! {handle}: not found/active, skipping')
            not_found += 1
            continue
        p = ps[0]
        if str(p['id']) in book:
            print(f"  ! {p['title']}: already in the book, skipping")
            already_booked += 1
            continue
        try:
            entry = resolve_product(p)
        except QuotaExhausted as exc:
            print(f'\nSTOPPED mid-run: CJ has no API points left today ({exc}).')
            interrupted = True
            break
        if entry:
            entries[str(p['id'])] = entry

    if not entries:
        print('\nNothing to add.')
        return 2 if interrupted else 0
    if not apply:
        print(f'\n{len(entries)} product(s) would be added. Dry run, use --apply.')
        return 0

    book.update(entries)
    json.dump(book, open(BOOK_PATH, 'w', encoding='utf-8'), indent=1)
    print(f'\n{len(entries)} product(s) added. Book now has {len(book)} entries.')
    if interrupted:
        remaining = len(HANDLES) - already_booked - not_found - len(entries)
        print(f'{remaining} product(s) still need pricing once the quota '
              f'recovers - re-run this script (already-booked handles are '
              f'skipped automatically, so it only pays for what is left).')
    return 2 if interrupted else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except QuotaExhausted as exc:
        print(f'\nSTOPPED: CJ has no API points left today ({exc}).')
        print('Nothing was written. Any product not printed above with a worst '
              'margin still needs a real (not partial) CJ read - re-run once '
              'the quota has replenished. Points trickle back roughly once a '
              'minute (daily total / 1440), so this recovers gradually rather '
              'than at a fixed reset time; practically, wait at least an hour '
              'of light CJ usage, or try again tomorrow.')
        sys.exit(2)
