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

---

# Appendix: exact SKUs to pair (PC work)

Pair each SKU at CJ, then Claude creates the Shopify variant at a price that
clears the 50% floor. Costs below are CJ's product cost only; freight is
resolved separately through `config/freight_floor.py` and is what usually
decides whether a size is viable.

### Waterproof Sofa & Furniture Cover (CJYD2251860) — 12 new variants

| CJ size | SKU to pair | CJ cost |
|---|---|---|
| Black-L 145cm*165cm | `CJYD225186004DW` | $11.28 |
| Black-XL 145cm*216cm | `CJYD225186005EV` | $14.26 |
| Black-2XL 200cm*200cm | `CJYD225186006FU` | $16.58 |
| Brown-L 145cm*165cm | `CJYD225186010JQ` | $11.28 |
| Brown-XL 145cm*216cm | `CJYD225186011KP` | $14.26 |
| Brown-2XL 200cm*200cm | `CJYD225186012LO` | $16.58 |
| Gray-L 145cm*165cm | `CJYD225186016PK` | $11.28 |
| Gray-XL 145cm*216cm | `CJYD225186017QJ` | $14.26 |
| Gray-2XL 200cm*200cm | `CJYD225186018RI` | $16.58 |
| Black-3XL 216x216cm | `CJYD225186019SH` | $17.91 |
| Brown-3XL 216x216cm | `CJYD225186020TG` | $17.91 |
| Gray-3XL 216x216cm | `CJYD225186021UF` | $17.91 |

### Waterproof Snuggle Blanket (CJGY1926497) — 9 new variants

| CJ size | SKU to pair | CJ cost |
|---|---|---|
| Black-M | `CJGY192649703CX` | $7.56 |
| Black-L | `CJGY192649704DW` | $10.71 |
| Black-XL | `CJGY192649705EV` | $13.86 |
| Gray-M | `CJGY192649708HS` | $7.56 |
| Gray-L | `CJGY192649709IR` | $10.71 |
| Gray-XL | `CJGY192649710JQ` | $13.86 |
| Coffee-M | `CJGY192649713MN` | $7.56 |
| Coffee-L | `CJGY192649714NM` | $10.71 |
| Coffee-XL | `CJGY192649715OL` | $13.86 |

### Paw Print Fleece Blanket (CJGY2117113) — 12 new variants

| CJ size | SKU to pair | CJ cost |
|---|---|---|
| Camel Dog's Paw-XS | `CJGY211711302BY` | $0.69 |
| Camel Dog's Paw-L | `CJGY211711305EV` | $3.02 |
| Camel Dog's Paw-XL | `CJGY211711306FU` | $4.70 |
| Camel Dog's Paw-XXL | `CJGY211711307GT` | $7.46 |
| Beige Dog's Paw-XS | `CJGY211711309IR` | $0.69 |
| Beige Dog's Paw-L | `CJGY211711312LO` | $3.02 |
| Beige Dog's Paw-XL | `CJGY211711313MN` | $4.70 |
| Beige Dog's Paw-XXL | `CJGY211711314NM` | $7.46 |
| Pink Dog's Paw-XS | `CJGY211711316PK` | $0.69 |
| Pink Dog's Paw-L | `CJGY211711319SH` | $3.02 |
| Pink Dog's Paw-XL | `CJGY211711320TG` | $4.70 |
| Pink Dog's Paw-XXL | `CJGY211711321UF` | $7.46 |

### Cooling Comfort Pad (CJPM2920000) — 8 new variants

| CJ size | SKU to pair | CJ cost |
|---|---|---|
| Coffee color-XS 40x30cm | `CJPM292000001AZ` | $2.27 |
| Coffee color-S 50x40cm | `CJPM292000002BY` | $2.69 |
| Pink-XS 40x30cm | `CJPM292000007GT` | $2.27 |
| Pink-S 50x40cm | `CJPM292000008HS` | $2.69 |
| Dark blue-XS 40x30cm | `CJPM292000013MN` | $2.27 |
| Dark blue-S 50x40cm | `CJPM292000014NM` | $2.69 |
| Light gray-XS 40x30cm | `CJPM292000019SH` | $2.27 |
| Light gray-S 50x40cm | `CJPM292000020TG` | $2.69 |

**Total: 41 new variants.**