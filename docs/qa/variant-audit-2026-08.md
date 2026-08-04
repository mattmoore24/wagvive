# Variant and sizing audit, 2026-08-04

Every store variant compared against CJ's full variant list for all 36 source
products. Data: `docs/qa/cj-variants.json` (regenerate by editing
`config/audit_spus.json` and letting the `cj-variant-audit` workflow run).

## Summary

Most of what the store "does not carry" is multipacks, bundles, unboxed
versions and extra colourways. Those are deliberate merchandising choices and
need no action. Four products have genuine missing SIZES, and one has a
misleading size naming scheme.

## Real size gaps

Adding any of these needs **CJ pairing in the browser** (owner action, no API)
and each new size must clear the 50% margin floor at its own cost and freight.
Nothing here has been added to the store.

### 1. Waterproof Sofa & Furniture Cover, and its size labels

The most significant finding. CJ sells seven sizes. The store sells the three
smallest and relabels them:

| Store label | CJ label | Size |
|---|---|---|
| Small | XS | 50 x 70 cm |
| Medium | S | 71 x 100 cm |
| Large | M | 100 x 145 cm |
| not stocked | L | 145 x 165 cm |
| not stocked | XL | 145 x 216 cm |
| not stocked | 2XL | 200 x 200 cm |
| not stocked | 3XL | 216 x 216 cm |

A customer buying "Large" gets the middle size of seven, at 39 x 57 inches.
That is a two-seat sofa's seat area, not a sofa cover in the way the title
suggests. The description previously claimed the range reached "a full
three-seater", which was untrue; that copy has been corrected. Stocking L and
XL would make the product honestly match its own name.

### 2. Waterproof Snuggle Blanket

Store has XS and S. CJ also makes M, L and XL in all three stocked colours.

| Size | Dimensions | In store |
|---|---|---|
| XS | 50 x 70 cm | yes |
| S | 71 x 100 cm | yes |
| M | 100 x 145 cm | no |
| L | 145 x 165 cm | no |
| XL | 145 x 216 cm | no |

Nine variants missing. The store currently tops out at a blanket that covers
one sofa cushion, so large-dog owners have nothing to buy.

### 3. Paw Print Fleece Blanket

Store has S and M. CJ makes seven sizes.

| Size | Dimensions | In store |
|---|---|---|
| XXS | 20 x 20 cm | no (likely too small to sell) |
| XS | 40 x 60 cm | no |
| S | 52 x 76 cm | yes |
| M | 76 x 104 cm | yes |
| L | 100 x 120 cm | no |
| XL | 100 x 160 cm | no |
| XXL | 160 x 200 cm | no |

Also note the store's M dimension was previously listed as 100 x 75 cm, which
was wrong in both numbers and order. Corrected to 76 x 104 cm.

### 4. Cooling Comfort Pad

Store has Medium through XX-Large. CJ also makes XS 40 x 30 cm and S 50 x 40 cm
in all four colours, eight variants. These would serve small breeds and
puppies, and the current copy already says the smallest option "fits a spaniel
comfortably", so the gap is at the bottom of the range.

## Confirmed complete, no action needed

- **Quick-Dry Bath Robe.** XS, S, M is CJ's entire range. The only CJ variant
  not stocked is a bundle. The XS to M range looked odd but is correct.
- **Paw Washing Cup.** S, M, L complete. The unstocked variants are a
  "Cartoon" printed version, a decorative choice.
- **Anti-Spill Floating Water Bowl.** 1.5L and 2L complete. The unstocked
  variants are multipacks and mixed-colour bundles.
- **Calming Thunder Wrap.** CJ makes one size only, 81.3 x 61 cm, confirmed
  against the store copy.

## Not gaps

These products show large numbers of "missing" CJ variants that are all
multipacks, sets, accessories, unboxed versions or colourways the store chose
not to carry: Pet Hair Remover Mitt, Dental & Ear Wipes (larger counts exist,
see below), Quiet Electric Nail Grinder, Slow Feeder Bowl, Finger Toothbrush,
LED Waste Bag Dispenser, Travel Water Bottle, Talk Button, Bouncy Egg
Squeaker, Screaming Chicken, LED Nail Clippers.

One worth a decision rather than dismissal: **Dental & Ear Wipes** currently
sells 50-count tubs. CJ also offers 100, 150 and 200 count tooth wipes. That is
a merchandising opportunity rather than a correctness problem.
