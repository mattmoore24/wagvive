# Shipping, kits and sourcing: what CJ actually charges, and what to do about it

2026-08-04. Companion to `docs/pricing-study-2026-08.md`, which set prices
against the market. This one goes underneath that and asks where the cost comes
from. Nothing here has been applied to the store.

The pricing study left one question unanswered and flagged it as the biggest
open item in the business: **does CJ ship a multi-item order as one parcel, or
as several?** Kit margin was 51% if separate and 71% if combined, and no one had
ever measured it. That question is now settled, along with several others that
turned out to matter more than the price changes themselves.

Everything below is measured, not assumed. `config/research_freight.py` queried
CJ live across all 36 catalogue products, ran quantity ladders and multi-item
baskets, and scanned 16 pet categories for alternatives. Raw output is in
`docs/qa/freight-research.json`; kit numbers are in `docs/qa/kit-designs.json`.

---

## 1. The headline

**Freight is a parcel charge, not an item charge, and the parcel has a fixed
cost of about $4.43 before it carries a single gram.**

Across 33 products with credible quotes, cheapest-carrier freight fits

    freight = $4.43 + $11.90 per kg

with no residual over $1.56 anywhere from 30g to 1.8kg. Three consequences
follow, and they are the whole study:

1. **Adding one more 100g toy to an order the customer is already placing costs
   $1.19 in freight.** Shipping that same toy on its own costs $5.62. The
   difference, 4.7x, is larger than any price change available to us.
2. **The fixed cost sets a floor on delivered price of roughly $9 to $12 for a
   small item.** A product whose market delivered price sits below its own floor
   cannot be sold at any price, at CJ or anywhere else, because $4.43 of parcel
   overhead does not care who the supplier is. Six of our 36 products are in
   that position. See section 3.
3. **Kits are not a merchandising nicety. They are the mechanism by which this
   catalogue becomes profitable.** A four-item kit pays the $4.43 once instead
   of four times, which is $13.29 of pure saving before anything else happens.

And one finding that came out of doing the arithmetic properly rather than out of
CJ: **the pricing study understated the catalogue by comparing our item price
against delivered market prices.** Section 3 redoes that comparison like for
like. It moves the verdict from nine unsellable products to six, and it changes
which six.

---

## 2. How CJ charges freight, precisely

### 2.1 It is weight, and only weight

Product value has no effect on the quote. Pairs of near-identical weight and
very different cost quote identically:

| Weight | Product | Cost | Freight |
|---|---|---|---|
| 100g | Barnyard Squeaker | $1.45 | $5.59 |
| 100g | Woodland Rope-Limb Plush | $3.45 | **$5.59** |
| 111g | Pet Hair Remover Mitt | $1.98 | $5.64 |
| 112g | Squirrel Squeaky Plush | $6.12 | **$5.65** |
| 220g | Corduroy Squeak Pals | $1.70 | $6.57 |
| 220g | Paw Print Fleece Blanket | $1.76 | **$6.57** |

A 4.2x difference in declared value moves the freight quote by one cent. That
matters for a reason beyond curiosity: **CJ's freight quote contains no
ad-valorem duty.** Reports that CJ has folded US tariffs into its shipping lines
would imply the quote rises with value. It does not. So either duty is billed
separately, or it is not being billed to us at all. This is still the open
question in task #64 and it is worth an actual ticket to CJ, because the answer
is worth 20% of product cost on every order.

### 2.2 The quantity ladder

Quoting the same item at rising quantity separates a per-item charge from a
per-parcel one. It is emphatically per parcel:

| Product | x1 | x2 | x3 | x5 | x10 |
|---|---|---|---|---|---|
| Bouncy Egg Squeaker, 50g | $4.75 | $5.59 | $6.18 | $6.96 | $10.22 |
| Travel Water Bottle, 165g | $6.39 | $8.01 | $10.15 | $13.51 | $24.21 |
| Anti-Spill Water Bowl, 1833g | $26.59 | $48.99 | $72.28 | $82.98 | $86.00 |

Ten of the 50g toy cost $10.22 to ship, against $47.50 as ten separate parcels.
That is a 78.5% saving. The saving shrinks as items get heavier, because the
weight component starts to dominate the fixed component, and it nearly vanishes
on the 1.8kg bowl until sea freight takes over at quantity five.

**The rule of thumb: consolidation saves $4.43 per item you avoid shipping
separately, and nothing more.** Light goods gain enormously, heavy goods barely
at all.

### 2.3 Consolidation is conditional on a shared carrier

CJ can only put two items in one parcel if at least one carrier will take both.
Where no carrier serves the whole basket, `/logistic/freightCalculate` returns
nothing for the combination and CJ ships separate parcels. This was already
suspected in `config/kit_margins.py`; it is now confirmed and quantified.

In practice the constraint is mild. Four carriers each serve 34 of our 36
products within the 12 business-day promise:

| Carrier | Products served, of 36 |
|---|---|
| CJPacket Fast Line | 34 |
| CJPacket Sensitive Pro+ | 34 |
| CJPacket Fast US | 34 |
| CJPacket Liquid US | 34 |
| CJPacket Postal, USPS, YunExpress Sensitive | 33 |

Only two products fall outside the widest carrier: the **Self-Cleaning Slicker
Brush** and the **Cordless Paw Trimmer**. Their problem turned out not to be
carriers at all, and section 7.1 is where that goes.

### 2.4 Combining can occasionally cost MORE

Two measured cases where a combined quote beat the sum of separate parcels by a
negative amount:

| Basket | Separate | Combined | Difference |
|---|---|---|---|
| Dental & Ear Wipes + Anti-Spill Bowl | $38.97 | $49.86 | **+$10.89 worse** |
| Nail Grinder + Anti-Spill Bowl | $34.38 | $36.74 | **+$2.36 worse** |

The mechanism: the wipes are a liquid and need a "Sensitive" or "Liquid"
carrier, of which only nine will take them; the bowl is 1.8kg. Forcing both into
one parcel forces the whole 2.2kg onto a restricted, expensive line. The cheap
line that would carry the bowl will not carry the wipes.

So "put everything in one box" is not the rule. **The rule is: consolidate light
items on an unrestricted carrier, and keep restricted items (liquids,
electronics) and heavy items out of baskets where they drag everything onto a
worse line.**

### 2.5 How far the formula can be trusted

The $4.43 + $11.90/kg line was fitted on single items. Checking it against
independently measured multi-item baskets and quantity ladders says where it
holds and where it does not:

| Basket, measured | Grams | Formula | Actual | Error |
|---|---|---|---|---|
| Bouncy Egg Squeaker x5 | 250 | $7.40 | $6.96 | -$0.44 |
| Travel Water Bottle x10 | 1,650 | $24.07 | $24.21 | +$0.14 |
| Four light plush toys | 531 | $10.75 | $10.62 | -$0.13 |
| Puppy plush + toothbrush + snuggle blanket | 1,423 | $21.36 | $21.27 | -$0.09 |
| Water bottle + bag dispenser + bath robe | 427 | $9.51 | $11.11 | +$1.60 |
| Lick bowl + slow feeder + talk button | 596 | $11.52 | $14.02 | +$2.50 |
| Wipes + Anti-Spill Bowl | 2,187 | $30.46 | $49.86 | **+$19.40** |
| Nail Grinder + Anti-Spill Bowl | 2,063 | $28.98 | $36.74 | **+$7.76** |

Within a few percent for ordinary goods, and badly optimistic the moment a
liquid or an electronic item shares the parcel. So the formula is a planning
tool for light unrestricted baskets and nothing more. **Every kit that actually
goes live must be priced off a real quote for its exact composition**, which is
what `config/research_kits.py` does before recommending anything.

---

## 3. Delivered price: the comparison the pricing study did not make

The pricing study compared our item price against market prices. Amazon and
Chewy prices are **delivered** prices, and on any order under $60 our customer
also pays $5.95 for shipping. So the comparison was item-against-delivered, and
it was unfair to us in one direction and to the customer in the other.

`config/delivered_price.py` redoes it like for like. Delivered price is item plus
whatever shipping the customer pays; the floor is the delivered price at which a
product clears a given margin after real freight, duty, returns and card fees.

**30 of 36 products clear 15% at the market delivered price, and 25 clear 25%.**
The pricing study's count of nine unsellable products was too harsh, and it named
the wrong nine.

### The six that genuinely cannot work

| Product | Cost | Freight | Floor at 15% | Market delivered | Margin at market |
|---|---|---|---|---|---|
| Crinkle Plush Buddy | $3.48 | $5.35 | $12.35 | $8.00 | **-29.5%** |
| Waterproof Snuggle Blanket, 1,220g | $10.71 | $18.63 | $39.96 | $29.95 | **-12.4%** |
| Dental & Ear Wipes | $1.62 | $12.38 | $18.38 | $13.99 | **-10.7%** |
| Anti-Spill Floating Water Bowl, 1,833g | $11.69 | $26.59 | $51.45 | $40.00 | **-8.4%** |
| Waterproof Sofa & Furniture Cover, 1,340g | $11.28 | $20.19 | $42.78 | $39.99 | +9.3% |
| Squirrel Squeaky Plush | $6.12 | $5.65 | $16.71 | $16.23 | +12.6% |

Four of the six are heavy or restricted, which is the same finding as section 2
seen from the demand side. The **Dental & Ear Wipes** is the one to look at
first: it is live at $22.00 today, it was healthy in the July economics, and it
broke purely because CJ's liquid-carrier freight went from $7.88 to $12.38 in a
month. It is the only product in the catalogue currently listed above a price it
cannot sustain.

### The ones the pricing study wrote off that are actually fine

| Product | Verdict then | Margin at market delivered, now |
|---|---|---|
| Self-Cleaning Slicker Brush | Re-source or drop | **43.4%** |
| Lick Bowl with Ball | Bundle only | 19.6% |
| Dental Duck Chew Toy | Bundle only | 18.2% |
| Woodland Rope-Limb Plush | Bundle only | 17.5% |
| Rope-Limb Puppy Plush | Bundle only | 15.7% |
| Screaming Chicken | Bundle only | 15.5% |

The slicker brush turnaround is not the delivered-price change, it is section
7.1: it was being costed against a freight quote that does not exist. On real
freight it is a 43% product and needs no re-sourcing at all. The other five clear
15% but only just, so they are fair game for the kits rather than the shop front.

### The number that should drive merchandising

The last column of `docs/qa/delivered-price.json` is what each product costs to
**add to a parcel that is already going out**: goods, duty, returns and the
weight-share of freight, with no fixed parcel cost at all.

| Product | Alone | Added to an existing parcel | Sells for |
|---|---|---|---|
| Finger Toothbrush | $6.88 floor | **$0.81** | $13.99 |
| LED Waste Bag Dispenser | $8.02 | **$1.82** | $11.99 |
| Watermelon Rope Frisbee | $8.65 | **$2.31** | $14.99 |
| Sneaker Chew Buddy | $9.39 | **$2.94** | $16.99 |
| Barnyard Squeaker | $9.59 | **$3.02** | $15.99 |
| Talk Button | $9.79 | **$3.19** | $22.00 |

A $2.31 frisbee attached to an order already in the box, sold at $14.99, is a
better piece of business than almost anything else available to this store. That
is the case for kits, for cross-sell, and for a free-shipping progress bar, all
in one line.

---

## 4. The five kits as they stand today

**The open question is settled: CJ ships all five kits as ONE parcel.** Every
one returned a combined quote. `config/research_kits.py` quoted each live kit's
exact composition against CJ; these are real quotes, not the fitted formula.

| Kit | Price | Goods | Weight | Separate parcels | **One parcel** | Saving | Margin |
|---|---|---|---|---|---|---|---|
| New Puppy Kit | $79.00 | $6.68 | 352g | $17.28 | **$9.85** | $7.43 | **73.2%** |
| Toy Kit | $65.00 | $8.27 | 368g | $21.83 | **$8.50** | $13.33 | **67.2%** |
| Travel Kit | $77.00 | $12.23 | 525g | $23.80 | **$12.83** | $10.97 | **59.7%** |
| Grooming Essentials Kit | $85.00 | $16.90 | 451g | $23.55 | **$11.00** | $12.55 | **58.6%** |
| Dog Enrichment Kit | $98.00 | $19.59 | 2,429g | $48.13 | **$45.42** | $2.71 | **24.1%** |

Four of the five are in good health and need no change at all. The kits are
already doing the job the study says they should: consolidation is worth $46.99
across the five, and the Toy Kit alone saves $13.33 of freight on a $65 order.

**The Dog Enrichment Kit is broken.** At $98 it returns 24.1%, and it would need
**$137.38** to clear 45%. The cause is one component: the Anti-Spill Floating
Water Bowl is 1,833g of the kit's 2,429g and drags the whole parcel onto a
freight bill of $45.42. Consolidation saves only $2.71 here, because at that
weight there is barely any fixed cost left to share. This is the same product
that fails as a single at -8.4%, and it fails in both places for the same reason.

One caveat on the Grooming kit's $11.00 quote: it came back on "Yunexpress CN to
US", the same line that produced the $3.00 placeholders in section 7.1. At 451g
the fitted line says $9.78, so $11.00 is plausible and it passes the credibility
test. It is still the one number here I would want confirmed by a real order.

---

## 5. Kit redesigns

Every on-theme combination of three and four products was scored against the
fitted freight model, and the leaders in each theme were then **quoted live at
CJ**. What follows is the quoted number, not the predicted one. Kit prices are
20% off the sum of the components' own recommended single prices, which is the
middle of what the pricing study found shoppers expect from a set.

**That last sentence is a sequencing constraint, not a footnote.** The kit prices
below are 20% off the *recommended* singles, which are not live yet. Against
today's prices the rebuilt Enrichment kit at $52.99 reads as 43.6% off, which is
too deep: it would cannibalise the singles rather than lift the order. So the
repricing pass has to land first, or the kit prices have to be recomputed against
whatever the singles actually are. Every kit here holds at 20% off; none of them
holds at 44%.

### Dog Enrichment Kit: rebuild, this is the urgent one

Drop the Anti-Spill Floating Water Bowl. Best on-theme replacement, quoted:

| Composition | Price | Freight | Margin | Contribution |
|---|---|---|---|---|
| Slow Feeder Bowl + Lick Bowl with Ball + Talk Button + Sneaker Chew Buddy | **$52.99** | $14.47 | **47.0%** | $24.91 |
| Slow Feeder Bowl + Lick Bowl + Bouncy Egg Squeaker + Sneaker Chew Buddy | $49.99 | $12.39 | 47.0% | $23.51 |
| Slow Feeder Bowl + Talk Button + Bouncy Egg Squeaker + Sneaker Chew Buddy | $45.99 | $14.52 | 47.0% | $21.63 |

The first is the pick: it keeps the two feeders and the talk button, which is
what "enrichment" means, and swaps the water bowl for a chew toy. Margin goes
from 24.1% to 47.0%. The price falls from $98 to $52.99, which is a large drop,
but $98 was never a price this kit could hold and $52.99 sits inside the $55 to
$110 pet AOV band while still qualifying for free shipping at $60 if a single
item is added.

### New Puppy Kit: keep the economics, fix the theme

At 73.2% the current kit is the healthiest thing in the catalogue, so there is
no financial case for changing it. There is an editorial one: a **Cooling
Comfort Pad** is not a new-puppy product, and the kit has only three items
against four in the others. The best on-theme four, quoted:

| Composition | Price | Freight | Margin |
|---|---|---|---|
| Finger Toothbrush + LED Waste Bag Dispenser + Heartbeat Soothing Sloth + Jingle Plush Ball | **$67.99** | $15.07 | **53.7%** |

A heartbeat plush is exactly the right object for a puppy's first nights, and it
is one of the highest-contribution products we sell. The trade is 73.2% on three
items against 53.7% on four that actually tell the story. Contribution per kit
is $36.54 against the current kit's $57.82, so **on pure economics, keep what is
there**. Change it only if the puppy kit is meant to be a story rather than a
margin engine.

### Toy Kit and Travel Kit: keep, with an optional swap

Both are healthy. If you want more contribution per order without touching
anything else:

| Kit | Alternative composition | Price | Margin | Contribution |
|---|---|---|---|---|
| Toy | Big Squeak Plush + Jingle Plush Ball + Sneaker Chew Buddy + Corduroy Squeak Pals | $64.99 | 59.6% | $38.74 |
| Travel | Watermelon Rope Frisbee + Quick-Dry Bath Robe + Paw Washing Cup + Cooling Comfort Pad | $65.99 | **62.9%** | **$41.54** |

The Travel alternative is the strongest kit in the whole study on contribution,
and it drops the Travel Water Bottle, which is our third most expensive product
at $6.92. Whether a travel kit can credibly omit the water bottle is a
merchandising call, not a numbers one.

### Grooming Essentials Kit: keep, or trade $85 for $70.99

The live kit is fine at 58.6%. The best alternative is $70.99 at 55.9% with
$39.68 of contribution against the current kit's $49.80, so the current kit
wins on money. Keep it.

### Calm & Comfort Kit: the one worth adding

The Heartbeat Soothing Sloth, the Calming Thunder Wrap and the two blankets are
four of the highest-contribution products in the catalogue and **none of them is
in any kit**. Quoted:

| Composition | Price | Weight | Freight | Margin | Contribution |
|---|---|---|---|---|---|
| Heartbeat Sloth + Thunder Wrap + Paw Print Fleece Blanket + Cooling Comfort Pad | **$100.99** | 1,340g | $20.19 | **53.0%** | **$53.52** |
| Heartbeat Sloth + Thunder Wrap + Cooling Comfort Pad | $85.99 | 1,120g | $17.34 | 51.3% | $44.10 |
| Thunder Wrap + Paw Print Fleece Blanket + Cooling Comfort Pad | $67.99 | 850g | $13.83 | 55.4% | $37.68 |

$53.52 of contribution is more than any existing kit. The four-item version at
$100.99 is above the $55 to $110 pet AOV band's midpoint, so the $85.99 three-item
version is the safer opening move.

Do **not** add the Waterproof Snuggle Blanket to it. Quoted with it in, the kit
goes to 2,340g and $32.15 of freight, and margin falls to 33.6%.

### Two composition rules the quotes established

1. **Never put the Anti-Spill Floating Water Bowl in a kit.** At 1,833g it
   consumes the entire consolidation saving and then some.
2. **Never pair the Slow Feeder Bowl with a bulky plush.** Four New Puppy
   candidates containing both quoted **$42.28 to $48.91** of freight at only 840
   to 908g, because the combined dimensions force a "CJPacket Ordinary Over
   Length" line. That is five times what the weight alone predicts, and it is the
   clearest evidence in the study that **dimensional weight, not just mass, sets
   the carrier**. The same bowl sits happily in the Enrichment kit at $14.47
   alongside flat items.

---

## 6. Replacements for the products that cannot work

Scored at the owner's new floor: 15% target, 10% hard minimum, real freight, and
the product's own market delivered ceiling. Candidates are ranked by margin at
that ceiling. Every one still needs the images eyeballed against the CJ
reference before it goes anywhere near the store, and a duplicate-SPU check
against `sku[:11]` across the catalogue.

### Squirrel Squeaky Plush, ceiling $16.23, currently 12.6%

| Candidate | CJ SPU | Cost | Freight | Margin at ceiling |
|---|---|---|---|---|
| Squeaky Dog Toys For Aggressive Chewers, Durable Stuffed, 70g | CJPT2915091 | $3.04 | $5.09 | **39.6%** |
| Squeaky Stuffed Dog Toy Small, No-Stuffing Crinkle Paper, 68g | CJPT2913504 | $3.37 | $5.05 | 37.3% |

Both are half the weight of the incumbent's 112g at a similar cost, and both
turn a 12.6% product into a high-thirties one. Straight swap.

### Lick Bowl with Ball, ceiling $19.00, currently 19.6%

| Candidate | CJ SPU | Cost | Freight | Margin at ceiling |
|---|---|---|---|---|
| Portable Household Silicone Pet Feeding Mat, 172g | CJYD2951433 | $0.86 | $6.48 | **54.6%** |
| Multifunctional Solid-Color Silicone Pet Feeding Bowl, 230g | CJYD2985999 | $1.88 | $6.71 | 46.7% |

The incumbent is $5.00 of goods at 328g. A silicone lick mat does the same job
for $0.86 at 172g and nearly triples the margin. Worth doing even though the
incumbent technically clears 15%.

### Anti-Spill Floating Water Bowl, ceiling $18.00, currently -8.4%

| Candidate | CJ SPU | Cost | Freight | Margin at ceiling |
|---|---|---|---|---|
| Slow-feeding Anti-choking And Non-slip Pet Bowl, 335g | CJYD2888211 | $1.74 | $8.07 | **37.1%** |
| Slow-feeding Bowl Silicone, 304g | CJYD2931138 | $2.99 | $7.66 | 30.9% |

Be clear about what this is: **there is no viable anti-spill floating water bowl
at CJ under an $18 ceiling.** Everything in that shape is 800g and up, and at
those weights the freight is fatal. The candidates above are lighter silicone
bowls, which is a different product serving a different need. So this is a
replacement of the *slot*, not of the *product*, and it overlaps what the Slow
Feeder Bowl already does. The honest recommendation is to **drop the category**
rather than replace it.

### Self-Cleaning Slicker Brush, ceiling $29.99

**No replacement needed.** On corrected freight it returns 43.4% at market. The
pricing study's "re-source or drop" verdict was an artifact of the $3.00
placeholder quote. Cheaper candidates exist at 74% to 80% if you ever want them,
but there is no problem to solve here.

### Crinkle Plush Buddy, ceiling $8.00

**Nothing works, and nothing can.** The best candidate found was $2.08 of goods
at 130g, which needs $10.93 delivered against an $8.00 ceiling: -15.0%. The
cheapest thing in CJ's plush category still lands above what the market pays,
because a $4.43 parcel plus $1.55 of weight is already $6 before the toy. Drop
it. This is the one product where "no supplier can fix this" is literally true.

### The three still open

The scan did not produce a usable answer for these, and they need a targeted
follow-up rather than a guess:

- **Dental & Ear Wipes.** The problem is liquid-carrier freight at $12.38 on
  354g, not the product. Two things to try before dropping it: a smaller pack
  (the current one is 50 wipes per box and the weight scales with it) and a
  US-warehouse source, since section 8 shows US-stocked cleaning wipes exist at
  CJ. Note that CJ lists this product as disposable single-use wet wipes, so a
  30-count pack is a legitimate size rather than a downgrade.
- **Waterproof Snuggle Blanket**, 1,220g, and **Waterproof Sofa & Furniture
  Cover**, 1,340g. Both are heavy fabric goods where China air freight is
  structurally wrong. These are the two products in the catalogue where a US
  supplier or a US-warehouse CJ source would genuinely change the answer, and
  section 9 explains why that is the only place it does.

---

## 7. Three corrections to the money model

### 7.1 A placeholder freight quote was being taken as real

`CLAUDE.md` already records that a CJ quote of $0.00 means missing data, never
free carriage. The study found the same bug wearing different clothes.

The **Self-Cleaning Slicker Brush** (80g) and the **Cordless Paw Trimmer**
(160g) each returned exactly ONE carrier, "Yunexpress CN to US", at exactly
$3.00. Every other product in the catalogue was offered 19 to 27 carriers
starting at $4.28. The same $3.00 came back for a 1,913g two-item basket
containing the brush, which is not a price any carrier charges for two kilos.

Both products have been priced on freight that does not exist. `freight_floor.py`
now discards any quote under $4.00 before choosing, and substitutes the fitted
weight estimate instead of a flat constant. The corrected numbers are in
section 5 and section 6.

### 7.2 Freight has risen sharply since the last audit

Same product, same carrier, comparing the July economics against 2026-08-04:

| Product | Then | Now | Change |
|---|---|---|---|
| Dental & Ear Wipes (CJPacket Sensitive Pro) | $7.88 | $12.38 | +57% |
| Anti-Spill Water Bowl | $15.47 | $26.59 | +72% |
| Pet Hair Remover Mitt | $5.36 | $5.64 | +5% |

This is consistent with the wider market: air freight rates from China to the US
rose roughly 20% from late February 2026 on fuel and war-risk surcharges, and
heavier lanes moved most. It also means **a price set against a freight quote is
perishable**. The margin guard already re-checks on a schedule; it should be
treated as the thing that catches this, not as a formality.

---

## 8. Non-China options inside CJ

Yes, CJ has them, and the first pass missed them by looking for the wrong thing.

The catalogue scan inferred US stock from the `CJBQ` SKU prefix, the way
`config/scout.py` always has, and found **none of our 36 products** in a US
warehouse. That is correct as far as it goes. But `/product/list` accepts a
`countryCode` parameter, and it works: the plush toy category returns **350
products plain and 70 with `countryCode=US`**. One product in five is US-stocked
and the prefix test never sees them.

Quoting 30 US-stocked candidates from both warehouses shows where it matters:

| Product | Weight | US freight | China freight | Price advantage at 15% |
|---|---|---|---|---|
| Pet Water Dispenser | 1,500g | $17.08 | $27.43 | **$16.85** |
| Professional Low Noise Pet Hair Clipper | 534g | $10.09 | $12.98 | $5.74 |
| Traveling Out Portable Dog Water Dispenser | 484g | $9.74 | $10.01 | $1.99 |
| Waterproof Silicone Spot Pet Mat | 562g | $10.29 | $11.02 | $1.92 |
| Pet Water Cup Outdoor Portable Bottle | 220g | $6.76 | $6.57 | -$0.19 |

The advantage combines cheaper carriage with the 20% duty that a US-warehoused
item does not pay again. And it is **entirely a function of weight**. Above
about 500g the US warehouse is meaningfully cheaper; below 250g it is a wash or
slightly worse.

That maps exactly onto our problem list. The three heavy products the delivered
price analysis kills, the **snuggle blanket at 1,220g**, the **sofa cover at
1,340g** and the **anti-spill bowl at 1,833g**, are precisely the goods a US
warehouse fixes, and the toys it would not help at all.

Two cautions before treating this as solved:

1. The stock rows for many `countryCode=US` results still read `CN`, so the
   filter appears to mean "available to be stocked in the US" as much as
   "currently sitting in a US warehouse". A candidate has to be checked
   individually.
2. Several genuinely US-stocked items returned no usable US quote and fell back
   to the estimate, marked `us_estimated` in the data. Those numbers are
   planning figures, not prices.

**The follow-up worth running** is a `countryCode=US` scan restricted to
Blankets and quilts, Pet mats and Pet bowls, hunting a US-stocked equivalent of
the three heavy failures. That is a 15 minute job and it is the highest-value
sourcing question left open.

---

## 9. Should we leave CJ? An honest answer

Short version: **no, and the reasoning is not loyalty to CJ.** Every alternative
raises landed cost, and the one structural fix, buying inventory in bulk, is a
different business with a different cash requirement.

### 9.1 US dropship wholesalers make cheap goods worse, not better

The appeal is obvious: goods already in the US, no duty, 2 to 5 day delivery, no
customs risk. The arithmetic does not survive contact with a $12 dog toy.

| | CJ, China (measured) | US dropship wholesaler (derived) |
|---|---|---|
| Product cost, generic plush toy | $1.45 | $7.50 to $9.00 |
| Freight, single item | $5.59 | $5.50 to $8.74 |
| Duty | 20% modelled | none |
| Platform fee | none | $34.99 to $59.99/month |
| Landed, single | ~$7.90 | ~$13.00 to $17.70 |
| Market delivered price | $13.00 | $13.00 |

One caveat on that right-hand column before relying on it. **Neither of the two
zero-fee US suppliers will show prices without a registered wholesale account
and a tax ID**, which is yours to open, not mine. So the US figure is derived
from TopDawg's published "40% to 50% below MSRP", not observed. It should be
checked against a real logged-in price before any decision rests on it.

The wholesale price is the problem, and the derivation is not delicate. TopDawg
prices at 40% to 50% below MSRP, which sounds generous until you notice that
MSRP *is* the market price we are competing at. A 45% discount off a $15 toy is
$8.25, and $8.25 plus $6 of domestic ground shipping is already above what the
toy sells for. Independent reviews say the same thing from the other direction:
Spocket's US and EU suppliers deliver **30 to 40% margins against 45 to 55% on
Chinese sourcing**, and reviewers specifically flag low-ticket items as where
the model breaks.

Domestic shipping does not rescue it either. USPS Ground Advantage commercial is
about $5.50 to $8.74 for a 1lb parcel depending on zone. That is not meaningfully
cheaper than the $4.43 + $11.90/kg we already pay from China. **The fixed cost of
putting one small parcel in front of one customer is roughly $6 in any country.**

Concrete platform costs, for the record:

| Platform | Fixed cost | Notes |
|---|---|---|
| TopDawg | $0 browse only, $34.99/mo to sync or order, plus per-order processing | US warehouses, strong pet catalogue, reviewers flag thin low-ticket margins and non-refundable fees |
| Spocket | $39.99/mo for 25 products, realistically $59.99/mo | US/EU suppliers, 30 to 40% typical margin |
| Zendrop | $49/mo Pro for US products, $79/mo Plus | Higher base prices than CJ by most comparisons |
| Essential Pet Products | none | US warehouses, product and shipping only, requires a US or Canada business and a tax ID to see prices |
| Mirage Pet Products | none | No minimums, free shipping over $250. **Closing its US factory and moving operations to Portugal**, so treat as unstable |
| Shopify Collective | none beyond Shopify Payments fees | US/Canada, Shopify Payments required; sources disagree on whether a $50k trailing revenue test applies |

**Essential Pet Products** is the only one worth a look, and only for the heavy
and bulky items where China freight is punitive: beds, blankets, furniture
covers, ceramic bowls. On a $40 bulky item a US supplier's $8 ground shipping
beats our $20 to $26 air freight decisively. On a $12 toy it changes nothing.
Mirage would have been the other candidate, but it is mid-move to Portugal and
is not a foundation to build on right now.

Opening that account needs your store name and tax ID, so it is a five minute
job for you and one I cannot do. If you want the comparison made properly, that
registration is the blocking step.

**Shopify Collective** deserves a separate mention because it costs nothing and
plugs straight into the existing store. It is worth applying to on those grounds
alone. Treat it as a possible source for the bulky end of the range, not as a
replacement catalogue.

### 9.2 The structural fix is bulk, and it is a different business

The only way to actually kill the $4.43 fixed parcel cost is to stop shipping
parcels from China one at a time. Buy in bulk, land it in the US, ship domestic.

- Air freight DDP from China runs **$4 to $8 per kg**, duty and clearance
  included. A 300g item lands for **$1.20 to $2.40** against $8.00 of
  single-parcel air freight plus duty today.
- CJ will do this without a separate freight forwarder: it holds stock in its own
  US warehouses, with **90 days free storage**, then **$0.80 per cubic metre per
  day** after, rising to $1.50 at low turnover. MOQ to stock an overseas
  warehouse is **10 units per variant and 100 units total**.
- Outbound then becomes domestic: **$5.50 to $8.74** USPS Ground Advantage
  commercial, 2 to 5 days, and duty is already paid.

The catch is not the storage fee, which is trivial. It is that 100 units at, say,
$3 each is $300 of goods plus freight, per product, spent before a single sale,
and repeated for every SKU. Across even a third of the catalogue that is real
working capital tied up in inventory that may not sell. It also converts every
sourcing mistake from "unlist it" into "write it off".

A third-party 3PL is worse again for a store at this stage: pick and pack runs
**$2.75 first item and $0.50 per additional**, all-in **$10 to $14 per order
including ground carriage**, and monthly minimums now average **over $500**. That
is a fixed cost of $6,000 a year before the first order.

**Recommendation.** Stay on CJ dropship as the default. Revisit bulk-into-CJ's-US-warehouse
for a *single* product only, once one product is demonstrably selling
more than roughly 20 units a month, at which point the $300 to $500 committed is
a reasonable bet rather than a guess. Do not do it speculatively across the
catalogue, and do not sign a 3PL.

---

## 10. What to do, ranked

Nothing below has been applied. Ranked by money at stake, not by effort.

### Do first, because a live product is losing money

1. **Rebuild the Dog Enrichment Kit.** It is live at $98 returning 24.1%, and it
   needs $137.38 to clear 45%. Drop the Anti-Spill Floating Water Bowl, use Slow
   Feeder Bowl + Lick Bowl with Ball + Talk Button + Sneaker Chew Buddy, price
   **$52.99** for 47.0%. Biggest single correction in the study.
2. **Fix the Dental & Ear Wipes.** Live at $22.00 with a delivered floor of
   $18.38 against a $13.99 market. CJ's liquid freight went from $7.88 to $12.38
   in a month and took the product with it. Either source a smaller pack, find a
   US-warehouse equivalent, or withdraw it. Do not leave it at $22.00.
3. **Reprice the Self-Cleaning Slicker Brush and the Cordless Paw Trimmer on
   real freight.** Both were costed against a $3.00 placeholder. The brush is
   fine at 43.4%; the trimmer drops to 35.1%. Neither needs dropping, but the
   numbers in `docs/qa/pricing-recommendations.json` for these two are wrong and
   should be recomputed before the repricing pass (#74) runs.

### Do next, because they are pure upside

4. **Add a free-shipping progress bar.** With $4.43 of fixed parcel cost, every
   item a customer adds to reach $60 costs us $1 to $3 to ship and sells for $12
   to $22. Independent benchmarks put the progress bar at an 8 to 14% conversion
   lift on top of the free-shipping effect, and it is described as the single
   most reliable AOV lever in ecommerce. Nothing else in this study has that
   ratio of effort to return. Keep the threshold at $60: it sits inside the $55
   to $110 pet AOV band, above every single item, and below every kit.
5. **Launch the Calm & Comfort Kit** at $85.99 for three items, 51.3%, $44.10 of
   contribution. Four of our best products are currently in no kit at all.
6. **Swap in the two clear replacement wins**: the Squirrel Squeaky Plush for
   CJPT2915091 (12.6% to 39.6%) and the Lick Bowl with Ball for the silicone
   feeding mat CJYD2951433 (19.6% to 54.6%).

### Do when convenient

7. **Drop the Crinkle Plush Buddy and the Anti-Spill Floating Water Bowl.**
   Neither can be fixed by price or by re-sourcing, and the bowl now fails in the
   kit as well as on its own.
8. **Run the US-warehouse scan on the heavy categories** (section 8) to hunt
   sources for the snuggle blanket and the sofa cover. Fifteen minutes of API
   time, and it is the only route that changes the answer for those two.
9. **Open the CJ ticket on duty** (task #64). CJ's freight quote is provably
   value-independent, so it contains no ad-valorem tariff. Whether the 20% in
   `pricing.py` is being billed elsewhere or is pure conservatism is worth 20% of
   product cost on every order, and it is one support message.
10. **Treat the margin guard as the thing that catches freight drift.** Two
    products moved 57% and 72% in a month. Prices set against a freight quote
    have a shelf life.

### Do not do

11. **Do not switch suppliers.** US dropship wholesalers raise landed cost on
    everything except heavy goods, and charge $35 to $60 a month for the
    privilege. The one exception worth a look is a zero-fee US supplier for the
    heavy fabric items, and opening that account needs your tax ID.
12. **Do not sign a 3PL.** $10 to $14 per order all-in plus a $500-plus monthly
    minimum, against a store with no order volume to spread it over.
13. **Do not buy bulk inventory speculatively.** Revisit it for one product
    only, once that product is selling more than about 20 units a month.
