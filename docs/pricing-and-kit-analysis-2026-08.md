# Pricing and kit analysis, 2026-08-04

The whole catalogue was repriced and all six kits were rebuilt on this date.
This document is the reference record: what was measured, what model was used,
what every product and kit ended up at, and which beliefs it overturned.

**Everything here is applied and verified live.** The machine-readable source of
truth is `config/price_book.json`; this file explains it.

---

## 1. Why the old prices were wrong

Prices had been set to clear a flat **50% gross margin floor**. That rule was
retired by the owner on 2026-08-04, and the repricing that followed found three
separate problems with what it had produced.

**A margin target is not a business objective.** 60% of nothing is nothing. A
floor set high enough to cover freight on the store's heaviest item forces every
light item to a price nobody pays. Under the old regime 33 of 36 products sat
above the top of their observed market range, several at two to three times the
volume price.

**Freight is a parcel charge, not a per-item cost.** Fitted across all 36
products from 30g to 1.8kg, CJ charges roughly **$4.40 fixed plus $12.11 per
kilo**, with no residual above $1.56 and no dependence on declared value at all:
two 100g items costing $1.45 and $3.45 both quote $5.59. This single fact
explains why a $1 toothbrush cannot be sold profitably on its own but is nearly
free money inside a kit, and it is the reason the kits were redesigned rather
than merely repriced.

**The earlier study measured the wrong products.** The 2026-08-04 iPad research
costed five of 36 products against **CJ multipack variants we do not sell** (the
water bowl was costed at 1833g / $11.69 for a "Grey 3pcs" listing when our
single is 620g / $4.13; also the wipes, sofa cover, snuggle blanket and hair
mitt). Healthy products looked like loss-makers: the Enrichment Kit was reported
at 24.1% when it was actually 57.5%, and the wipes at negative 10.7% when they
were positive 29.6%. Three steps of the resulting implementation plan were
voided. `config/validate_research.py` now flags any research row whose weight
exceeds the heaviest variant we stock by more than 25%, so this specific error
cannot recur silently.

---

## 2. Method

### 2.1 Costs: re-measured from the SKUs we actually sell

`config/reprice_catalogue.py` walks all 36 products, reads each one's live CJ
variants filtered to **our** SKUs, takes the dearest variant's goods cost and
the heaviest variant's weight (so no customer choice can lose money), and quotes
freight live through `config/freight_floor.py::resolve()`, which picks the
cheapest carrier whose upper transit bound still meets the published 5 to 12
business day promise and rejects placeholder quotes below 75% of the
weight-fitted estimate. Snapshot: `docs/qa/recost-2026-08-04.json`.

### 2.2 Market bands, not a single "market price"

`config/market_bands.py` carries three prices per product rather than one:

| | meaning |
|---|---|
| **low** | what the cheapest credible competitor charges, delivered |
| **mid** | where the bulk of the volume actually sits |
| **high** | the premium brand, reachable only with brand equity we do not have |

This distinction was the single biggest correction to the earlier research,
which had repeatedly captured the premium brand and called it "the market":

- Nail grinder: recorded at $50 (Dremel PawControl, $45 to $60). The volume
  seller is Casfuy at about $20 with 88,000 reviews.
- Self-cleaning slicker brush: recorded at $29.99. Amazon listings start at $9.90.
- Slow feeder bowl: recorded at $19.99. Outward Hound, the category brand,
  starts at $8.99.
- Paw cleaner cup: recorded at $23.99. Dexas MudBuster runs $10.12 to $25.

We are an unbranded store with zero reviews. The band a shopper compares us
against is **mid**, not high. Rows are marked `live` where set from a
2026-08-04 search and `category` where inferred from a sibling product.

### 2.3 Demand: a logistic share of consideration

`config/demand_model.py`. The textbook constant-elasticity curve
`q = (p/m)^-e` was tried first and rejected: it never reaches zero, so it will
happily recommend pricing at twice the market and claim the lost volume is paid
for by the margin. It rated the store's existing 2 to 3x prices as *better* than
market prices, which is obviously wrong for a store with no traffic and no
reviews.

The replacement models the probability of winning the sale as a logistic in log
price, calibrated on the observed band rather than an assumed elasticity:

```
share(p) = 1 / (1 + (p / mid) ** beta)
```

- at **mid**, a shopper is indifferent: share = 0.50
- at **high** (the premium price) an unbranded store retains `share_at_high`
- **beta** is solved from those two points, so a wide band (mid $15, high $60,
  brand matters) yields a gentle curve and a tight band (mid $11, high $17, pure
  commodity) yields a brutal one

`share_at_high` varies by product type, because outcome goods tolerate a premium
that a squeaky toy does not: **0.28** for anxiety, cooling, sleep and dental;
**0.18** for functional tools; **0.12** for commodities.

### 2.4 Price: maximise contribution times share, under a competitive ceiling

`config/optimise_prices.py` sweeps price by the cent and maximises

```
(price - variable cost) x share(price)
```

where variable cost is goods + duty + freight + returns allowance + payment fee
from `config/pricing.py`, computed on the dearest variant.

One correction was needed on top. The raw optimum still has a fat tail: it
recommended $94.99 for the Cooling Pad, above the $59.99 premium brand, because
the curve's tail keeps a sliver of demand at any price. A store that intends to
be **competitive from day one** cannot price there, so a hard ceiling is
applied: **mid x 1.15 for outcome goods, mid for everything else.** Prices are
then rounded to .99 endings.

### 2.5 Per-variant price book

`config/build_price_book.py` turns one recommendation per product into 144
variant prices:

- **Sized products** (blankets, cooling pad, bath robe, sofa cover, paw cup,
  water bowl) are priced per size, scaling by that size's share of the dearest
  variant's unit cost, damped by `^0.7` because perceived value grows more
  slowly than weight. Without this, small sizes are overpriced and large ones
  sold at a loss.
- **Colour-only variants stay levelled** at one price. Colour-varying prices
  read as a bug to shoppers, and CJ's per-colour cost differences are cents.
- **No variant may lose money.** Anything under +5% on a worst-case single-unit
  order is nudged up to the smallest .99 that clears it.

---

## 3. Result: the singles

36 products, 144 variants. "Margin" is the **worst variant's** margin measured
the strict way the automated guard measures it: live selected-carrier freight,
duty, returns allowance, and the card fee charged on the tax-inclusive total.
Rows showing "5%+" are kit-carriers whose standalone margin is thin by design
(see section 5).

| Product | Was | Now | Market low / mid / high | Band | Margin | Variants |
|---|---|---|---|---|---|---|
| Anti-Spill Floating Water Bowl | $48.00 | $19.99 to $24.99 | $14.99 / $24.99 / $39.99 | category | 5%+ | 8 |
| Barnyard Squeaker | $19.00 | $11.99 | $7.99 / $12.99 / $19.99 | category | 25% | 7 |
| Big Squeak Plush | $28.00 | $18.99 | $12.99 / $19.99 / $29.99 | category | 32% | 2 |
| Bouncy Egg Squeaker | $16.99 | $9.99 | $6.99 / $10.99 / $16.99 | category | 19% | 4 |
| Calming Thunder Wrap | $36.99 | $31.99 | $14.99 / $27.99 / $44.95 | live | 44% | 3 |
| Cooling Comfort Pad | $34.00 | $19.99 to $33.99 | $12.00 / $29.99 / $59.99 | live | 29% | 16 |
| Cordless Paw Trimmer | $39.99 | $23.99 | $15.99 / $24.99 / $39.99 | category | 17% | 1 |
| Corduroy Squeak Pals | $19.99 | $11.99 | $7.99 / $12.99 / $19.99 | category | 20% | 3 |
| Crinkle Plush Buddy | $24.00 | $11.99 | $5.99 / $8.99 / $14.99 | category | 5%+ | 3 |
| Cuddle Companion Teddy | $19.99 | $14.99 | $9.99 / $15.99 / $24.99 | category | 37% | 1 |
| Dematting Comb | $18.99 | $13.99 | $8.99 / $14.99 / $24.99 | category | 36% | 1 |
| Dental & Ear Wipes | $22.00 | $13.99 | $7.99 / $12.99 / $19.99 | category | 30% | 2 |
| Dental Duck Chew Toy | $22.00 | $10.99 | $6.99 / $10.99 / $16.99 | category | 10% | 1 |
| Finger Toothbrush | $14.00 | $10.99 | $5.99 / $9.99 / $14.99 | category | 37% | 4 |
| Heartbeat Soothing Sloth | $43.99 | $33.99 | $19.99 / $29.99 / $49.95 | category | 37% | 1 |
| Jingle Plush Ball | $19.99 | $12.99 | $8.99 / $13.99 / $21.99 | category | 25% | 3 |
| LED Nail Clippers | $27.99 | $13.99 | $8.99 / $14.99 / $24.99 | category | 5%+ | 3 |
| LED Waste Bag Dispenser | $14.00 | $10.99 | $7.99 / $11.99 / $17.99 | category | 37% | 5 |
| Lick Bowl with Ball | $32.00 | $16.99 | $9.99 / $15.99 / $24.99 | category | 10% | 4 |
| Paw Print Fleece Blanket | $15.99 | $13.99 to $16.99 | $11.99 / $17.99 / $29.99 | category | 42% | 6 |
| Paw Washing Cup | $17.99 | $16.99 | $10.12 / $17.99 / $25.00 | live | 46% | 9 |
| Pet Hair Remover Mitt | $19.00 | $8.99 to $10.99 | $6.99 / $11.99 / $19.99 | category | 19% | 4 |
| Quick-Dry Bath Robe | $18.99 | $15.99 to $18.99 | $12.99 / $19.99 / $29.99 | live | 38% | 9 |
| Quiet Electric Nail Grinder | $39.00 | $21.99 | $15.99 / $22.99 / $59.99 | live | 22% | 2 |
| Rope-Limb Puppy Plush | $29.00 | $14.99 | $8.99 / $14.99 / $21.99 | category | 5%+ | 1 |
| Screaming Chicken | $24.99 | $12.99 | $7.99 / $12.99 / $19.99 | category | 5%+ | 3 |
| Self-Cleaning Slicker Brush | $34.00 | $17.99 | $9.90 / $15.99 / $29.99 | live | 21% | 3 |
| Slow Feeder Bowl | $26.00 | $13.99 | $8.99 / $14.99 / $24.99 | live | 21% | 3 |
| Sneaker Chew Buddy | $18.00 | $12.99 | $8.99 / $13.99 / $19.99 | category | 34% | 3 |
| Squirrel Squeaky Plush | $32.00 | $15.99 | $9.99 / $15.99 / $24.99 | category | 5%+ | 1 |
| Talk Button | $18.00 | $16.99 | $9.99 / $17.99 / $29.99 | category | 50% | 4 |
| Travel Water Bottle & Bowl | $30.00 | $18.99 | $12.99 / $19.99 / $32.99 | category | 23% | 2 |
| Watermelon Rope Frisbee | $18.00 | $10.99 | $7.99 / $11.99 / $17.99 | category | 25% | 1 |
| Waterproof Snuggle Blanket | $22.99 | $18.99 to $23.99 | $14.99 / $24.99 / $39.99 | category | 33% | 6 |
| Waterproof Sofa & Furniture Cover | $28.00 | $17.99 to $31.99 | $19.99 / $32.99 / $59.99 | category | 20% | 9 |
| Woodland Rope-Limb Plush | $24.00 | $12.99 | $7.99 / $12.99 / $19.99 | category | 11% | 6 |

**Headline.** The sum of the dearest variant across the catalogue falls from
$917.86 to $624.64. Modelled win rate against the market rises from an average
**24% to 54%**. Median margin lands in the high twenties to high thirties
depending on the view, against a former nominal 50% that was mostly theoretical
because almost nothing would have sold at those prices.

---

## 4. Result: the kits

Kits are the reason the light, cheap products exist. Freight's fixed component
is paid once per parcel, so a 30g toothbrush that costs $5.62 to ship alone adds
about $0.36 to a kit already going out. `config/optimise_kits.py` enumerates
every four and five item combination from hand-curated theme pools (with
required core items so a "grooming essentials" kit cannot drop nail care to win
on contribution), prices each at 20% off the sum of its members' new single
prices rounded to whole dollars, and ranks by contribution.

**The fitted freight curve is only allowed to nominate candidates, never to pick
the winner.** Carrier eligibility is invisible to any weight model: a basket
containing the Talk Button (electronics) gets forced onto sensitive or oversize
carrier lines, adding nearly $25 to a five-item kit. The curve's preferred
Enrichment composition returned **negative 2.1%** on a live quote. The top eight
candidates per theme are therefore re-quoted live through
`/logistic/freightCalculate` on the real component vids, and the best surviving
composition wins.

| Kit | Was | Now | Contents (singles value) | Live freight | Carrier | Margin | Contribution |
|---|---|---|---|---|---|---|---|
| New Puppy Kit | $79 | **$54** | Teddy, Sneaker, Fleece Blanket, LED Dispenser, Toothbrush ($66.95) | $13.95 | YunExpress Sensitive | 56.5% | $30.61 |
| Toy Kit | $65 | **$49** | Barnyard, Frisbee, Sneaker, Jingle Ball, Corduroy Pal ($60.95) | $12.53 | LuWei Ordinary US | 51.0% | $25.09 |
| Grooming Essentials Kit | $85 | **$70** | Slicker, Grinder, Bath Robe, Toothbrush, Paw Cup ($86.95) | $14.69 | Yunexpress CN to US | 42.3% | $29.77 |
| Travel Kit | $77 | **$85** | Bottle & Bowl, Cooling Pad XXL, Paw Cup, Bath Robe, Fleece ($105.95) | $22.86 | LuWei Ordinary US | 41.6% | $35.55 |
| Calm & Comfort Kit | NEW | **$109** | Sloth, Thunder Wrap, Fleece, Cooling Pad XXL, Big Squeak ($135.95) | $28.04 | LuWei Ordinary US | 39.3% | $43.06 |
| Dog Enrichment Kit | $98 | **$46** | Talk Button, Lick Bowl, Slow Feeder, Bouncy Egg ($57.96) | $14.85 | YunExpress Sensitive | 36.2% | $16.69 |

Notes on the changes:

- **Enrichment** fell from $98 to $46 because it was never a $98 kit. It was
  four inexpensive plastic items whose old price came from the old floor, and
  the water bowl (its heaviest member at 620g) was swapped out for the 50g
  Bouncy Egg. Even at $46 the sensitive-line surcharge holds it to the lowest
  margin in the range; it stays because it is the only kit that opens the
  enrichment category and it clears the 30% kit floor.
- **Travel went up**, from $77 to $85, because its new composition is genuinely
  more valuable ($105.95 of singles against $96 before) and it carries the
  cooling pad's XXL size.
- **Calm & Comfort is new.** It is the highest-contribution kit in the range at
  $43.06 and it monetises the anxiety category, whose products are the least
  price-elastic in the catalogue.
- Every kit is variant-selectable: shoppers pick colours per component, up to
  Shopify's three-parent-option cap, with priced options (Size, Capacity) pinned
  at the variant the kit was costed on. Colour never changes the price.
- Compare-at equals the true sum of the components' current single prices, so
  the advertised saving is real and stays real.

---

## 5. The kit-carriers

Eleven products cannot pay their own freight at a competitive standalone price.
They are not dropped: inside a kit or a multi-item basket they cost only their
marginal weight, which is typically a tenth of shipping them alone. Each is
priced at the competitive price and then nudged up only as far as needed to
clear **+5% on a worst-case single-unit order**, so none of them lose money even
if someone buys exactly one.

This is a deliberate structural position, not an oversight. It is also why the
free shipping threshold matters (section 7).

---

## 6. Guardrails after the change

The flat 50% floor is gone, so the automation that enforced it was repointed.

- **`config/margin_guard.py`** now reads `floor_margin_pct` per product from
  `config/price_book.json` instead of a global number. Its job changed from
  policing a target to **catching cost drift** against what the book promised.
  Floors are set at the worst variant's margin minus an 8 point drift buffer,
  clamped at 2%.
- **`config/calibrate_floors.py`** exists because the book and the guard measure
  margin differently: the book uses the fitted freight curve, the guard uses the
  selected carrier's live quote and charges the card fee on the tax-inclusive
  total. On light items the gap exceeds the drift buffer, so a floor computed in
  one model false-alarms in the other. **Run
  `python config/calibrate_floors.py --apply` after any deliberate repricing**,
  or the 6-hourly Actions job goes red for no real reason.
- **`config/kit_margins.py`** floor moved from 50% to **30%**, matching the
  optimiser's worth-the-complexity threshold.

Both guards were green at the end of this work: 144 of 144 variants clear their
floors, six of six kits clear 30% on live quotes.

---

## 7. Free shipping threshold

Left at **$60**, which the site copy already advertised. That is deliberate: the
$46, $49 and $54 kits sit just below it, so "add one more toy and shipping is
free" is the default upsell on the three highest-volume kits, while the $70, $85
and $109 kits clear it on their own. `config/shipping_rates.py`'s constant was
corrected from a stale $50 to match live.

---

## 8. What was tried and rejected

Recorded so nobody re-derives them.

| Idea | Why it failed |
|---|---|
| Flat 50% margin floor | Prices 33 of 36 products above their market range. Retired by owner. |
| Delivered-price parity (item = market minus $5.95 shipping) | Ten products go negative, one at negative 411%. Delivered parity is not the same as item parity when your freight is the competitor's zero. |
| Constant-elasticity optimum `p* = c·e/(e-1)` | Never decays; recommends above-market prices and rates today's 2 to 3x prices as good. |
| Uncapped logistic optimum | Fat tail still recommends $94.99 for a pad whose premium brand is $59.99. Needed the competitive ceiling. |
| Fitted freight curve for kit selection | Blind to carrier eligibility. Picks a composition that is negative 2% live. |
| CJ API keyword search for new products | `/product/list` returns newest-first with `listedNum` near zero. There is no demand-sorted API search; sourcing needs the CJ trending UI in a browser. |

---

## 9. Files

| File | Role |
|---|---|
| `config/price_book.json` | **Source of truth.** 144 variant prices + per-product `floor_margin_pct`. |
| `config/market_bands.py` | Observed low/mid/high and elasticity class per product. |
| `config/demand_model.py` | Logistic share-of-consideration curve and price sweep. |
| `config/optimise_prices.py` | Contribution maximiser with the competitive ceiling. |
| `config/build_price_book.py` | Per-variant expansion: size scaling, levelling, loss floors. |
| `config/apply_price_book.py` | Writes prices to Shopify, then re-fetches and fails if anything differs. |
| `config/optimise_kits.py` | Theme-constrained kit enumeration and ranking. |
| `config/apply_kits.py` | Writes kit compositions, bodies, prices, compare-at. Creates new kits. |
| `config/calibrate_floors.py` | Re-denominates book floors in the guard's cost model. |
| `config/reprice_catalogue.py` | Re-costs all 36 from live CJ using only our SKUs. |
| `config/validate_research.py` | Flags research rows costed against variants we do not stock. |
| `docs/qa/recost-2026-08-04.json` | Cost, weight, freight and carrier snapshot behind all of the above. |
