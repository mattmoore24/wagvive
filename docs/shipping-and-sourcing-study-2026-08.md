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
2. **Every cheap single item is a losing proposition and always will be**, at
   any supplier, because $4.43 of fixed parcel cost cannot be recovered from a
   $9 toy. This is not a CJ problem. It is arithmetic.
3. **Kits are not a merchandising nicety. They are the mechanism by which this
   catalogue becomes profitable.** A four-item kit pays the $4.43 once instead
   of four times, which is $13.29 of pure saving before anything else happens.

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
Brush** and the **Cordless Paw Trimmer**. Both are discussed in section 6,
because their problem turned out not to be carriers at all.

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
| Live Toy Kit, 4 items | 531 | $10.75 | $10.62 | -$0.13 |
| Live New Puppy Kit, 3 items | 1,423 | $21.36 | $21.27 | -$0.09 |
| Live Travel Kit, 3 items | 427 | $9.51 | $11.11 | +$1.60 |
| Live Enrichment Kit, 3 items | 596 | $11.52 | $14.02 | +$2.50 |
| Wipes + Anti-Spill Bowl | 2,187 | $30.46 | $49.86 | **+$19.40** |
| Nail Grinder + Anti-Spill Bowl | 2,063 | $28.98 | $36.74 | **+$7.76** |

Within a few percent for ordinary goods, and badly optimistic the moment a
liquid or an electronic item shares the parcel. So the formula is a planning
tool for light unrestricted baskets and nothing more. **Every kit that actually
goes live must be priced off a real quote for its exact composition**, which is
what `config/research_kits.py` does before recommending anything.

---

## 3. What this means for the five kits

See section 4 for the redesigns. The measured position today:

<!-- KIT_TABLE -->

---

## 4. Kit redesigns

<!-- KIT_DESIGNS -->

---

## 5. Replacements for the nine unsellable products

<!-- REPLACEMENTS -->

---

## 6. Two corrections to the money model

### 6.1 A placeholder freight quote was being taken as real

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
section 4 and section 5.

### 6.2 Freight has risen sharply since the last audit

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

## 7. Non-China options inside CJ

<!-- US_WAREHOUSE -->

---

## 8. Should we leave CJ? An honest answer

Short version: **no, and the reasoning is not loyalty to CJ.** Every alternative
raises landed cost, and the one structural fix, buying inventory in bulk, is a
different business with a different cash requirement.

### 8.1 US dropship wholesalers make cheap goods worse, not better

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

### 8.2 The structural fix is bulk, and it is a different business

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

## 9. What to do, ranked

<!-- ACTIONS -->
