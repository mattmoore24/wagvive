#!/usr/bin/env python3
"""How many people buy at price p, given what the market charges.

A constant-elasticity curve q = (p/m)**-e is the textbook choice and it is wrong
here. It never reaches zero, so it will happily recommend pricing at twice the
market and claim the lost volume is worth the margin. Real shoppers comparing a
no-name store against Amazon simply stop considering you somewhere above the
premium brand, and the curve has to say so.

So demand is modelled as a share-of-consideration logistic in log price,
calibrated on the three observed band points rather than on an assumed
elasticity:

    share(p) = 1 / (1 + (p/mid) ** beta)

  * at the band MIDPOINT a shopper is indifferent, share = 0.50
  * at the band HIGH, the premium-brand price, an unbranded store keeps
    SHARE_AT_HIGH of that consideration
  * beta is solved from those two points, so a category with a wide band
    (mid $15, high $60: tolerant, brand matters) gets a gentle curve, and a
    tight band (mid $11, high $17: pure commodity) gets a brutal one

That single parameter does the work elasticity was doing, but it is derived from
observed prices instead of assumed, and it decays properly.

`e` from market_bands.py is still used, as a modifier on SHARE_AT_HIGH: outcome
goods (anxiety, cooling, dental) tolerate a premium better than a squeaky toy
does, independent of how wide the band happens to be.
"""
import math

# What share of consideration an unbranded store retains at the premium price.
# Anchored for a commodity; outcome goods get more, see share_at_high().
SHARE_AT_HIGH_BASE = 0.12


def share_at_high(e):
    """Differentiated goods keep more consideration at a premium price."""
    if e <= 1.8:
        return 0.28      # anxiety, cooling, sleep, dental: outcome buyers
    if e <= 2.2:
        return 0.18      # functional tools
    return SHARE_AT_HIGH_BASE


def beta(mid, high, e):
    """Solve share(high) = share_at_high(e) for the logistic exponent."""
    s = share_at_high(e)
    ratio = max(high / mid, 1.01)
    return math.log((1 - s) / s) / math.log(ratio)


def share(price, mid, high, e):
    """Relative probability of winning the sale at this price. 0.5 at mid."""
    b = beta(mid, high, e)
    return 1.0 / (1.0 + (max(price, 0.01) / mid) ** b)


def contribution(price, unit_cost, fee_pct=0.029):
    return price - unit_cost - fee_pct * price


def best_price(unit_cost, low, mid, high, e, lo=None, hi=None, step=0.01):
    """Price maximising contribution x share, searched over a sane range.

    Searched rather than solved: the logistic has no closed form, and a cent-by-
    cent sweep over a $200 range is a few thousand evaluations.
    """
    lo = lo if lo is not None else max(unit_cost * 1.02, low * 0.6)
    hi = hi if hi is not None else high * 1.6
    best, best_val = lo, -1e9
    p = lo
    while p <= hi:
        v = contribution(p, unit_cost) * share(p, mid, high, e)
        if v > best_val:
            best_val, best = v, p
        p += step
    return best, best_val
