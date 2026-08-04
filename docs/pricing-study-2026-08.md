# Wagvive pricing study, August 2026

Commissioned to answer: are we priced competitively, and what should each
product cost to maximise profit and conversion?

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

Freight is a median **73% of our landed cost**. On the worst offenders it is
over 90%: the finger toothbrush costs $0.23 and ships for $5.62. Because
freight is roughly fixed per parcel at $5 to $8 regardless of what is in it,
it behaves as a regressive tax that destroys cheap products. A $1.45 plush toy
lands at $8.36 and needs $18.47 to clear a 50% margin, in a market that pays
$6 to $12 for it. No pricing decision fixes that. It is a structural problem
with single-item orders of low-cost goods shipped individually from China.

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
per unit**. That number, not the percentage, is what has to fund customer
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

### Cut into thin territory (25 to 40%) — acceptable as basket builders

| Product | Now | Recommended | Margin | Contribution |
|---|---|---|---|---|
| Finger Toothbrush | $14.00 | **$10.99** | 39% | $4.28 |
| Cordless Paw Trimmer | $39.99 | **$30.99** | 38% | $11.83 |
| Talk Button | $18.00 | **$12.99** | 38% | $4.93 |
| Dental & Ear Wipes | $22.00 | **$14.99** | 34% | $5.11 |
| Barnyard Squeaker | $19.00 | **$12.99** | 30% | $3.92 |
| Travel Water Bottle | $30.00 | **$20.99** | 30% | $6.33 |
| Bouncy Egg Squeaker | $16.99 | **$9.99** | 19% | $1.87 |

### Cannot work as singles — bundle only, or drop

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

---

## 6. What the pricing research says to do beyond the numbers

Ranked by expected impact.

**1. Get five reviews on every product before anything else.** Northwestern's
Spiegel Research Center found purchase likelihood rises about **270%** between
zero and five reviews, with the effect largest on higher-priced items. No price
cut available to us buys that much conversion. This is the highest-return
action in this entire document and it costs nothing but time.

**2. Consolidate shipping, then rebuild the kits around it.** See section 4.
Verify CJ's parcel behaviour first.

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

1. **Verify CJ multi-item parcel behaviour.** Everything about kit strategy
   depends on it. Check order #1001 and the next multi-item order.
2. **Replace the 50% floor with the tier table** in section 2, and repoint
   `margin_guard.py` at it.
3. **Apply the price cuts** in section 5. Catalogue price sum falls about 23%.
4. **Archive or bundle-lock the nine non-viable products.** Two should simply
   go.
5. **Re-price and re-merchandise the kits** as the primary offer once shipping
   behaviour is known.
6. **Start the review engine.** Post-purchase review requests are already
   tracked as task #63 and this study promotes it to the top of the list.
7. **Re-check AOV after 30 days** and move the free-shipping threshold.

Do not do 3 before 2, and do not do 5 before 1.

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
