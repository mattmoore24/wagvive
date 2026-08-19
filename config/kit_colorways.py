#!/usr/bin/env python3
"""The kit option design: one Size choice, one Colorway choice. Source of truth.

WHY THIS SHAPE. A kit should let the shopper choose what they receive. Doing that
per component is impossible on Shopify: products cap at 3 options and 2048
variants, and every kit needs 4 or 5 option slots once each component's choices
are counted. The Travel Kit alone would need 2 x 16 x 9 x 9 x 6 = 15,552
variants, 7.6x the ceiling. Verified against the API docs, error code
OPTIONS_OVER_LIMIT, "Can only specify a maximum of 3 options".

So the choice is collapsed along the two axes a dog owner actually cares about:

  Size      one pick that drives EVERY size-varying component at once. A shopper
            should not have to know that the robe runs XS-M while the cooling pad
            runs Medium-XXL; they know their dog.
  Colorway  a curated set where every component's color is chosen to go together.

That is 2 options with one slot spare, 39 kit variants across the whole range
instead of 234, and nothing is silently chosen: every component's variant is
determined by, and stated from, the two picks.

RULES FOR EDITING THIS FILE
  * Every color and size string here must EXACTLY match a live option value on
    the component product. Values are lifted from the catalogue, not invented; a
    typo produces a kit variant that maps to no real SKU and cannot be fulfilled.
    `rebuild_kits.py` validates every one against the live catalogue before it
    writes anything.
  * Single-variant components have no choice to express, so they cannot appear in
    a colorway map. List them in `fixed` instead. `fixed` is NOT optional
    decoration: composition is derived from this file, so a single-variant
    component missing from `fixed` is DROPPED from the kit. Inferring them from
    the live bundle instead is what made the Watermelon Rope Frisbee impossible
    to remove from the Toy Kit even after CJ stopped being able to ship it.
  * Keep colorways coherent. The whole justification for this design is that the
    curated set looks considered; a mismatched set is worse than a random one.
  * `price` and `compare_at` live here too, because a composition change IS a
    price change and the two must move together. `compare_at` is the honest sum
    of buying every component separately at its own live retail price, and it has
    to come out the SAME for every colorway or the advertised saving would depend
    on which colour the shopper picked. `verify_kit_compare_at.py` proves both.
    Previously the price was read back from `config/kit-backup/`, which meant a
    rebuild after a composition change re-applied the OLD kit's price to the new
    kit.
"""

# Kit size -> the size value to use on each size-varying component.
# The blanket only comes in S and M, so Large reuses M: that is the largest the
# supplier makes, not an oversight.
SIZE_MAP = {
    'S': {'Paw Print Fleece Blanket': 'S',
          'Quick-Dry Bath Robe':      'S',
          'Paw Washing Cup':          'S',
          'Cooling Comfort Pad':      'M'},
    'M': {'Paw Print Fleece Blanket': 'L',
          'Quick-Dry Bath Robe':      'M',
          'Paw Washing Cup':          'M',
          'Cooling Comfort Pad':      'L'},
    'L': {'Paw Print Fleece Blanket': 'L',
          'Quick-Dry Bath Robe':      'L',
          'Paw Washing Cup':          'L',
          'Cooling Comfort Pad':      'XL'},
}

# Per kit: the option that is NOT size, and what each of its values fixes.
# 'option' is the customer-facing option name. The Toy Kit's components vary by
# character rather than color, so its option is named accordingly.
KITS = {
    'New Puppy Kit': {
        'option': 'Colorway',
        'price': '54.00', 'compare_at': '66.95',
        'sizes': ['S', 'M'],          # only the blanket varies by size
        'fixed': ['Cuddle Companion Teddy'],
        'values': {
            'Blue': {
                'Sneaker Chew Buddy':      'Blue',
                'Paw Print Fleece Blanket': 'Beige',
                'LED Waste Bag Dispenser': 'Blue',
                'Finger Toothbrush':       'Blue',
            },
            'Pink': {
                'Sneaker Chew Buddy':      'Sea Fog Blue',
                'Paw Print Fleece Blanket': 'Pink',
                'LED Waste Bag Dispenser': 'Pink',
                'Finger Toothbrush':       'White',
            },
            'Natural': {
                'Sneaker Chew Buddy':      'Black',
                'Paw Print Fleece Blanket': 'Camel',
                'LED Waste Bag Dispenser': 'Grey',
                'Finger Toothbrush':       'Dark Blue',
            },
        },
    },

    # 2026-08-17: the Watermelon Rope Frisbee was REMOVED from this kit. CJ has
    # no stock record for it (stock:null) so it cannot be shipped, which is what
    # broke order #1002's sibling case. Replaced by the Woodland Rope-Limb Plush:
    # it keeps the rope/tug play the frisbee provided AND has six characters, so
    # it maps onto the character sets instead of being one fixed item.
    'Toy Kit': {
        'option': 'Character set',
        # $49.00/$60.95 before the swap. The plush retails $1.00 above the
        # frisbee, so both numbers move by that and the saving stays 20.6%.
        'price': '50.00', 'compare_at': '62.95',
        'sizes': None,                          # nothing in this kit has a size
        'fixed': [],        # the Watermelon Rope Frisbee used to live here
        'values': {
            'Farmyard': {
                'Barnyard Squeaker':   'Green Dog',
                'Woodland Rope-Limb Plush': 'Rabbit',
                'Sneaker Chew Buddy':  'Blue',
                'Jingle Plush Ball':   'Monkey',
                'Corduroy Squeak Pals': 'Fawn',
            },
            'Safari': {
                'Barnyard Squeaker':   'Giraffe',
                'Woodland Rope-Limb Plush': 'Tiger',
                'Sneaker Chew Buddy':  'Black',
                'Jingle Plush Ball':   'Frog',
                'Corduroy Squeak Pals': 'Frog',
            },
            'Puppy Pack': {
                'Barnyard Squeaker':   'Puppy',
                'Woodland Rope-Limb Plush': 'Fox',
                'Sneaker Chew Buddy':  'Sea Fog Blue',
                'Jingle Plush Ball':   'Dog',
                'Corduroy Squeak Pals': 'Crooked Neck',
            },
        },
    },

    'Grooming Essentials Kit': {
        'option': 'Colorway',
        'price': '70.00', 'compare_at': '86.95',
        'sizes': ['S', 'M', 'L'],
        'values': {
            'Green': {
                'Self-Cleaning Slicker Brush': 'Green',
                'Quiet Electric Nail Grinder': 'Deep Green',
                'Quick-Dry Bath Robe':         'Green',
                'Finger Toothbrush':           'Blue',
                'Paw Washing Cup':             'Green',
            },
            'Pink': {
                'Self-Cleaning Slicker Brush': 'Pink',
                'Quiet Electric Nail Grinder': 'Pure White',
                'Quick-Dry Bath Robe':         'Pink',
                'Finger Toothbrush':           'White',
                'Paw Washing Cup':             'Blue',
            },
            'Orange': {
                'Self-Cleaning Slicker Brush': 'Orange',
                'Quiet Electric Nail Grinder': 'Pure White',
                'Quick-Dry Bath Robe':         'Blue',
                'Finger Toothbrush':           'Orange',
                'Paw Washing Cup':             'Orange',
            },
        },
    },

    # 2026-08-17: the Bouncy Egg Squeaker was REMOVED. It is the item that made
    # order #1002 (CJ DP2608121816000646700) ship short: CJ advertised 44,838
    # while holding no stock record at all. Replaced by the Dental Chew Stick,
    # which is verified shippable and does the same job for the kit's promise,
    # giving a bored dog something self-directed to work at.
    'Dog Enrichment Kit': {
        'option': 'Colorway',
        # $46.00/$57.96 before the swap. The Dental Chew Stick retails $5.00
        # above the egg it replaces, so the kit rises $4.00 and the saving
        # improves slightly, from 20.6% to 20.6% on a bigger basket.
        'price': '50.00', 'compare_at': '62.96',
        'sizes': None,
        'values': {
            'Green': {
                'Slow Feeder Bowl':   'Green',
                'Lick Bowl with Ball': 'Grey',
                'Talk Button':        'Green',
                'Dental Chew Stick':  'Green',
            },
            'Pink': {
                'Slow Feeder Bowl':   'Pink',
                'Lick Bowl with Ball': 'Black',
                'Talk Button':        'Pink',
                'Dental Chew Stick':  'Teal',
            },
            'Sunshine': {
                'Slow Feeder Bowl':   'Orange',
                'Lick Bowl with Ball': 'Yellow',
                'Talk Button':        'Yellow',
                'Dental Chew Stick':  'Yellow',
            },
        },
    },

    'Travel Kit': {
        'option': 'Colorway',
        'price': '85.00', 'compare_at': '105.95',
        'sizes': ['S', 'M', 'L'],
        'values': {
            'Blue': {
                'Travel Water Bottle & Bowl': 'Blue',
                'Cooling Comfort Pad':        'Dark Blue',
                'Paw Washing Cup':            'Blue',
                'Quick-Dry Bath Robe':        'Blue',
                'Paw Print Fleece Blanket':   'Beige',
            },
            'Pink': {
                'Travel Water Bottle & Bowl': 'Pink',
                'Cooling Comfort Pad':        'Pink',
                'Paw Washing Cup':            'Orange',
                'Quick-Dry Bath Robe':        'Pink',
                'Paw Print Fleece Blanket':   'Pink',
            },
            'Natural': {
                'Travel Water Bottle & Bowl': 'Blue',
                'Cooling Comfort Pad':        'Coffee',
                'Paw Washing Cup':            'Green',
                'Quick-Dry Bath Robe':        'Green',
                'Paw Print Fleece Blanket':   'Camel',
            },
        },
    },

    'Calm & Comfort Kit': {
        'option': 'Colorway',
        'price': '109.00', 'compare_at': '135.95',
        'sizes': ['S', 'M', 'L'],
        'fixed': ['Heartbeat Soothing Sloth'],
        'values': {
            'Grey': {
                'Calming Thunder Wrap':     'Grey',
                'Paw Print Fleece Blanket': 'Beige',
                'Cooling Comfort Pad':      'Light Grey',
                'Big Squeak Plush':         'Blue',
            },
            'Blue': {
                'Calming Thunder Wrap':     'Dark Blue',
                'Paw Print Fleece Blanket': 'Camel',
                'Cooling Comfort Pad':      'Dark Blue',
                'Big Squeak Plush':         'Blue',
            },
            'Pink': {
                'Calming Thunder Wrap':     'Grey and Blue',
                'Paw Print Fleece Blanket': 'Pink',
                'Cooling Comfort Pad':      'Pink',
                'Big Squeak Plush':         'Orange',
            },
        },
    },
}


def plan():
    """(kit, [option names], [(size, colorway), ...]) for each kit."""
    out = []
    for kit, spec in KITS.items():
        sizes = spec['sizes']
        combos = ([(s, c) for s in sizes for c in spec['values']]
                  if sizes else [(None, c) for c in spec['values']])
        names = (['Size', spec['option']] if sizes else [spec['option']])
        out.append((kit, names, combos))
    return out


if __name__ == '__main__':
    total = 0
    for kit, names, combos in plan():
        print(f'{kit:26} options={names}  {len(combos)} variants')
        total += len(combos)
    print(f'\n{total} kit variants in total (was 234)')
