#!/usr/bin/env python3
"""
Wagvive margin rule: no order type ever returns less than 50% margin after
every cost - product, freight, payment processing, and duty.

    margin = (price - product - freight - duty - fee) / price >= FLOOR

with fee = PCT * price + FLAT (Shopify Payments), duty = DUTY_PCT * product.

Solving for the minimum price:

    price * (1 - PCT - FLOOR) >= product * (1 + DUTY_PCT) + freight + FLAT
    price >= (product * (1 + DUTY_PCT) + freight + FLAT) / (1 - PCT - FLOOR)

FREIGHT_BUFFER guards against CJ quote drift and the $0.00 quotes the calculator
returns for US-warehouse items, which are not yet verified against a real order.

CLI:
    python config/pricing.py 22.99 0        # product cost, freight
    python config/pricing.py 3.37 5.10 --at 32
"""
import sys

FLOOR = 0.50          # required margin
PCT = 0.029           # Shopify Payments percentage
FLAT = 0.30           # Shopify Payments per-transaction
FREIGHT_BUFFER = 6.00  # absorb an unquoted/underquoted freight surprise

# Shopify Payments takes 2.9% of the WHOLE order - item + shipping + sales tax -
# not just the item price. Sales tax itself is a pass-through (collected from the
# customer, remitted to the state) and is correctly NOT a margin cost, but the
# card fee charged on top of it is ours. ~7% is a mid US combined rate.
SALES_TAX_AVG = 0.07

# 30-day returns. Faulty/wrong items cost us the refund, the original freight and
# the return shipping; change-of-mind returns cost the freight. Modelled as an
# expected loss on landed cost per order. Set to 0.0 to price ex-returns.
RETURNS_RATE = 0.03

# CJ's freight calculator returns $0.00 for this US-warehouse SKU on all three
# carriers (UPS/FedEx/USPS) at every quantity tested, including 20 units - i.e.
# missing data, not free carriage. The item is 450g but packs to a mailer where
# dimensional weight governs, giving roughly 3-4 lb billable; US ground at that
# weight runs about $8-12. $11 is the planning figure until a real order settles
# it. Applied by config/freight_floor.py wherever a quote comes back at zero.
US_DOMESTIC_FREIGHT_FALLBACK = 11.00

# US import duty, checked against Zonos postal tariff guidance as of 2026-07-24.
# De minimis is permanently suspended, so every parcel is dutiable regardless of
# value. For China-origin postal parcels the stack is:
#   Section 301 forced-labour tariff   10-12.5%   (China is in scope)
#   MFN rate per HTS code              ~3-7%      (plastic/textile pet goods)
#   Section 232                        n/a        (not steel/aluminium articles)
# Two things that circulated widely are NOT in force: the IEEPA China tariffs
# ended 2026-02-24, and the Section 122 flat 10% surcharge expired 2026-07-24.
# Blog claims of a 54% rate or a $100-per-package floor do not match the
# customs guidance and are not used here.
#
# 20% is deliberately above the 12.5% + ~5% midpoint so a rate move or a
# worse-than-expected HTS classification does not silently breach the floor.
DUTY_PCT = 0.20

# Goods already sitting in a US warehouse were imported by the supplier, so no
# duty is charged again when the customer orders.
DUTY_PCT_US_WAREHOUSE = 0.00


def landed(product, freight, duty_pct=DUTY_PCT, returns=RETURNS_RATE):
    """Per-unit cost that does not vary with price: goods, duty, freight, and the
    expected cost of the share of orders that come back."""
    base = product * (1 + duty_pct) + freight
    return base * (1 + returns)


def _fee_rate():
    """Card fee as a fraction of item price, allowing for the fee being charged on
    sales tax as well."""
    return PCT * (1 + SALES_TAX_AVG)


def min_price(product, freight, duty_pct=DUTY_PCT, floor=FLOOR, buffer=0.0,
              returns=RETURNS_RATE):
    """Lowest price that still clears `floor` margin.

        price * (1 - fee_rate - floor) >= landed + buffer + FLAT
    """
    numerator = landed(product, freight, duty_pct, returns) + buffer + FLAT
    denominator = 1 - _fee_rate() - floor
    if denominator <= 0:
        raise ValueError('floor + processing pct must be under 1')
    return numerator / denominator


def margin(price, product, freight, duty_pct=DUTY_PCT, returns=RETURNS_RATE):
    """Actual margin at a given price."""
    cost = landed(product, freight, duty_pct, returns) + _fee_rate() * price + FLAT
    return (price - cost) / price if price else 0.0


def retail_round(p):
    """Round up to the next .00 that ends in 2, 4, 6, 8 or 9 - keeps prices tidy
    without ever rounding down through the floor."""
    import math
    n = math.ceil(p)
    while n % 10 not in (2, 4, 6, 8, 9, 0):
        n += 1
    return float(n)


def plan(product, freight, label=''):
    bare = min_price(product, freight)
    safe = min_price(product, freight, buffer=FREIGHT_BUFFER)
    rec = retail_round(safe)
    return {
        'label': label, 'product': product, 'freight': freight,
        'min_price': round(bare, 2),
        'min_price_buffered': round(safe, 2),
        'recommended': rec,
        'margin_at_rec': round(margin(rec, product, freight) * 100, 1),
        'margin_if_freight_plus_buffer': round(
            margin(rec, product, freight + FREIGHT_BUFFER) * 100, 1),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        print(__doc__)
        return
    product, freight = float(args[0]), float(args[1])
    p = plan(product, freight)
    print(f'product ${product:.2f}  freight ${freight:.2f}')
    print(f'  min price for {FLOOR:.0%} margin      ${p["min_price"]:.2f}')
    print(f'  min price with ${FREIGHT_BUFFER:.0f} freight buffer  ${p["min_price_buffered"]:.2f}')
    print(f'  recommended                     ${p["recommended"]:.2f}'
          f'   -> {p["margin_at_rec"]}% margin')
    print(f'  same price if freight rises ${FREIGHT_BUFFER:.0f}   -> '
          f'{p["margin_if_freight_plus_buffer"]}% margin')
    if '--at' in sys.argv:
        at = float(sys.argv[sys.argv.index('--at') + 1])
        print(f'  at ${at:.2f}                        -> '
              f'{margin(at, product, freight) * 100:.1f}% margin')


if __name__ == '__main__':
    main()
