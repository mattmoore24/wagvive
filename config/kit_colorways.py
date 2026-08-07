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
  * A component absent from a colorway map is single-variant and needs no choice.
  * Keep colorways coherent. The whole justification for this design is that the
    curated set looks considered; a mismatched set is worse than a random one.
"""

# Kit size -> the size value to use on each size-varying component.
# The blanket only comes in S and M, so Large reuses M: that is the largest the
# supplier makes, not an oversight.
SIZE_MAP = {
    'Small':  {'Paw Print Fleece Blanket': 'S',
               'Quick-Dry Bath Robe':      'XS',
               'Paw Washing Cup':          'S',
               'Cooling Comfort Pad':      'Medium 24" x 20"'},
    'Medium': {'Paw Print Fleece Blanket': 'M',
               'Quick-Dry Bath Robe':      'S',
               'Paw Washing Cup':          'M',
               'Cooling Comfort Pad':      'Large 28" x 22"'},
    'Large':  {'Paw Print Fleece Blanket': 'M',
               'Quick-Dry Bath Robe':      'M',
               'Paw Washing Cup':          'L',
               'Cooling Comfort Pad':      'X-Large 39" x 28"'},
}

# Per kit: the option that is NOT size, and what each of its values fixes.
# 'option' is the customer-facing option name. The Toy Kit's components vary by
# character rather than color, so its option is named accordingly.
KITS = {
    'New Puppy Kit': {
        'option': 'Colorway',
        'sizes': ['Small', 'Medium'],          # only the blanket varies by size
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

    'Toy Kit': {
        'option': 'Character set',
        'sizes': None,                          # nothing in this kit has a size
        'values': {
            'Farmyard': {
                'Barnyard Squeaker':   'Green Dog',
                'Sneaker Chew Buddy':  'Blue',
                'Jingle Plush Ball':   'Monkey',
                'Corduroy Squeak Pals': 'Fawn',
            },
            'Safari': {
                'Barnyard Squeaker':   'Giraffe',
                'Sneaker Chew Buddy':  'Black',
                'Jingle Plush Ball':   'Frog',
                'Corduroy Squeak Pals': 'Frog',
            },
            'Puppy Pack': {
                'Barnyard Squeaker':   'Puppy',
                'Sneaker Chew Buddy':  'Sea Fog Blue',
                'Jingle Plush Ball':   'Dog',
                'Corduroy Squeak Pals': 'Crooked Neck',
            },
        },
    },

    'Grooming Essentials Kit': {
        'option': 'Colorway',
        'sizes': ['Small', 'Medium', 'Large'],
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

    'Dog Enrichment Kit': {
        'option': 'Colorway',
        'sizes': None,
        'values': {
            'Green': {
                'Slow Feeder Bowl':   'Green',
                'Lick Bowl with Ball': 'Grey',
                'Talk Button':        'Green',
                'Bouncy Egg Squeaker': 'Green',
            },
            'Pink': {
                'Slow Feeder Bowl':   'Pink',
                'Lick Bowl with Ball': 'Black',
                'Talk Button':        'Pink',
                'Bouncy Egg Squeaker': 'Purple',
            },
            'Sunshine': {
                'Slow Feeder Bowl':   'Orange',
                'Lick Bowl with Ball': 'Yellow',
                'Talk Button':        'Yellow',
                'Bouncy Egg Squeaker': 'Orange',
            },
        },
    },

    'Travel Kit': {
        'option': 'Colorway',
        'sizes': ['Small', 'Medium', 'Large'],
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
        'sizes': ['Small', 'Medium', 'Large'],
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
