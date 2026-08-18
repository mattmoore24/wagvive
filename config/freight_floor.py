#!/usr/bin/env python3
"""One place that decides what freight to trust for a variant.

CJ's freight calculator sometimes returns a quote of $0.00. That is missing data,
never free carriage - for the US-warehouse Furniture Cover it returns $0.00 on
UPS, FedEx and USPS alike, at 1, 5 and 20 units. Taking it at face value made the
item look like a 60.7% margin product when its true margin is well under the
floor.

A zero is not the only shape the bug takes. On 2026-08-04 a freight study across
all 36 catalogue products found the Self-Cleaning Slicker Brush (80g) and the
Cordless Paw Trimmer (160g) each returning exactly ONE carrier, "Yunexpress CN to
US", at exactly $3.00 - while every other product in the catalogue was offered 19
to 27 carriers starting at $4.28. The same $3.00 came back for a 1913g two-item
basket containing the brush, which is not a price any carrier charges for two
kilos. It is a placeholder, and it had both products looking profitable on
freight that does not exist.

So `resolve()` now rejects a quote that is below what any real parcel costs, the
same way it rejects a zero, and substitutes an estimate instead of a fallback
constant where a weight is known.

The estimate comes from the same study. Across 34 products with credible quotes,
cheapest-carrier freight tracks weight almost exactly:

    30g $4.75   100g $5.59   200g $6.87   490g $10.08   1220g $18.63   1833g $26.59

which is a straight line, about $4.40 of fixed parcel cost plus $12.11 per kilo.
That fixed component is also the whole case for kits: every ADDITIONAL parcel in
an order costs $4.40 before it carries a single gram.

Every pricing path should resolve freight through `resolve()` so a zero, or a
placeholder, can never quietly become profit again.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import US_DOMESTIC_FREIGHT_FALLBACK

# Delivery window published at checkout and on the FAQ / Shipping pages.
MAX_DAYS = 12

# Fitted 2026-08-04 over every catalogue product whose quote was credible.
# See docs/qa/freight-research.json for the observations.
FREIGHT_BASE = 4.40         # fixed cost of putting one parcel on a plane
FREIGHT_PER_GRAM = 0.01211  # $12.11 per kg on top

# The cheapest credible quote in that study was $4.28, for a 6g comb. Nothing
# real ships from China for less, so anything under this is missing data. Used
# only when no weight is available.
MIN_CREDIBLE_FREIGHT = 4.00

# With a weight, a better test than a flat floor: reject anything far below what
# the fitted line says a parcel of that weight costs. The fit's worst residual
# anywhere was $1.56, so 75% leaves ample room for a genuinely cheap carrier
# while still catching a placeholder. It has to be weight-relative, because the
# Cordless Paw Trimmer's second bogus line quotes $4.00 for 160g - above a flat
# $4.00 floor, but well under the $6.34 that weight really costs.
CREDIBLE_FRACTION = 0.75


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def estimate(weight_g=None):
    """Planning freight for a parcel of a given weight, China to US."""
    if not weight_g:
        return US_DOMESTIC_FREIGHT_FALLBACK
    return FREIGHT_BASE + FREIGHT_PER_GRAM * float(weight_g)


def credible_floor(weight_g=None):
    """Below this, a quote is missing data rather than a bargain."""
    if weight_g:
        return CREDIBLE_FRACTION * estimate(weight_g)
    return MIN_CREDIBLE_FREIGHT


def _pick(rows, weight_g):
    """rows are (price, name, aging, days). Returns the resolve() tuple."""
    if not rows:
        return estimate(weight_g), 'no quote', None, True

    inside = [r for r in rows if r[3] <= MAX_DAYS]
    pool = inside or rows

    # Discard placeholder prices before choosing, so one bogus $3.00 line cannot
    # win on price against 26 real ones.
    floor = credible_floor(weight_g)
    credible = [r for r in pool if r[0] >= floor]
    if credible:
        best = min(credible, key=lambda r: r[0])
        return best[0], best[1], best[2], False

    # Everything on offer was zero or a placeholder.
    best = min(pool, key=lambda r: r[0])
    return estimate(weight_g), best[1], best[2], True


def resolve(options, sku='', weight_g=None):
    """Pick the cheapest carrier inside the delivery promise.

    Returns (freight, carrier_name, aging, estimated) where `estimated` is True
    when the quote was unusable and an estimate was substituted.
    """
    rows = [(float(o['logisticPrice']), str(o.get('logisticName')),
             o.get('logisticAging'), upper_days(o.get('logisticAging')))
            for o in (options or []) if o.get('logisticPrice') is not None]
    return _pick(rows, weight_g)


def resolve_from_menu(menu, weight_g=None):
    """Same decision, applied to a stored carrier menu.

    `config/research_freight.py` records every carrier CJ offered for a product,
    so the choice can be recomputed offline whenever the rule changes, without
    re-querying CJ. That makes the rule authoritative and the freight figure
    stored alongside it merely a snapshot.
    """
    rows = [(o['price'], o.get('carrier'), o.get('aging'),
             o.get('days', upper_days(o.get('aging'))))
            for o in (menu or []) if o.get('price')]
    return _pick(rows, weight_g)


# --- where a SKU actually ships FROM -----------------------------------------
# Added 2026-08-18 after the scheduled job failed every 3 hours for a day.
#
# Ten scripts decided shipping origin with `sku.startswith('CJBQ')`. That
# heuristic is WRONG and it cost real money in false alarms: the Automatic Ball
# Launcher is `CJCT25677400001`, and it IS US-warehoused, so margin_guard quoted
# it from China, got zero carrier options back, substituted an estimate of about
# $21.50 against a real domestic rate of $11.00, and reported a margin breach
# that did not exist. The job is designed to fail on a breach, so the owner got
# a failure notification every three hours.
#
# Origin lives in the STOCK ROWS, which is the only place that actually knows.
# `countryCode == 'US'` on any row means CJ holds it in a US warehouse: no duty,
# and flat domestic freight instead of weight-scaled international.
_ORIGIN_CACHE = {}


def origin_for(sku, default='CN'):
    """'US' or 'CN' for a variant SKU, read from CJ's stock rows.

    Cached per process because a catalogue sweep asks the same question 145
    times. On any error the answer is the conservative one, `default='CN'`,
    which prices freight HIGHER rather than lower: a wrong guess that way costs
    margin headroom, the other way silently sells under the floor.
    """
    sku = str(sku or '')
    if not sku:
        return default
    # Cached by SPU (sku[:11]), not by variant sku. A warehouse is a property of
    # the PRODUCT, so all its variants share the answer, and margin_guard walks
    # 258 variants across about 38 SPUs. Keying per variant made this one stock
    # call each and pushed the scheduled job toward its 30 minute timeout.
    spu = sku[:11]
    if spu in _ORIGIN_CACHE:
        return _ORIGIN_CACHE[spu]
    origin = default
    try:
        import cj_api
        rows = cj_api.call('/product/stock/queryBySku', {'sku': sku}).get('data')
        if isinstance(rows, list) and rows:
            origin = ('US' if any((r.get('countryCode') or '').upper() == 'US'
                                  for r in rows) else 'CN')
    except Exception:
        pass
    _ORIGIN_CACHE[spu] = origin
    return origin
