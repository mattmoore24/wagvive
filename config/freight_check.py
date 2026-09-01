#!/usr/bin/env python3
"""
Re-price against carriers that can actually meet the published delivery promise.

Earlier margins used the cheapest carrier of any speed, and some of those run
10-23 or 25-30 days - which the site's "5-11 business days" claim cannot honour.
This picks the cheapest carrier whose upper transit bound is within MAX_DAYS and
re-checks every variant against the flat floor in config/pricing.py (20%).

WHAT THIS IS AND IS NOT. This is a DIAGNOSTIC, not the enforcement. It answers
one deliberately blunt question: on the cheapest carrier that still keeps the
promise, does every variant clear a single flat floor? Live enforcement is
config/margin_guard.py, which is a different and stricter thing - it prices
against the carrier CJ will actually BOOK (config/carriers.json) and grades each
product against its own floor from config/price_book.json, where the median is
17.5% and the range is 2.0% to 41.7%. Expect the two to disagree; when they do,
margin_guard is the one that governs and the one wired into
.github/workflows/scheduled-ops.yml.

FOUR BUGS FIXED 2026-08-31, all of which made this script LIE rather than fail.
A run that morning printed a confident eight-variant BELOW FLOOR verdict, and
it had actually priced 32 of 193 variants:

  1. It read sku -> vid and cost from config/cj_variants.json, a static cache
     checked in with the initial commit holding 8 SPUs / 74 variants, plus two
     SPUs hardcoded here. The catalogue is 46 products / 193 SKU-carrying
     variants. Every miss printed "not resolvable" and was SKIPPED - 161 of
     them - and the summary then spoke as if it had covered the catalogue. Now
     resolved live through margin_guard.live_cj_costs, which derives the SPU
     list from the SKUs actually on the store and so cannot go stale.
  2. main() returned None, so `sys.exit(main())` was never even the pattern -
     the script exited 0 whether or not it found breaches. As a release gate it
     could only ever pass. This is the same bug apply_colorway_covers.py had.
  3. No coverage gate. If CJ answered for nothing at all, the output was
     "All variants clear the floor". margin_guard grew a MIN_COVERAGE gate on
     2026-08-19 for exactly this reason; this now mirrors it.
  4. Shipping origin was guessed from a `CJBQ` SKU prefix. That heuristic is
     documented wrong in docs/HANDOFF.md and was already fixed in
     audit_cj_connections.py and margin_guard.py: origin lives in the STOCK
     ROWS. Now uses freight_floor.origin_for(). Getting this wrong quotes a
     US-warehoused item from China and charges it 20% duty it does not owe.

Also: an empty answer from CJ is retried, and CJ's daily API points quota is
detected and aborted on rather than retried into. An unanswerable variant is
UNKNOWN and counts against coverage - it is never silently dropped.

    python config/freight_check.py

Exit codes, matching margin_guard.py so the two can be read the same way:
0 clean, 1 one or more variants below the flat floor, 2 Shopify HTTP failure,
3 COULD NOT VERIFY (too little of the catalogue got a real answer from CJ -
nothing is known to be wrong with any price).
"""
import json, os, re, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import margin, min_price, retail_round, DUTY_PCT, DUTY_PCT_US_WAREHOUSE
# Reuse the proven resolver rather than keeping a second copy of a thing that
# has already gone stale once. live_cj_costs builds sku -> (vid, cost) from the
# SPUs present on the store; CJUnavailable is raised on quota exhaustion.
from margin_guard import live_cj_costs, CJUnavailable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Matches the delivery window published at checkout and on the FAQ / Shipping
# pages ("5-12 business days"). Was 11, which wrongly flagged the Slicker Brush's
# only carrier (6-12 days) as breaking a promise the site never made.
MAX_DAYS = 12

# Same threshold and same reasoning as margin_guard.MIN_COVERAGE: a guard that
# graded almost nothing must not be able to report success.
MIN_COVERAGE = 0.80

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
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def best_freight(vid, start='CN', max_days=MAX_DAYS):
    """Cheapest option inside the transit promise; falls back to cheapest overall.

    Returns None only when CJ did not answer after retries, which the caller
    must treat as UNKNOWN rather than as "no carrier" - CLAUDE.md is explicit
    that an empty answer from CJ is not evidence of anything.
    """
    opts = []
    for attempt in range(3):
        r = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': start, 'endCountryCode': 'US',
            'products': [{'quantity': 1, 'vid': vid}]})
        # Quota exhaustion arrives as an ordinary 200 with result:false. No
        # number of retries changes it, and every number computed while it is
        # happening is untrustworthy - a partial read once reported 53.4%
        # against a true 27.8%. Abort the whole run.
        if r.get('result') is False and 'Insufficient API points' in str(r.get('message')):
            raise CJUnavailable(str(r.get('message'))[:200])
        opts = [o for o in (r.get('data') or []) if o.get('logisticPrice') is not None]
        if opts:
            break
        time.sleep(1.5 * (attempt + 1))
    if not opts:
        return None
    inside = [o for o in opts if upper_days(o.get('logisticAging')) <= max_days]
    pool = inside or opts
    b = min(pool, key=lambda o: o['logisticPrice'])
    return {'price': b['logisticPrice'], 'name': b.get('logisticName'),
            'aging': b.get('logisticAging'), 'within_promise': bool(inside)}


def main():
    products = api('products.json?limit=250&status=active')['products']
    skus = [v['sku'] for p in products for v in p['variants'] if v.get('sku')]
    print(f'resolving {len(skus)} SKUs against CJ...')
    resolved = live_cj_costs(skus)
    # Count only SKUs the STORE sells: live_cj_costs returns every variant of
    # each SPU, so len(resolved) can exceed the catalogue and would read as
    # more than 100% resolved.
    print(f'{sum(1 for s in skus if s in resolved)} of {len(skus)} resolved\n')

    problems, unresolved = [], []
    checked = 0
    print(f'Cheapest carrier delivering within {MAX_DAYS} days\n')
    for p in products:
        title = p['title'].encode('ascii', 'replace').decode()
        if not any(v.get('sku') for v in p['variants']):
            print(f'{title}  (bundle / no SKUs - skipped)')
            continue
        print(f'{title}')
        for v in p['variants']:
            sku = v.get('sku')
            vid, cost = resolved.get(sku, (None, None))
            if not vid or cost is None:
                print(f'   {str(v["title"])[:30]:32} sku {sku} - no CJ record')
                unresolved.append((p['title'], v['title'], sku, 'no CJ record'))
                continue
            # Origin from the STOCK ROWS, never the SKU prefix. See the module
            # docstring, bug 4.
            start = freight_floor.origin_for(sku)
            f = best_freight(vid, start)
            if not f:
                print(f'   {str(v["title"])[:30]:32} CJ did not answer - UNKNOWN')
                unresolved.append((p['title'], v['title'], sku, 'CJ did not answer'))
                continue
            checked += 1
            # US-warehouse stock was already imported; only China-origin pays duty.
            duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
            price = float(v['price'])
            m = margin(price, cost, f['price'], duty) * 100
            floor = min_price(cost, f['price'], duty)
            flag = '' if price >= floor else '  <-- BELOW FLOOR'
            note = '' if f['within_promise'] else '  (no carrier within promise)'
            print(f'   {str(v["title"])[:30]:32} ${price:<7.2f} cost ${cost:<6.2f} '
                  f'frt ${f["price"]:<6.2f} duty ${cost*duty:<5.2f} {m:5.1f}%  '
                  f'{str(f["aging"]):<7}{flag}{note}')
            if price < floor:
                problems.append((p['id'], p['title'], v['title'], price, floor, cost, f['price']))
        print()

    total_seen = checked + len(unresolved)
    coverage = checked / total_seen if total_seen else 0.0
    print(f'{checked} of {total_seen} variants priced ({coverage:.0%} coverage)')
    for t, vt, sku, why in unresolved:
        print(f'  UNRESOLVED  {t[:30]:32} {str(vt)[:20]:22} {sku}  ({why})')

    if total_seen and coverage < MIN_COVERAGE:
        print(f'\nCOULD NOT VERIFY: only {checked}/{total_seen} variants '
              f'({coverage:.0%}) got a real answer from CJ, below the '
              f'{MIN_COVERAGE:.0%} minimum.')
        print('This is NOT a margin finding. Nothing is known to be wrong with '
              'any price. Re-run once CJ recovers.')
        return 3

    if problems:
        print('\nBELOW FLOOR (flat floor - check margin_guard.py for what is '
              'actually enforced):')
        for pid, pt, vt, price, floor, cost, fr in problems:
            print(f'  {pt[:34]:36} {str(vt)[:22]:24} ${price:.2f} -> '
                  f'needs ${floor:.2f} (retail ${retail_round(floor):.2f})')
        return 1

    print('\nAll priced variants clear the flat floor using promise-compliant '
          'carriers.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except CJUnavailable as exc:
        print(f'\nCOULD NOT VERIFY: {exc}', file=sys.stderr)
        print('CJ daily API points are exhausted. This is NOT a margin finding. '
              'Points trickle back roughly once a minute; wait at least an hour '
              'of light CJ usage, or resume tomorrow. See '
              'docs/knowledge/cj-api-points-quota.md.', file=sys.stderr)
        sys.exit(3)
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(2)
