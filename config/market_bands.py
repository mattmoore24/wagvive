#!/usr/bin/env python3
"""Observed US market price bands per product, and the elasticity to price at.

WHY THIS REPLACES THE OLD SINGLE NUMBER
---------------------------------------
The 2026-08-04 pricing study recorded one `market_delivered` figure per product.
Spot-checking it against live listings showed it had frequently captured the
PREMIUM BRAND rather than the volume seller, which is the price a shopper
actually compares us against:

  * Dog nail grinder      study $50.00   Dremel PawControl is $45-60, but the
                                         volume seller is Casfuy at ~$20 with
                                         88,000 reviews.
  * Self-cleaning slicker study $29.99   Amazon listings start at $9.90.
  * Slow feeder bowl      study $19.99   Outward Hound, the category brand,
                                         starts at $8.99.
  * Paw cleaner cup       study $23.99   Dexas MudBuster $10.12 to $25.

We are an unbranded store with zero reviews, so we cannot hold a premium-brand
price. Each product therefore carries a band:

    low   what the cheapest credible competitor charges (delivered)
    mid   where the bulk of the volume sits
    high  the premium brand, reachable only with brand equity we do not have

ELASTICITY
----------
`e` is the own-price elasticity assumed for the category. Pet supplies are
generally elastic; commodity toys with dozens of near-identical substitutes are
very elastic, while anxiety, cooling and health items are differentiated by
outcome rather than features and are much less so.

    3.0  commodity: plush and rubber toys, generic accessories
    2.5  semi-commodity: bowls, waste and walk accessories
    2.0  tools with a functional claim: brushes, combs, clippers
    1.6  outcome goods: anxiety, cooling, sleep, dental health

With constant elasticity the contribution-maximising price is the textbook
markup  p* = c * e / (e - 1)  over variable cost c. That is what
`optimise_prices.py` uses, then caps it against this band.

`conf` records how the band was set: 'live' from a 2026-08-04 search,
'category' inferred from a sibling product in the same category.
"""

# product title (without the "Wagvive " prefix) -> band
BANDS = {
    # --- outcome goods: cooling, anxiety, sleep -------------------------------
    'Cooling Comfort Pad':            dict(low=12.00, mid=29.99, high=59.99, e=1.6, conf='live'),
    'Calming Thunder Wrap':           dict(low=14.99, mid=27.99, high=44.95, e=1.6, conf='live'),
    'Heartbeat Soothing Sloth':       dict(low=19.99, mid=29.99, high=49.95, e=1.6, conf='category'),
    'Waterproof Snuggle Blanket':     dict(low=14.99, mid=24.99, high=39.99, e=2.0, conf='category'),
    'Paw Print Fleece Blanket':       dict(low=11.99, mid=17.99, high=29.99, e=2.5, conf='category'),
    'Waterproof Sofa & Furniture Cover': dict(low=19.99, mid=32.99, high=59.99, e=2.0, conf='category'),

    # --- grooming tools -------------------------------------------------------
    'Quiet Electric Nail Grinder':    dict(low=15.99, mid=22.99, high=59.99, e=2.0, conf='live'),
    'LED Nail Clippers':              dict(low=8.99,  mid=14.99, high=24.99, e=2.2, conf='category'),
    'Self-Cleaning Slicker Brush':    dict(low=9.90,  mid=15.99, high=29.99, e=2.0, conf='live'),
    'Dematting Comb':                 dict(low=8.99,  mid=14.99, high=24.99, e=2.0, conf='category'),
    'Pet Hair Remover Mitt':          dict(low=6.99,  mid=11.99, high=19.99, e=2.5, conf='category'),
    'Cordless Paw Trimmer':           dict(low=15.99, mid=24.99, high=39.99, e=2.0, conf='category'),
    'Quick-Dry Bath Robe':            dict(low=12.99, mid=19.99, high=29.99, e=2.2, conf='live'),
    'Paw Washing Cup':                dict(low=10.12, mid=17.99, high=25.00, e=2.2, conf='live'),

    # --- dental ---------------------------------------------------------------
    'Dental & Ear Wipes':             dict(low=7.99,  mid=12.99, high=19.99, e=1.8, conf='category'),
    'Finger Toothbrush':              dict(low=5.99,  mid=9.99,  high=14.99, e=1.8, conf='category'),

    # --- bowls, feeding, water ------------------------------------------------
    'Slow Feeder Bowl':               dict(low=8.99,  mid=14.99, high=24.99, e=2.5, conf='live'),
    'Lick Bowl with Ball':            dict(low=9.99,  mid=15.99, high=24.99, e=2.5, conf='category'),
    'Anti-Spill Floating Water Bowl': dict(low=14.99, mid=24.99, high=39.99, e=2.2, conf='category'),
    'Travel Water Bottle & Bowl':     dict(low=12.99, mid=19.99, high=32.99, e=2.2, conf='category'),

    # --- walk and waste -------------------------------------------------------
    'LED Waste Bag Dispenser':        dict(low=7.99,  mid=11.99, high=17.99, e=2.5, conf='category'),

    # --- enrichment -----------------------------------------------------------
    'Talk Button':                    dict(low=9.99,  mid=17.99, high=29.99, e=2.0, conf='category'),

    # --- toys: commodity, dozens of near-identical substitutes ----------------
    'Dental Duck Chew Toy':           dict(low=6.99,  mid=10.99, high=16.99, e=3.0, conf='category'),
    'Crinkle Plush Buddy':            dict(low=5.99,  mid=8.99,  high=14.99, e=3.0, conf='category'),
    'Woodland Rope-Limb Plush':       dict(low=7.99,  mid=12.99, high=19.99, e=3.0, conf='category'),
    'Rope-Limb Puppy Plush':          dict(low=8.99,  mid=14.99, high=21.99, e=3.0, conf='category'),
    'Squirrel Squeaky Plush':         dict(low=9.99,  mid=15.99, high=24.99, e=3.0, conf='category'),
    'Big Squeak Plush':               dict(low=12.99, mid=19.99, high=29.99, e=3.0, conf='category'),
    'Cuddle Companion Teddy':         dict(low=9.99,  mid=15.99, high=24.99, e=3.0, conf='category'),
    'Jingle Plush Ball':              dict(low=8.99,  mid=13.99, high=21.99, e=3.0, conf='category'),
    'Corduroy Squeak Pals':           dict(low=7.99,  mid=12.99, high=19.99, e=3.0, conf='category'),
    'Barnyard Squeaker':              dict(low=7.99,  mid=12.99, high=19.99, e=3.0, conf='category'),
    'Screaming Chicken':              dict(low=7.99,  mid=12.99, high=19.99, e=3.0, conf='category'),
    'Sneaker Chew Buddy':             dict(low=8.99,  mid=13.99, high=19.99, e=3.0, conf='category'),
    'Bouncy Egg Squeaker':            dict(low=6.99,  mid=10.99, high=16.99, e=3.0, conf='category'),
    'Watermelon Rope Frisbee':        dict(low=7.99,  mid=11.99, high=17.99, e=3.0, conf='category'),
}


def band(title):
    return BANDS.get(title.replace('Wagvive ', '').strip())
