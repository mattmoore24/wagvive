#!/usr/bin/env python3
"""Hold each product's margin floor even when CJ's prices move.

The flat 50% floor was retired 2026-08-04 (owner decision): prices are now set
per product by the demand model (optimise_prices.py -> build_price_book.py),
and each product's floor lives in config/price_book.json as `floor_margin_pct`
- the worst variant margin the book accepted, minus a drift buffer. The guard's
job is no longer to police a global number but to catch COST DRIFT against
whatever the book promised.

Prices were set against a snapshot of CJ product cost and freight. Both drift -
CJ posted two shipping price adjustment notices in one week - so a price that
cleared its floor at launch can quietly fall through it. This re-quotes every
active variant against live CJ data and reports, or fixes, any breach.

Cost model comes from config/pricing.py: product + duty + freight + Shopify
Payments (2.9% + $0.30). Duty is 20% on China-origin and 0% on US-warehouse
stock, which was already imported by the supplier. Freight is the cheapest
carrier whose upper transit bound still meets the published 5-12 business day
window, matching what the CJ connections are actually set to ship by.

    python config/margin_guard.py            # report only, exits 1 on a breach
    python config/margin_guard.py --apply    # also raise prices to clear the floor
    python config/margin_guard.py --margin 55  # override: one global floor

Report mode changes nothing, so it is safe to run unattended. --apply edits live
retail prices and should only run where that is intended.

EXIT CODES. These are not interchangeable and the difference is the whole point:

    0  every graded variant clears its floor
    1  a real BREACH - a live price is under its floor, and a price must move
    2  Shopify itself failed (HTTP error)
    3  COULD NOT VERIFY - too little of the catalogue got a real answer from CJ,
       or the sweep aborted. NOTHING is known to be wrong with any price.

3 was split out of 1 on 2026-08-31. While both meant "exit 1", a five-day CJ
outage and a five-day pricing error were indistinguishable in the failure email,
and they need opposite responses: one is "wait for CJ", the other is "change a
price now". GitHub Actions fails the job on any non-zero, so the workflow did
not need changing.
"""
import json, os, re, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import (PCT, FLAT, DUTY_PCT, DUTY_PCT_US_WAREHOUSE, SALES_TAX_AVG,
                     RETURNS_RATE, landed, retail_round)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_DAYS = 12
LOG = os.path.join(ROOT, 'config', 'margin_guard_log.json')

# Drift the stress column models: one realistic repricing step, not a worst case.
# CJ product costs move a few percent at a time; freight moves in steps when
# carriers reprice, which happened twice in the week to 2026-07-30. Both are
# proportional - a flat freight adder punishes cheap-to-ship items absurdly (+$6
# on a $5 quote is +120%) and flags the whole catalogue, which is no signal at all.
# A variant that fails this is still compliant today; it just has no room, so it
# is the first thing to break.
STRESS_COST = 0.10
STRESS_FREIGHT = 0.15

# Fraction of variants that must get a REAL CJ answer for a run to mean
# anything. Below this the job fails as "could not verify" rather than
# reporting either a breach or an all-clear, both of which would be fiction.
# 0.80 leaves room for CJ's normal per-call flakiness (a handful of empty
# responses per sweep is routine) while still catching a genuine outage or an
# exhausted points budget, where nearly everything comes back empty.
MIN_COVERAGE = 0.80

# Stop the sweep once this many variants in a row come back unanswered. Without
# it, retrying 258 variants x 3 attempts with backoff takes ~36 minutes for the
# freight step alone and blows the workflow's 50 minute timeout, converting a
# clean "could not verify" into an opaque timeout that burns the full 50
# minutes of Actions time and says nothing. 15 in a row is far past normal
# flakiness (routine is a handful scattered through a sweep) and means CJ is
# down or the points budget is gone.
OUTAGE_STREAK = 15


class CJUnavailable(Exception):
    """CJ cannot answer at all right now. Not a margin finding."""

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


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def _fee_rate():
    # Card fee is charged on the whole order, sales tax included.
    return PCT * (1 + SALES_TAX_AVG)


def floor_price(product, freight, duty_pct, floor):
    """Lowest price clearing `floor` margin. Mirrors pricing.min_price but takes
    the floor as an argument so a stricter target can be enforced."""
    return (landed(product, freight, duty_pct) + FLAT) / (1 - _fee_rate() - floor)


def margin_at(price, product, freight, duty_pct):
    cost = landed(product, freight, duty_pct) + _fee_rate() * price + FLAT
    return (price - cost) / price if price else 0.0


def live_cj_costs(skus):
    """sku -> (vid, cost) straight from CJ rather than any cached matrix, so a
    supplier price change is picked up.

    The SPU list is derived from the SKUs actually on the store - a CJ variant SKU
    is its 11-character parent SPU plus a suffix. Reading it from a checked-in
    matrix instead meant every newly added product came back "no CJ record" and
    was silently skipped by the floor check.
    """
    out = {}
    spus = {str(s)[:11] for s in skus if s}
    for spu in sorted(spus):
        r = cj_api.call('/product/query', {'productSku': spu})
        for v in ((r.get('data') or {}).get('variants') or []):
            sku = v.get('variantSku')
            raw = str(v.get('variantSellPrice') or '').split('-')[0]
            try:
                out[sku] = (v.get('vid'), float(raw))
            except ValueError:
                continue
    return out


with open(os.path.join(ROOT, 'config', 'carriers.json'), encoding='utf-8') as _fh:
    SELECTED_CARRIER = json.load(_fh)['carriers']

# Per-product floors from the price book. Clamped at 2% so a kit-only product
# (book floor can be near zero after the drift buffer) still alerts BEFORE it
# sells at an actual loss. Products absent from the book get DEFAULT_FLOOR.
FLOOR_MIN = 0.02
DEFAULT_FLOOR = 0.20   # owner standard 2026-08-30; was 0.25
try:
    with open(os.path.join(ROOT, 'config', 'price_book.json'), encoding='utf-8') as _fh:
        _BOOK = json.load(_fh)
    BOOK_FLOOR = {pid: max(v.get('floor_margin_pct', DEFAULT_FLOOR * 100) / 100.0,
                           FLOOR_MIN)
                  for pid, v in _BOOK.items()}
except FileNotFoundError:
    BOOK_FLOOR = {}


def best_freight(vid, start, sku=''):
    """Freight for the carrier CJ will actually book.

    Pricing against the cheapest available carrier understates cost whenever a
    faster one was deliberately selected, which quietly inflates every margin.
    Falls back to the cheapest promise-compliant option only when the selected
    carrier is unavailable for that variant.
    """
    # RETRY before believing CJ has nothing. An empty answer from CJ is not
    # evidence of anything (CLAUDE.md), and this function had no retry at all:
    # one transient empty response was enough to substitute an estimate and,
    # via the caller, report a margin breach that did not exist. Confirmed
    # live 2026-08-19: four identical calls for the same vid returned 27 real
    # carriers three times and zero on the fourth.
    opts = []
    for attempt in range(3):
        r = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': start, 'endCountryCode': 'US',
            'products': [{'quantity': 1, 'vid': vid}]})
        # Quota exhaustion is not flakiness and cannot be retried through: CJ
        # returns an ordinary 200 with result:false and this message, and no
        # number of attempts will change it until points replenish. Bail out
        # of the whole run immediately rather than burning ~36 minutes
        # retrying every remaining variant into the same wall.
        if r.get('result') is False and 'Insufficient API points' in str(r.get('message')):
            raise CJUnavailable(str(r.get('message'))[:200])
        opts = r.get('data') or []
        if opts:
            break
        time.sleep(1.5 * (attempt + 1))

    inside = [o for o in opts if o.get('logisticPrice') is not None
              and upper_days(o.get('logisticAging')) <= MAX_DAYS]

    want = SELECTED_CARRIER.get(str(sku)[:11])
    for o in opts:
        if want and str(o.get('logisticName')).strip() == want:
            p = o.get('logisticPrice')
            if p and p > 0:
                return {'price': float(p), 'name': want, 'aging': o.get('logisticAging'),
                        'within_promise': bool(inside), 'estimated': False,
                        'answered': True}

    price, name, aging, estimated = freight_floor.resolve(opts)
    # `answered` separates two very different situations that both set
    # `estimated`:
    #   opts non-empty but all $0/placeholder -> CJ ANSWERED with missing data.
    #     Stable and known (the US-warehoused Ball Launcher does this on every
    #     call), so the documented fallback stands in and the variant is still
    #     judged.
    #   opts empty after retries -> CJ did NOT answer. Unknowable right now,
    #     and judging it means inventing a cost. The caller treats this as
    #     UNRESOLVED instead of as a breach.
    return {'price': price, 'name': f'{name} (selected carrier unavailable)',
            'aging': aging, 'within_promise': bool(inside),
            'estimated': estimated, 'answered': bool(opts)}


def main():
    apply_fix = '--apply' in sys.argv
    # --headroom prices against the stress case rather than today's quote, so a
    # variant still clears the floor after a routine CJ move instead of breaching
    # the moment anything shifts.
    headroom = '--headroom' in sys.argv
    override = None
    if '--margin' in sys.argv:
        override = float(sys.argv[sys.argv.index('--margin') + 1]) / 100.0

    src = (f'global {override:.0%}' if override is not None
           else f'price_book floors ({len(BOOK_FLOOR)} products)')
    print(f'Margin guard - {src}, carriers within {MAX_DAYS} days, '
          f'{"APPLY" if apply_fix else "report only"}\n')

    products = api('GET', 'products.json?limit=250&status=active')['products']
    costs = live_cj_costs([v.get('sku') for p in products for v in p['variants']])
    # How many variants SHOULD be graded, counted before a single CJ call. The
    # coverage gate below is denominated in this and nothing else. See the long
    # comment there for the bug that made the gate defeat itself.
    expected = sum(1 for p in products for v in p['variants'] if v.get('sku'))
    breaches, unresolved, thin, checked = [], [], [], 0
    streak, outage = 0, None

    for p in products:
        title = p['title']
        floor = override if override is not None else BOOK_FLOOR.get(
            str(p['id']), DEFAULT_FLOOR)
        rows = []
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            entry = costs.get(sku)
            if not entry:
                unresolved.append((title, v['title'], sku, 'no CJ record'))
                continue
            vid, cost = entry
            # Origin from the STOCK ROWS, never the SKU prefix. The CJBQ
            # heuristic quoted the CJCT-prefixed, US-warehoused Ball Launcher
            # from China, got no carriers, substituted a ~$21.50 estimate
            # against a real $11.00 domestic rate, and failed this job every
            # three hours on a breach that did not exist.
            start = freight_floor.origin_for(sku)
            duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
            try:
                fr = best_freight(vid, start, sku)
            except CJUnavailable as exc:
                outage = str(exc)
                break
            if fr.get('answered'):
                streak = 0
            else:
                streak += 1
                if streak >= OUTAGE_STREAK:
                    outage = (f'{streak} variants in a row returned no carrier; '
                              f'CJ is not answering')
                    unresolved.append((title, v['title'], sku,
                                       'CJ returned no carrier after 3 tries'))
                    break
            # `if not fr` was dead code: best_freight ALWAYS returns a dict, so
            # this never fired and a variant CJ would not quote fell through
            # with an invented freight figure and got judged on it. That is how
            # this job failed on 2026-08-19 with a breach that did not exist:
            # the Pumpkin Hoodie 9XL reads 29.3% on a real $7.10 quote and 4.2%
            # on the $11.00 no-quote fallback, against a 21.3% floor.
            #
            # An unanswered quote is UNKNOWN, never a finding - the same rule
            # guard_unshippable.py already follows and CLAUDE.md states
            # outright. A $0/placeholder answer is different: CJ did respond,
            # the condition is stable and documented, so the fallback stands
            # and the variant is still judged.
            if not fr.get('answered'):
                unresolved.append((title, v['title'], sku,
                                   'CJ returned no carrier after 3 tries'))
                continue
            checked += 1
            price = float(v['price'])
            need = floor_price(cost, fr['price'], duty, floor)
            if headroom:
                need = floor_price(cost * (1 + STRESS_COST),
                                   fr['price'] * (1 + STRESS_FREIGHT), duty, floor)
            m = margin_at(price, cost, fr['price'], duty) * 100
            # Headroom: how far freight can rise before this price breaches the
            # floor. The real exposure is not today's quote but tomorrow's.
            slack = price * (1 - PCT - floor) - cost * (1 + duty) - FLAT
            stress = margin_at(price, cost * (1 + STRESS_COST),
                               fr['price'] * (1 + STRESS_FREIGHT), duty) * 100
            rows.append((v, sku, cost, fr, price, need, m, slack, stress))
            if price < need - 0.005:
                breaches.append((p['id'], title, v, sku, cost, fr, price, need, m))
            elif stress < floor * 100:
                thin.append((title, str(v['title']), sku, price, m, stress, slack,
                             fr['price']))

        if outage:
            break
        if rows:
            safe = title.encode('ascii', 'replace').decode()
            print(f'{safe}  (floor {floor:.0%})')
            for v, sku, cost, fr, price, need, m, slack, stress in rows:
                flag = '' if price >= need - 0.005 else f'  <-- needs ${need:.2f}'
                warn = '' if fr['within_promise'] else '  (no carrier in window)'
                zero = '  (freight quoted $0 - unverified)' if fr['price'] == 0 else ''
                print(f'   {str(v["title"])[:28]:30} ${price:<7.2f} cost ${cost:<6.2f} '
                      f'frt ${fr["price"]:<6.2f} {m:5.1f}%  stress {stress:5.1f}%  '
                      f'frt headroom ${slack:5.2f}{flag}{warn}{zero}')
            print()

    print(f'{checked} of {expected} variants checked')
    for t, vt, sku, why in unresolved:
        print(f'  UNRESOLVED  {t[:30]:32} {str(vt)[:20]:22} {sku}  ({why})')
    # The abort reason was recorded and then never read: not printed, not
    # logged, not in the exit code. A run that stopped at variant 5 looked
    # exactly like a run that finished.
    if outage:
        print(f'\nSWEEP ABORTED: {outage}')

    if thin:
        print(f'\n{len(thin)} variant(s) compliant today but with no room - these '
              f'break first if CJ moves\n  (stress = cost +{STRESS_COST:.0%} and '
              f'freight +{STRESS_FREIGHT:.0%}):')
        for t, vt, sku, price, m, stress, slack, frt in sorted(thin, key=lambda r: r[5]):
            print(f'  {t[:32]:34} {vt[:18]:20} ${price:.2f}  now {m:.1f}%  '
                  f'stress {stress:.1f}%  freight headroom ${slack:.2f}')

    # A guard that verified almost nothing must not report success. Treating an
    # unanswered quote as UNKNOWN (rather than as a breach) is correct, but it
    # opens the opposite failure: if CJ is down or its daily points budget is
    # exhausted, every variant becomes UNKNOWN and the job would exit 0 having
    # checked nothing at all. So a run that could not grade most of the
    # catalogue fails loudly, and says clearly that it is a COVERAGE problem,
    # not a margin problem - the two need completely different responses.
    # DENOMINATED IN `expected`, NOT IN WHAT THE SWEEP HAPPENED TO REACH.
    #
    # This gate defeated itself until 2026-08-31. It read
    #     total_seen = checked + len(unresolved)
    # and both abort paths break out of the loop WITHOUT appending to
    # `unresolved` (the CJUnavailable branch appends nothing at all; the
    # OUTAGE_STREAK branch appends exactly one row). So a quota wall at variant
    # 5 gave total_seen = 4, coverage = 100%, the gate passed, and the job
    # printed "All variants clear their floors" and exited 0 having graded 4 of
    # 193. That is precisely the silent all-clear MIN_COVERAGE was written to
    # make impossible, reintroduced through the denominator.
    #
    # Counting against `expected` cannot be gamed by stopping early: variants
    # never reached are missing coverage, which is what they are.
    coverage = checked / expected if expected else 0.0
    if expected and (coverage < MIN_COVERAGE or outage):
        why = ('the sweep aborted' if outage else
               f'only {coverage:.0%} of variants got a real answer from CJ')
        print(f'\nCOULD NOT VERIFY: {checked}/{expected} variants graded '
              f'({coverage:.0%}) - {why}, below the {MIN_COVERAGE:.0%} minimum.')
        print('This is NOT a margin breach. Nothing is known to be wrong with '
              'any price. CJ did not answer often enough for this run to mean '
              'anything - most likely its daily API points budget '
              '(docs/knowledge/cj-api-points-quota.md) or a transient outage. '
              'Re-run once it recovers.')
        with open(LOG, 'w', encoding='utf-8') as fh:
            json.dump({'ran_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                       'result': 'insufficient_coverage',
                       'checked': checked, 'expected': expected,
                       'unresolved': len(unresolved), 'aborted': outage,
                       'coverage': round(coverage, 3)}, fh, indent=1)
        # 3, not 1. Exit 1 means "a price is wrong"; this means "we could not
        # tell". They need opposite responses, and conflating them is how a
        # five-day outage gets mistaken for a five-day pricing problem. Actions
        # fails on any non-zero, so the workflow needs no change.
        return 3

    if not breaches:
        print('\nAll variants clear their floors.')
    else:
        print(f'\n{len(breaches)} variant(s) below their floor:')
        for pid, t, v, sku, cost, fr, price, need, m in breaches:
            print(f'  {t[:32]:34} {str(v["title"])[:20]:22} '
                  f'${price:.2f} -> ${retail_round(need):.2f}  ({m:.1f}%)')
        if apply_fix:
            print()
            # One product can hold several breaching variants; Shopify wants each
            # variant PUT separately.
            for pid, t, v, sku, cost, fr, price, need, m in breaches:
                new = retail_round(need)
                api('PUT', f'variants/{v["id"]}.json',
                    {'variant': {'id': v['id'], 'price': f'{new:.2f}'}})
                print(f'  raised {t[:30]:32} {str(v["title"])[:18]:20} '
                      f'${price:.2f} -> ${new:.2f}')
        else:
            print('\nRun with --apply to raise these to clear the floor.')

    with open(LOG, 'w', encoding='utf-8') as fh:
        json.dump({'ran_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                   'floor': override if override is not None else 'price_book',
                   'applied': apply_fix, 'checked': checked,
                   'expected': expected, 'coverage': round(coverage, 3),
                   'breaches': [{'product': t, 'variant': str(v['title']),
                                 'sku': sku, 'price': price,
                                 'needed': round(need, 2), 'margin': round(m, 1)}
                                for _, t, v, sku, _, _, price, need, m in breaches],
                   'unresolved': [{'product': t, 'variant': str(vt), 'sku': s,
                                   'why': w} for t, vt, s, w in unresolved],
                   'thin': [{'product': t, 'variant': vt, 'sku': s, 'price': pr,
                             'margin': round(mg, 1), 'stress_margin': round(st, 1),
                             'freight_headroom': round(sl, 2), 'freight': fr}
                            for t, vt, s, pr, mg, st, sl, fr in thin]},
                  fh, indent=1)
    print(f'\nlog -> {os.path.relpath(LOG, ROOT)}')
    return 1 if (breaches and not apply_fix) else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(2)
