#!/usr/bin/env python3
"""ONE size scale for the whole store. Source of truth for every sized product.

THE PROBLEM THIS FIXES. Sizing was inherited from whatever each CJ supplier
happened to print, so the same letter meant wildly different dogs:

  Pumpkin Hoodie   "XS" = a 1.3 lb dog        (chest 27 cm)
  Jack-o-Lantern   "XS" = a chest of 30 cm
  Skeleton Suit    "S"  = a chest of 34 cm
  Quick-Dry Robe   "XS" = an 18 to 33 lb dog  (chest 45 to 55 cm!)
  Big Dog Costume  "3XL"= a chest of 68 cm

So a beagle owner needed the robe in XS, the hoodie in 4XL and the costume in
3XL. Nobody can be expected to work that out, and the Big Dog Costume starting
at "3XL" made the store look like it only sold to giant breeds.

THE RULE NOW: one scale, XS to XL, defined by the DOG, not by the garment. A
given dog picks the same letter on every product in the store, forever. A
product that physically cannot serve the whole range offers a SUBSET of the
scale (the Skeleton Suit is genuinely a small-dog suit, so it sells XS and S
and nothing else) - but the letters it does offer mean exactly what they mean
everywhere else.

WHY CHEST GIRTH IS THE MATCHER. Weight is what customers KNOW, girth is what
actually decides whether a garment does up. So the mapping below is computed on
girth, and weight plus breed are what we SHOW. Every supplier chart gives girth;
only some give weight, and where both exist they agree with these bands.

WHAT WE SHOW THE CUSTOMER, in this order, because it is the order they can
actually answer: weight -> breed examples -> measurements. Nobody knows their
dog's chest girth. Everybody knows roughly what it weighs and what breed it is.
"""

# --- the scale -------------------------------------------------------------
# chest_cm is the fitting band. weight_lb and breeds are the customer-facing
# anchors. Bands are contiguous so no dog falls between two sizes.
SCALE = [
    dict(size='XS', chest_cm=(28, 40), weight_lb=(0, 10),
         breeds='Chihuahua, Yorkshire Terrier, Pomeranian, Maltese',
         short='toy breeds'),
    dict(size='S', chest_cm=(40, 55), weight_lb=(10, 25),
         breeds='Shih Tzu, Miniature Schnauzer, Pug, Boston Terrier, '
                'West Highland Terrier',
         short='small breeds'),
    dict(size='M', chest_cm=(55, 70), weight_lb=(25, 50),
         breeds='Beagle, Cocker Spaniel, Border Collie, French Bulldog, '
                'Staffordshire Bull Terrier',
         short='medium breeds'),
    dict(size='L', chest_cm=(70, 85), weight_lb=(50, 90),
         breeds='Labrador, Golden Retriever, German Shepherd, Boxer',
         short='large breeds'),
    dict(size='XL', chest_cm=(85, 100), weight_lb=(90, 200),
         breeds='Great Dane, Mastiff, Newfoundland, Saint Bernard',
         short='giant breeds'),
]
ORDER = [s['size'] for s in SCALE]
BY_SIZE = {s['size']: s for s in SCALE}


def band(size):
    return BY_SIZE[size]


def weight_text(size):
    lo, hi = band(size)['weight_lb']
    return f'up to {hi} lb' if lo == 0 else (f'{lo} lb and up' if hi >= 200
                                             else f'{lo} to {hi} lb')


# --- per-product mapping ----------------------------------------------------
# supplier_size -> our size. Derived by placing each supplier variant's CHEST
# GIRTH into the bands above. Where several supplier sizes land in one band we
# keep the one closest to the band's midpoint and RETIRE the rest: the whole
# point is that "S" is one obvious choice, not three near-identical ones.
#
# `basis` records the measurement each decision was made on, so a future
# session can re-derive rather than trust.

MAP = {
 # Pumpkin Hoodie: chest 27,32,37,42,47,52,59,64,69,74,79,83,87 cm.
 # The only product that spans the entire scale, so it anchors it.
 'wagvive-pumpkin-hoodie': dict(
     basis='chest girth cm from the maker chart',
     keep={'S': 'XS', 'XL': 'S', '4XL': 'M', '7XL': 'L', '9XL': 'XL'},
     retire=['XS', 'M', 'L', '2XL', '3XL', '5XL', '6XL', '8XL'],
     note='13 supplier sizes collapse to 5. Kept chest 32/47/64/79/87 cm, the '
          'closest to each band midpoint.'),

 # Big Dog Costume: bust 68,73,78,83,88,93 cm. Genuinely a big-dog product;
 # its "3XL" was never a 3XL dog, it was a medium one.
 'wagvive-big-dog-costume': dict(
     basis='costume bust cm from the maker chart',
     keep={'3XL': 'M', '5XL': 'L', '8XL': 'XL'},
     retire=['4XL', '6XL', '7XL'],
     note='Relabelling 3XL to M is the single biggest readability win in the '
          'catalogue.'),

 # Skeleton Suit: chest 34,38,42,46 cm. Maker states small dogs only.
 'wagvive-glow-skeleton-suit': dict(
     basis='chest girth cm from the maker chart',
     keep={'S': 'XS', 'L': 'S'},
     retire=['M', 'XL'],
     note='Small-dog suit. Offers XS and S only, which is honest rather than '
          'pretending it fits a labrador.'),

 # Jack-o-Lantern Sweater: bust 30,35,40,48,56 cm (by grade order).
 'wagvive-jack-o-lantern-sweater': dict(
     basis='bust cm from the maker chart, mapped by grade order',
     keep={'XS': 'XS', 'L': 'S', 'XL': 'M'},
     retire=['S', 'M'],
     note='Knit with give, so the bands tolerate the wider steps.'),

 # Thanksgiving Turkey Sweater: bust 36,38,44,46 cm.
 'wagvive-thanksgiving-turkey-coat': dict(
     basis='bust cm from the maker chart',
     keep={'S': 'XS', 'XL': 'S'},
     retire=['M', 'L'],
     note='Supplier steps are tiny (36/38 and 44/46), so two of the four were '
          'always redundant.'),

 # Quick-Dry Bath Robe: chest 45-55, 57-67, 70-80 cm. Maps one-to-one, and is
 # the clearest example of the old problem: its "XS" is a 33 lb dog.
 'wagvive-quick-dry-bath-robe': dict(
     basis='chest girth cm from the maker chart',
     keep={'XS': 'S', 'S': 'M', 'M': 'L'},
     retire=[],
     note='Pure relabel, no variants retired. Every size shifts up two letters.'),

 # Paw Washing Cup: all three share a 7 cm opening; only depth changes, which
 # tracks leg length, which tracks dog size.
 'wagvive-paw-washing-cup': dict(
     basis='cup depth 11/13.5/15 cm against leg length',
     keep={'S': 'S', 'M': 'M', 'L': 'L'},
     retire=[],
     note='Already aligned. Labels unchanged; the guide now states the shared '
          '2.8 in opening as the real constraint.'),

 # Bedding is matched on the dog it covers, not worn, so the band is applied to
 # back length rather than chest. Short edge for a blanket (a curled dog), long
 # edge for a pad (a stretched-out dog).
 'wagvive-paw-print-fleece-blanket': dict(
     basis='blanket short edge 52/76 cm against curled back length',
     keep={'S': 'S', 'M': 'L'},
     retire=[],
     note='Only two sizes exist, and they genuinely serve small and large. No '
          'M offered rather than inventing one.'),

 'wagvive-waterproof-snuggle-blanket': dict(
     basis='blanket short edge 50/71 cm against curled back length',
     keep={'XS': 'S', 'S': 'L'},
     retire=[],
     note='Same two-point spread as the fleece blanket, so same treatment.'),

 'wagvive-cooling-comfort-pad': dict(
     basis='pad long edge 60/70/100/150 cm against stretched back length',
     keep={'Medium 24" x 20"': 'M', 'Large 28" x 22"': 'L',
           'X-Large 39" x 28"': 'XL'},
     retire=['XX-Large 59" x 39"'],
     note='The 150 cm pad is furniture-scale, not dog-scale, and duplicated XL.'),
}

# The Sofa & Furniture Cover is deliberately NOT on this scale. It is sized to
# the FURNITURE, and putting dog letters on it is exactly the confusion this
# file exists to remove. It gets plain furniture names instead.
FURNITURE = {
 'wagvive-waterproof-sofa-furniture-cover': {
     'Small 20" x 28"': 'Armchair or car seat',
     'Medium 28" x 39"': 'Two seat sofa',
     'Large 39" x 57"': 'Three seat sofa'},
}

# Kits drive several components from one pick, so their size IS a dog size and
# uses the scale. The binding component is the robe (the only worn item), which
# after remapping offers S, M, L - so the kits offer S, M, L.
KIT_SIZES = ['S', 'M', 'L']
KIT_RENAME = {'Small': 'S', 'Medium': 'M', 'Large': 'L'}


def summary():
    rows = []
    for handle, m in MAP.items():
        rows.append((handle, len(m['keep']), len(m['retire']),
                     ' '.join(f'{k}->{v}' for k, v in m['keep'].items())))
    return rows


if __name__ == '__main__':
    print('CANONICAL SCALE')
    for s in SCALE:
        print(f"  {s['size']:3} {weight_text(s['size']):16} "
              f"chest {s['chest_cm'][0]}-{s['chest_cm'][1]}cm   {s['breeds']}")
    print('\nPER PRODUCT')
    tot_keep = tot_ret = 0
    for h, keep, ret, mapping in summary():
        tot_keep += keep
        tot_ret += ret
        print(f'  {h[:42]:44} keeps {keep}  retires {ret}')
        print(f'  {"":44} {mapping}')
    print(f'\n{tot_keep} size options kept, {tot_ret} supplier sizes retired')
