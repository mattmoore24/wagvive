# Fall / Halloween lineup + viral devices, sourcing research
2026-08-18. Scan of **5,535 unique CJ products** across 27 pet categories
(`config/scout_fall.py`), costed on live freight through
`freight_floor.resolve()` at the 50% floor for new products.

## Timing, which decides everything

Halloween is **31 October**. The site promises 5 to 12 business days, so a
customer ordering later than about **10 October** does not get it in time.
Working back through listing, art, pairing and ads, anything not live by
**mid September** is decoration rather than revenue. That makes this a
three-week window, and it is the main argument for shipping a small lineup
now rather than a perfect one later.

## Recommended: 5 fall products

| # | Product | SPU | CJ cost | Weight | Freight | Floor price | Proposed | Listings | Stock |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Glow in the Dark Skeleton Jumpsuit** | CJGD2143164 | $4.24 | 60-86g | $4.92 | $24 | **$24.99** | 203 | 11,275 |
| 2 | **Halloween Snuffle Mat** (hides treats) | CJYD2183039 | $5.47 | 270g | $7.23 | $32 | **$32.99** | 6 | 14,912 |
| 3 | **Jack-o-Lantern Knit Sweater** | CJGD1809813 | $1.80-2.37 | 85-125g | $5.34 | $17 | **$17.99** | 1,653 | 12,178 |
| 4 | **Halloween Squeaky Bone** | CJYD2146653 | $1.22 | 56g | $4.85 | $15 | **$15.99** | 40 | 10,101 |
| 5 | **Thanksgiving Plaid Lapel Coat** | CJGD1841040 | $3.16 | 75g | $5.17 | $20 | **$19.99** | 194 | 14,805 |

1 is the hero and matches the brief exactly: four-leg black jumpsuit, glow in
the dark bone print, 4 sizes. Reference photo is clean, dog-only, no supplier
branding and no label text.

2 is the enrichment ask: fleece mat with ghosts, bats, pumpkins and a haunted
house, plus a drawstring pumpkin pouch, treats hidden in the folds. Only 6
other sellers list it, so it is unproven, but it is genuinely on brief and
seasonal scarcity is the point.

3 is the safest volume bet in the whole sweep at 1,653 listings, 20 variants.

## Recommended: 1 viral device

| Product | SPU | CJ cost | Weight | Freight | Floor price | Proposed | Listings | Stock |
|---|---|---|---|---|---|---|---|---|
| **3-in-1 Steam Grooming Brush** | CJYD2256797 | $3.51 | 200g | $6.87 | $26 | **$26.99** | 356 | 9,196 |

Water tank, mist button, silicone bristles. Demos in five seconds, which is the
whole point. NOTE its CJ reference images carry burnt-in English marketing text
("Daily cleaning kit"), so art must be shot with `nano-banana-pro` and the text
banned explicitly, or a different reference used.

## Rejected, and why. Weight is what kills the viral devices.

| Product | SPU | Why rejected |
|---|---|---|
| 7-in-1 grooming vacuum | CJGY2140137 | Real device is **3,550g** at $44.44. The $1.04/170g variant is an ACCESSORY, the classic multipack trap |
| Portable grooming vacuum | CJYD2763967 | **1,020g**, over the 1kg rule; needs $122 against a $60-90 market |
| Automatic ball launcher | CJCT2567740 | **1,800g**, needs $164 |
| Steam brush (large) | CJHR2364997 | **822g**, freight $23.64, needs $72 against a ~$30 market |
| Self-cleaning brush | CJHR2543290 | 582g, needs $48; we already sell a slicker brush |
| 7pc grooming kit | CJHR2665670 | **No freight quote at all**, and stock 30 |
| Automatic massager | - | **Does not exist on CJ as a device.** Only massage/bath BRUSHES. The viral units are other suppliers |
| Pumpkin spice spray | - | **Does not exist.** Nearest is a generic deodorising spray, 5 listings, needs ~$45 |
| Turkey costume | CJGD1379862 | 41 listings, needs $46 |
| Fall bandana | CJGD2143477 | Needs $18.87 against a ~$10 market |
| "Pumpkin vest" | CJYD1861730 | **It is a CAT head hood**, not a dog vest. Caught by the image gate, not the title |

**The pattern worth keeping:** every viral grooming device failed on the same
thing, freight weight. Anything with a motor and a dust cup lands between 800g
and 3.5kg, and at those weights CJ freight alone is $17 to $53. To sell that
category we need a US-warehouse SKU (`CJBQ` prefix, no duty, domestic freight)
rather than a China-shipped one.

## Verification applied to every survivor
Duplicate SPU check against all 38 catalogue SPUs (all new), live freight inside
the 12 day promise, stock depth, and every reference image opened at full size.
