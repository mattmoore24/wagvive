#!/usr/bin/env python3
"""One place that decides what freight to trust for a variant.

CJ's freight calculator sometimes returns a quote of $0.00. That is missing data,
never free carriage - for the US-warehouse Furniture Cover it returns $0.00 on
UPS, FedEx and USPS alike, at 1, 5 and 20 units. Taking it at face value made the
item look like a 60.7% margin product when its true margin is well under the
floor.

Every pricing path should resolve freight through `resolve()` so a zero can never
quietly become profit again.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import US_DOMESTIC_FREIGHT_FALLBACK

# Delivery window published at checkout and on the FAQ / Shipping pages.
MAX_DAYS = 12


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def resolve(options, sku=''):
    """Pick the cheapest carrier inside the delivery promise.

    Returns (freight, carrier_name, aging, estimated) where `estimated` is True
    when the quote was unusable and the fallback was substituted.
    """
    priced = [o for o in (options or []) if o.get('logisticPrice') is not None]
    if not priced:
        return US_DOMESTIC_FREIGHT_FALLBACK, 'no quote', None, True

    inside = [o for o in priced if upper_days(o.get('logisticAging')) <= MAX_DAYS]
    pool = inside or priced
    best = min(pool, key=lambda o: o['logisticPrice'])
    price = float(best['logisticPrice'])

    if price <= 0:
        # Carriers were returned but unpriced - substitute rather than book $0.
        return (US_DOMESTIC_FREIGHT_FALLBACK, str(best.get('logisticName')),
                best.get('logisticAging'), True)

    return price, str(best.get('logisticName')), best.get('logisticAging'), False
