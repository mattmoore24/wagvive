# Wagvive pricing study, August 2026

Commissioned to answer: are we priced competitively, and what should each
product cost to maximise profit and conversion?

> **Revised 2026-08-04, later the same day.** The shipping study that followed
> this one measured what this study could only assume, and it changed several
> conclusions. Read `docs/shipping-and-sourcing-study-2026-08.md` alongside this
> document; where the two disagree, the shipping study wins, because it is built
> on live CJ quotes rather than on estimates. The corrections are marked
> **REVISED** inline and summarised immediately below. The market research in
> sections 5 to 7 stands unchanged: those are observed competitor prices, and
> nothing about freight alters them.

## What the shipping study changed

| This study said | Corrected |
|---|---|
| Freight is "roughly fixed per parcel at $5 to $8". | Measured: **$4.43 fixed plus $11.90 per kg**, fitted across 36 products with no residual over $1.56. Not fixed, but with a large fixed component. |
| Unknown whether CJ ships kits as one parcel. Kit margin 51% or 71%. | **Answered: CJ ships all five live kits as ONE parcel.** Every one returned a combined quote. |
| Nine products cannot work as singles. | Scored on **delivered** price, which is the like-for-like comparison, **30 of 36 clear 15% and 25 clear 25%**. Only three of the nine survive; three products this study passed are actually failing. |
| Slicker brush: "re-source or drop", our most expensive product cost. | It was costed against a **$3.00 placeholder freight quote** that does not exist. On real freight it returns **43.4%** and needs nothing. |
| Nothing said about the Dog Enrichment Kit. | It is live at $98 returning **24.1%** and needs $137.38 to clear 45%. The worst position in the catalogue. |
| Nothing said about the Dental & Ear Wipes. | CJ's liquid-carrier freight rose **57% in a month** and the product is now live above a price it can sustain. |

---

Method: seven parallel research streams. Five covered observed US market prices
for every product (Amazon, Chewy, Petco, PetSmart, Walmart, Target, Temu,
AliExpress, eBay, TikTok Shop, and brand DTC sites), one covered pricing
science for unbranded new stores, one covered marketplace dynamics. Internal
economics come from `config/pricing.py`, the live CJ variant data in
`docs/qa/cj-variants.json`, and the margin guard's re-quote of every variant on
2026-08-02. Every market price cited in the source reports is one that was
actually observed, with a link.

---

## 1. The short answer

**Yes, we are priced too high, and it is not close.** Of 36 products, 33 sit
above the top of their observed market range. Many sit at two to three times
the typical transacted price. On six of seven plush toys, the *brand-name*
market leader is cheaper than our generic: KONG Cozie at $11.96 against our
$29 rope-limb puppy, ZippyPaws' entire three-pack at $14.99 against our $32
single squirrel, PetSafe's latex duck at $6.08 against our $22 duck.

**But the headline finding is not the prices. It is the freight.**

Freight is a median **65% of our landed cost** and over 90% on the worst
offenders: the finger toothbrush costs $0.36 and ships for $4.75. Because
freight carries a large fixed component per parcel, it behaves as a regressive
tax that destroys cheap products. A $1.45 plush toy lands at $8.36 and needs
$18.47 to clear a 50% margin, in a market that pays $6 to $12 for it. No pricing
decision fixes that. It is a structural problem with single-item orders of
low-cost goods shipped individually from China.

**REVISED.** The shipping study measured the shape of that fixed component
exactly: freight is **$4.43 per parcel plus $11.90 per kg**, and it does not
vary with declared value at all. Two 100g products costing $1.45 and $3.45 both
quote $5.59. That refines the conclusion rather than overturning it, and it adds
the number that matters most: **adding a 100g toy to an order already going out
costs $1.19, against $5.62 to ship it alone.** The regressive tax is $4.43, and
it is paid once per parcel, not once per item. Everything about kits, cross-sell
and the free-shipping threshold follows from that one figure.

This reframes the brief. The question is not "what should each product cost".
It is **"which products can survive at market prices, and how do we sell them
so freight stops eating the margin"**.

---

## 2. On the 50% floor

You said you are open to removing it, and the evidence supports that. The 50%
figure is not derived from anything: it is a round number chosen at launch. Two
things about it are worth knowing.

**It is simultaneously too high and too low.** Too high, because it makes 24 of
36 products unsellable at market prices. Too low, because on the products that
genuinely work (nail grinder, cooling pad, sofa cover) the market supports
55 to 66% and a 50% floor would leave money on the table if treated as a target.

**Removing it does not rescue the catalogue.** Repriced to the top of each
product's observed market band, the median margin across the catalogue is
**49%**, and 27 of 36 products still clear 25%. The nine that fail do not fail
because of the floor. They fail because landed cost exceeds what the market
will pay. Dropping the floor to 35% saves seven of those nine; dropping it to
zero saves none of the remaining two, which lose money at market price.

**REVISED, and the correction is mine to own.** This paragraph compares our
*item* price against market prices that are *delivered* prices, and it never
counts the $5.95 the customer pays for shipping on any order under $60. Those
two conservatisms point in opposite directions, so the combination is not
cautious, it is simply wrong: it overstates our price against the market while
understating our revenue. Done like for like, on measured freight, **30 of 36
products clear 15% at the market delivered price, 25 clear 25%, and the median
margin is 45%**. `config/delivered_price.py` is the tool that does this
properly, and it should be consulted before any product is called unsellable.
The tier table below is unaffected and stands.

**Recommendation: replace the single floor with three tiers.**

| Tier | Target margin | Applies to |
|---|---|---|
| Differentiated | 55% or better | Comfort, anxiety, grooming systems. Low comparability, brand and imagery do the work. |
| Comparable | 40 to 50% | Items a shopper can price-check in one search. Price at market, accept the lower margin, win on presentation. |
| Traffic and basket | 25 to 35% | Cheap impulse items whose job is to build baskets and hit the free-shipping threshold, not to make money alone. |
| Bundle-only | n/a as a single | Anything that cannot clear 25% at market price. Sell inside kits only. |

The margin guard should enforce the tier assigned to each product rather than
one global number, and `--apply` should be repointed at the tier table.

---

## 3. Why contribution dollars matter more than margin percent

At market-realistic prices, the median product returns **$7.19 of contribution
per unit** (**REVISED: $7.78** on measured freight and delivered prices, which
does not change the argument). That number, not the percentage, is what has to fund customer
acquisition.

Published DTC benchmarks put paid acquisition at **$38 to $58 per customer**
against **$12 to $18 on Amazon**. A single-item order at $7 of contribution
cannot pay for a $40 click. It is not close: you would need five to eight items
per order to break even on paid traffic, or acquisition has to be effectively
free (organic, TikTok, referral).

This is the second structural finding, and it points the same direction as the
first: **average order value has to rise, and the way to raise it is bundles.**

---

## 4. Kits are the answer to both problems

The Grooming Essentials Kit contains four items costing $9.75 in total. Shipped
as four separate parcels, freight is $25.56. Shipped as one, it is roughly $9.

| Scenario | Landed | Price | Contribution | Margin |
|---|---|---|---|---|
| Four separate parcels | $38.38 | $85 | $43.68 | 51% |
| One combined parcel | $21.32 | $85 | $60.74 | 71% |
| One combined parcel | $21.32 | $65 | $41.36 | 64% |
| One combined parcel | $21.32 | $59 | $35.55 | 60% |

A kit at a **market-credible $59** earns $35.55 of contribution, five times the
median single item, at a 60% margin. And kits have a second advantage the
research is emphatic about: **a curated bundle has no Amazon comparable**, so
the reference price that crushes our singles does not exist. This is the single
highest-leverage change available.

**Caveat that must be checked before acting:** the combined-parcel figure
assumes CJ ships a multi-item order as one consignment. CJ often splits by
supplier warehouse. If kits are shipping as separate parcels today, kit margins
are the 51% row, not the 71% row, and consolidating them is worth more than any
repricing in this document. **Verify on order #1001 and the next kit order.**

Note also that the margin guard currently checks 147 variants but **kits are
not among them** (their SKUs are null), so kit economics have never been
verified against live CJ costs at all.

### REVISED: the caveat is resolved, and the table above was wrong

`config/research_kits.py` quoted every live kit's exact composition against CJ.
**All five return a combined quote. CJ ships them as one parcel.** So the good
row was the right one, and consolidation is worth $46.99 across the five kits.

The illustrative Grooming Essentials figures above were built on estimates and
on a composition that is not the live one. The measured position, on real
quotes:

| Kit | Price | Goods | Weight | Separate | One parcel | Margin |
|---|---|---|---|---|---|---|
| New Puppy | $79.00 | $6.68 | 352g | $17.28 | $9.85 | **73.2%** |
| Toy | $65.00 | $8.27 | 368g | $21.83 | $8.50 | **67.2%** |
| Travel | $77.00 | $12.23 | 525g | $23.80 | $12.83 | **59.7%** |
| Grooming Essentials | $85.00 | $16.90 | 451g | $23.55 | $11.00 | **58.6%** |
| **Dog Enrichment** | $98.00 | $19.59 | 2,429g | $48.13 | $45.42 | **24.1%** |

So the strategic conclusion of this section holds, and holds more strongly than
it claimed. But it missed the one kit that is actually broken. The **Dog
Enrichment Kit** returns 24.1% and needs $137.38 to clear 45%, because the
Anti-Spill Floating Water Bowl is 1,833g of its 2,429g and consolidation saves
only $2.71 at that weight. Rebuilt without it, quoted live: Slow Feeder Bowl +
Lick Bowl with Ball + Talk Button + Sneaker Chew Buddy at **$52.99 for 47.0%**.

Two composition rules the quotes established, which this study had no way to
anticipate:

1. **Never put a 1.8kg item in a kit.** At that weight there is no fixed cost
   left to share, so the kit is paying full freight and giving a discount.
2. **Bulky-but-light behaves like heavy.** Four candidate kits pairing the Slow
   Feeder Bowl with a bulky plush quoted **$42 to $49 of freight at only 840 to
   908g**, because the combined dimensions force an over-length carrier.
   Dimensional weight, not mass, picks the line.

Full designs, including a proposed Calm & Comfort kit at $85.99 for 51.3%, are
in `docs/shipping-and-sourcing-study-2026-08.md` section 5.

---

## 5. Per-product recommendations

Recommended prices sit at the **top of each product's observed typical market
band**, with .99 endings. Rationale: the only clean experimental estimate of
the "unknown seller" penalty is about **8%** (Resnick et al., eBay matched-pair
field experiment), not the 30% that intuition suggests, and it is cheaper to
close that gap with reviews and guarantees than with price. So we price at
market, not below it, and spend the difference on trust.

`p@35%` is the price this product would need to clear a 35% margin. Where that
exceeds the market high, the product cannot work as a single at any sensible
margin.

### Cut, and still healthy (margin 45% or better)

| Product | Now | Recommended | Margin | Contribution |
|---|---|---|---|---|
| Quiet Electric Nail Grinder | $39.00 | **$30.99** | 66% | $20.55 |
| Cooling Comfort Pad (M) | $34.00 | **$25.99** | 59% | $15.38 |
| Pet Hair Remover Mitt | $19.00 | **$16.99** | 58% | $9.94 |
| LED Nail Clippers | $27.99 | **$21.99** | 58% | $12.71 |
| Dematting Comb | $18.99 | **$17.99** | 50% | $8.97 |
| Sneaker Chew Buddy | $18.00 | **$17.99** | 50% | $8.97 |
| Corduroy Squeak Pals | $19.99 | **$18.99** | 49% | $9.23 |
| Heartbeat Soothing Sloth | $43.99 | **$40.99** | 47% | $19.46 |
| Watermelon Rope Frisbee | $18.00 | **$15.99** | 47% | $7.58 |
| Cuddle Companion Teddy | $19.99 | **$17.99** | 47% | $8.42 |
| LED Waste Bag Dispenser | $14.00 | **$12.99** | 47% | $6.05 |
| Slow Feeder Bowl | $26.00 | **$16.99** | 46% | $7.87 |
| Big Squeak Plush | $28.00 | **$23.99** | 45% | $10.87 |

### Hold or raise (already at or below market)

| Product | Now | Recommended | Margin |
|---|---|---|---|
| Waterproof Sofa Cover (S) | $28.00 | **$30.99** | 58% |
| Paw Washing Cup (S) | $17.99 | **$20.99** | 58% |
| Paw Print Fleece Blanket (S) | $15.99 | **$17.99** | 60% |
| Waterproof Snuggle Blanket (XS) | $22.99 | **$25.99** | 56% |
| Calming Thunder Wrap | $36.99 | **$40.99** | 55% |
| Quick-Dry Bath Robe (XS) | $18.99 | **$18.99** | 51% |
| Jingle Plush Ball | $19.99 | **$19.99** | 50% |

The thunder wrap is the strongest position in the catalogue: it undercuts
ThunderShirt ($44.99 to $54.99 at like size) while beating generic Amazon
vests on presentation. The listing should name that comparison explicitly.

### Cut into thin territory (25 to 40%), acceptable as basket builders

| Product | Now | Recommended | Margin | Contribution |
|---|---|---|---|---|
| Finger Toothbrush | $14.00 | **$10.99** | 39% | $4.28 |
| Cordless Paw Trimmer | $39.99 | **$30.99** | 38% | $11.83 |
| Talk Button | $18.00 | **$12.99** | 38% | $4.93 |
| Dental & Ear Wipes | $22.00 | **$14.99** | 34% | $5.11 |
| Barnyard Squeaker | $19.00 | **$12.99** | 30% | $3.92 |
| Travel Water Bottle | $30.00 | **$20.99** | 30% | $6.33 |
| Bouncy Egg Squeaker | $16.99 | **$9.99** | 19% | $1.87 |

### Cannot work as singles, bundle only or drop

| Product | Now | Market high | Price needed for 35% | Verdict |
|---|---|---|---|---|
| Rope-Limb Puppy Plush | $29.00 | $15.99 | $21.68 | Bundle only |
| Dental Duck Chew Toy | $22.00 | $10.99 | $15.33 | Bundle only |
| Woodland Rope-Limb Plush | $24.00 | $13.00 | $17.99 | Bundle only |
| Screaming Chicken | $24.99 | $13.99 | $18.41 | Bundle only |
| Lick Bowl with Ball | $32.00 | $19.00 | $23.73 | Bundle only |
| Self-Cleaning Slicker Brush | $34.00 | $29.99 | $27.80 | Re-source or drop |
| Squirrel Squeaky Plush | $32.00 | $16.23 | $22.77 | Drop |
| Anti-Spill Floating Water Bowl | $48.00 | $40.00 | $34.47 | **Drop** (loses money at market price) |
| Crinkle Plush Buddy | $24.00 | $8.00 | $17.70 | **Drop** (loses money at market price) |

Two of these are worth calling out. The **anti-spill water bowl** carries
$15.47 of freight on a $4.13 product and would need $34.47 to make 35%, in a
market where the equivalent sells for $13 to $18 and the premium branded
Slopper Stopper is $40. The **crinkle plush** competes against three-packs at
$2.38 per toy. Neither is fixable with a price change.

The **slicker brush** is a special case worth one check before dropping: at
$8.26 it is by far our most expensive product cost, and the Hertzko category
leader sells at $12 to $14 on near-permanent promotion. Re-sourcing it at a
lower cost is more promising than repricing it.

### REVISED: this table is superseded

Scored on delivered price with measured freight, six of the nine above are fine
and three products this study passed are failing instead. Use this list:

**Cannot work, drop them.** Neither is fixable by price or by re-sourcing.

| Product | Margin at market delivered | Why |
|---|---|---|
| Crinkle Plush Buddy | **-29.5%** | The cheapest thing in CJ's whole plush category still lands above its $8 ceiling. |
| Anti-Spill Floating Water Bowl | **-8.4%** | 1,833g. $26.59 of freight on a $11.69 product, and it breaks the Enrichment kit too. |

**Broken by freight drift, fixable.**

| Product | Margin at market delivered | Fix |
|---|---|---|
| Dental & Ear Wipes | -10.7% | The 354g pack is the problem, not the product. CJ SPU CJYD2449710, a 90g ear and teeth finger-stall wipe, returns **46.9%**. |
| Waterproof Snuggle Blanket | -12.4% | 1,220g. No like-for-like exists at CJ under the ceiling. Either sell a lighter blanket honestly described, or source from a US warehouse. |
| Waterproof Sofa & Furniture Cover | +9.3% | 1,340g. Positive but under 15%. Not urgent. US warehouse is the likely answer. |
| Squirrel Squeaky Plush | +12.6% | Swap to CJ SPU CJPT2915091, 70g against 112g, giving **39.6%**. |

**Wrongly written off above. All clear 15% as singles on corrected freight.**

| Product | Verdict here | Actual |
|---|---|---|
| Self-Cleaning Slicker Brush | Re-source or drop | **43.4%.** It was costed against a $3.00 placeholder quote. No action needed. |
| Lick Bowl with Ball | Bundle only | 19.6%, and swapping to a $0.86 silicone lick mat gives 54.6%. |
| Dental Duck Chew Toy | Bundle only | 18.2% |
| Woodland Rope-Limb Plush | Bundle only | 17.5% |
| Rope-Limb Puppy Plush | Bundle only | 15.7% |
| Screaming Chicken | Bundle only | 15.5% |

The five "bundle only" toys clear 15% but only just, so the advice to lead with
them inside kits rather than on the shop front still holds. What changes is that
they no longer have to be hidden from the catalogue.

---

## 6. What the pricing research says to do beyond the numbers

Ranked by expected impact.

**1. Get five reviews on every product before anything else.** Northwestern's
Spiegel Research Center found purchase likelihood rises about **270%** between
zero and five reviews, with the effect largest on higher-priced items. No price
cut available to us buys that much conversion. This is the highest-return
action in this entire document and it costs nothing but time.

**2. Consolidate shipping, then rebuild the kits around it.** See section 4.
~~Verify CJ's parcel behaviour first.~~ **REVISED: verified. CJ already ships
every kit as one parcel**, so there is nothing to consolidate and the work is
purely rebuilding the Enrichment kit and adding the Calm & Comfort kit. The
related action this study missed is a **free-shipping progress bar**: with
$4.43 of fixed parcel cost, an item a customer adds to reach $60 costs $1 to $3
to ship and sells for $12 to $22.

**3. Standardise on .99 endings.** The left-digit effect is one of the
best-replicated findings in pricing (Strulov-Shlain, *Review of Economic
Studies* 2023, finds retailers systematically under-exploit it and forgo 1 to
4% of gross profit). Our catalogue currently mixes `.00` and `.99`, which
captures neither the charm effect nor the round-number quality signal. All
recommended prices above use `.99`. Keep `.00` only for kits, where round
numbers read as curated.

**4. Anchor kits against the true sum of parts.** "$74 value" is legally safe
because it is a real price we charge. Never fabricate a compare-at price;
fictitious pricing draws FTC and state action.

**5. Show the delivery date, do not hide it.** 53% of shoppers have abandoned a
cart over slow delivery, but around 90% will accept slower shipping for a lower
price. The honest "arrives in 5 to 12 business days" already on our pages is a
differentiator against Temu's checkout-fee ambush, not an apology. Say it
earlier and more plainly.

**6. Protect the photography.** Google Lens processes roughly 20 billion visual
searches a month, about a fifth shopping-related, and free browser extensions
reverse-image any product photo onto Temu in seconds. Our Runway master images
are doing more pricing work than any copy on the site because they break that
match. A supplier photo must never appear on a product page or in an ad.

**7. Do not launch a discount habit.** Companies running more than four major
discount events a year show roughly **30% lower willingness to pay**. Use one
email-gated welcome code at 10 to 15% rather than sitewide sales.

**8. Reconsider the $60 free-shipping threshold once AOV is known.** The
practitioner consensus is 20 to 30% above AOV. If repricing drops AOV toward
$35, a $60 threshold becomes unreachable and reads as a shipping surcharge.
$45 would likely be the better number after the cuts.

**REVISED: keep $60, and revisit only with real AOV data.** Pet-category AOV
benchmarks for 2026 land at $55 to $110, so $60 is inside the band rather than
above it. It also sits above every single item and below every kit, which is
exactly the incentive structure the $4.43 fixed parcel cost wants. Note as well
that `config/shipping_rates.py` still has `FREE_THRESHOLD = 50.00` in its
constants while the store is set to $60; running it with `--apply` would move
the threshold back and give away $5.95 on every order between $50 and $60.

---

## 7. TikTok Shop implications

You raised TikTok Shop as the trigger for this study. The research is
unambiguous and it is bad news for most of the catalogue.

- Median pet product price on TikTok Shop is **$15.53**, and **69% of pet
  products sell below $20**.
- All-in selling costs run **35 to 55% of revenue** once the ~6% referral fee,
  affiliate commissions of 5 to 20%, and Shop Ads at 15 to 25% are counted.
- Displayed prices are distorted downward by platform subsidies and coupons of
  20 to 50%, so shoppers' remembered price is well below sticker.

Combined with our contribution figures, **most single products cannot be sold
profitably on TikTok Shop at all**. A product returning $7 of contribution
cannot absorb another 35 to 55% of revenue in platform costs. The only
candidates are the high-contribution items (nail grinder at $20.55, thunder
wrap at $22.73, heartbeat sloth at $19.46, sofa cover at $17.98) and kits.

This should gate task #60. TikTok Shop is not a channel to open catalogue-wide.

---

## 8. Recommended sequence

~~1. Verify CJ multi-item parcel behaviour.~~ **Done. CJ ships every kit as one
   parcel.**

**REVISED sequence.** Superseded by the runbook in
`docs/pc-implementation-plan-2026-08.md`, which is the document to work from.
In outline:

1. **Fix the two live losers first**: rebuild the Dog Enrichment Kit, and fix or
   withdraw the Dental & Ear Wipes. Both are losing money today, which nothing
   else in this study is.
2. **Recompute the slicker brush and paw trimmer** on real freight before
   repricing anything, because their rows in
   `docs/qa/pricing-recommendations.json` were built on a placeholder quote.
3. **Replace the 50% floor with the tier table** in section 2, and repoint
   `margin_guard.py` at it.
4. **Apply the price cuts** in section 5, checked against
   `docs/qa/delivered-price.json` rather than against item-price comparisons.
5. **Drop the two products that cannot work**, swap the two with better
   equivalents.
6. **Add the free-shipping progress bar** and launch the Calm & Comfort kit.
7. **Start the review engine** (task #63). Still the highest-return action in
   this document.
8. **Re-check AOV after 30 days.** Keep the $60 threshold until there is data.

Do not do 4 before 3, and do not do 4 before 2. Kit prices are 20% off the
*recommended* singles, so the kit changes in step 1 have to be re-priced if
step 4 has not happened yet.

---

## Appendix: sources

Full sourced market tables, with a link for every price observed, are in the
seven research reports summarised here. Principal external sources: Amazon,
Chewy, Petco, PetSmart, Walmart, Target, Five Below, eBay, AliExpress, Temu,
TikTok Shop, and brand sites (KONG, ZippyPaws, Outward Hound, ThunderShirt,
Snuggle Puppy, Dexas, Hertzko, Casfuy, PetAmi, Bedsure, FluentPet).
Pricing-science sources: Resnick et al. on seller reputation, Spiegel Research
Center on reviews, Strulov-Shlain (*RESTUD* 2023) on left-digit pricing,
Akçay/Boyacı/Zhang (*POM* 2013) on money-back guarantees, APPA 2026 industry
data, Profitero 2025 price-comparison study.
