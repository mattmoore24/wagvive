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
# real ships from China for less, so anything under this is missing data.
MIN_CREDIBLE_FREIGHT = 4.00


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def estimate(weight_g=None):
    """Planning freight for a parcel of a given weight, China to US."""
    if not weight_g:
        return US_DOMESTIC_FREIGHT_FALLBACK
    return FREIGHT_BASE + FREIGHT_PER_GRAM * float(weight_g)


def resolve(options, sku='', weight_g=None):
    """Pick the cheapest carrier inside the delivery promise.

    Returns (freight, carrier_name, aging, estimated) where `estimated` is True
    when the quote was unusable and an estimate was substituted.
    """
    priced = [o for o in (options or []) if o.get('logisticPrice') is not None]
    if not priced:
        return estimate(weight_g), 'no quote', None, True

    inside = [o for o in priced if upper_days(o.get('logisticAging')) <= MAX_DAYS]
    pool = inside or priced

    # Discard placeholder prices before choosing, so one bogus $3.00 line cannot
    # win on price against 26 real ones.
    credible = [o for o in pool if float(o['logisticPrice']) >= MIN_CREDIBLE_FREIGHT]
    if credible:
        best = min(credible, key=lambda o: o['logisticPrice'])
        return (float(best['logisticPrice']), str(best.get('logisticName')),
                best.get('logisticAging'), False)

    # Everything on offer was zero or a placeholder.
    best = min(pool, key=lambda o: o['logisticPrice'])
    return (estimate(weight_g), str(best.get('logisticName')),
            best.get('logisticAging'), True)
