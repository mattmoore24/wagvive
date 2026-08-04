# PC implementation plan, 2026-08-04

Everything the web session could not do, in the order it should be done, with
the reasoning and the exact data for each step. Written to be worked through
top to bottom in one or more PC sessions.

**Nothing in this plan has been applied to the store.** Every figure comes from
a live CJ quote or a live Shopify read on 2026-08-04.

---

## What this session will need from you

Gather these once rather than being interrupted eleven times:

- **Approval on every price, product and bundle change** before it is written.
- **CJ browser app logins**, for pairing SKUs in steps 2, 6 and 10. There is no
  API for pairing; it has to be done by hand, one product at a time.
- **Theme editor access** for step 9. Claude's live theme writes are refused by
  policy on every device.
- **GA4 measurement ID and Meta pixel ID** (task #59) if you want analytics
  installed in the same session. The store currently has none, which blocks any
  ad spend and any AOV measurement.
- Optionally, whether you want anything prepared for **#57** (NY DTF-17 filing)
  or **#64** (the CJ duty ticket). Both are yours to submit; neither needs the
  PC.

Credentials, payment details, tax filings and supplier account registrations are
yours to perform. Claude will flag and hand off, never enter them.

---

## Read these first, in this order

| Document | What it is |
|---|---|
| `docs/HANDOFF.md` | Current state, device capabilities, the full task table. Always first. |
| `docs/shipping-and-sourcing-study-2026-08.md` | How CJ actually charges freight, the kit designs, the supplier assessment. The newest and most authoritative. |
| `docs/pricing-study-2026-08.md` | Market prices for every product. Revised 2026-08-04; where the two studies disagree, the shipping study wins. |
| This file | The runbook. |

Supporting data, all machine-readable:

| File | Contents |
|---|---|
| `docs/qa/delivered-price.json` | Per product: cost, measured freight, delivered-price floors at 15/25/35%, market delivered price, margin at market, and the marginal cost of adding it to a parcel that is already shipping. **Consult this before calling any product unsellable.** |
| `docs/qa/kit-designs.json` | Every on-theme kit combination scored, plus live CJ quotes for the leaders and for all five current kits. |
| `docs/qa/freight-research.json` | Raw study: carrier menus per product, quantity ladders, multi-item baskets, US-warehouse scan, replacement candidates. |
| `docs/qa/pricing-recommendations.json` | Per-product recommended prices. **Two rows are wrong, see step 2.** |
| `docs/qa/variant-audit-2026-08.md` | The 41 missing size SKUs with CJ costs. |
| `docs/qa/theme-copy-fixes.md` | Four exact find-and-replace edits for the theme. |

---

## The three facts everything else follows from

1. **Freight is a parcel charge: $4.43 fixed plus $11.90 per kg**, measured
   across all 36 products, with no dependence on declared value. Two 100g
   products costing $1.45 and $3.45 both quote $5.59.
2. **CJ ships all five kits as ONE parcel.** Verified with live combined quotes.
   Consolidation is worth $46.99 across the five.
3. **Adding a 100g item to an order already going out costs $1.19.** Shipping it
   alone costs $5.62. That 4.7x gap is larger than any price change available.

---

## Step 1. Rebuild the Dog Enrichment Kit

**Why first:** it is live at $98 returning **24.1%** and would need $137.38 to
clear 45%. It is the largest live loss of margin in the business.

**Cause:** the Anti-Spill Floating Water Bowl is 1,833g of the kit's 2,429g.
Freight quotes $45.42 against $48.13 as separate parcels, so consolidation saves
$2.71. At that weight there is no fixed cost left to share.

**Do this:**

1. Re-quote the new composition before writing anything, because freight moves:
   `python config/research_kits.py docs/qa/freight-research.json /tmp/check.json`
   and read the `verified` entries.
2. Rebuild the bundle as **Slow Feeder Bowl + Lick Bowl with Ball + Talk Button
   + Sneaker Chew Buddy**.
3. Price at **$52.99** (quoted: $14.47 freight, 47.0% margin, $24.91
   contribution).

**Sequencing trap.** $52.99 is 20% off the *recommended* single prices, which
are not live yet. Against today's prices it reads as 43.6% off, deep enough to
cannibalise the singles. **Either do step 5 first, or recompute the kit price as
20% off whatever the singles actually are on the day.**

**Verify:** re-fetch the bundle from Shopify and confirm the components and
price, then run `config/kit_margins.py`.

---

## Step 2. Fix or withdraw the Dental & Ear Wipes

**Why:** live at $22.00 with a delivered-price floor of $18.38 against a $13.99
market. It returns **-10.7%** at market. It was healthy in July; CJ's
liquid-carrier freight went from $7.88 to $12.38 in a month and took the product
with it.

**Cause:** the 354g 50-count tub. Weight is the entire problem.

**Options, best first:**

1. **Swap to CJ SPU `CJYD2449710`**, "Cat Dog Ear Teeth Cleaning Finger Stall":
   $0.48 at **90g**, freight $5.93, **46.9% at the market ceiling**, listed by
   18 sellers. Does the same dental and ear job and pairs with the Finger
   Toothbrush already in the catalogue.
2. A smaller pack of the current product.
3. Withdraw it.

**Do NOT go to larger wipe counts.** Task #70 proposed exactly that. On a
$4.43 + $11.90/kg curve every extra wipe is pure weight, so larger counts make
the economics worse. #70 is closed as researched-and-rejected.

If you swap: pair the new SPU in the CJ browser app one product at a time,
verify `matchitem.shopType === 'Shopify'` and `first.shopSku === last.SKU`
before confirming, check `sku[:11]` against the catalogue for duplicates, and
eyeball the CJ images before uploading anything.

---

## Step 3. Recompute the slicker brush and paw trimmer

**Why before repricing:** both were costed against a CJ freight quote of exactly
$3.00 from a single carrier, while every other product was offered 19 to 27
carriers starting at $4.28. It is a placeholder, not a price, the same bug class
as the $0.00 quote already recorded in `CLAUDE.md`.

`config/freight_floor.py` now rejects any quote below 75% of the weight-fitted
estimate and substitutes the estimate. Corrected:

| Product | Old freight | Corrected | Margin at market |
|---|---|---|---|
| Self-Cleaning Slicker Brush, 80g | $3.00 | $5.37 estimated | **43.4%** |
| Cordless Paw Trimmer, 160g | $3.00 | $6.34 estimated | 35.1% |

**The brush needs no action beyond the correction.** The pricing study's
"re-source or drop" verdict was entirely an artifact of the bad quote.

**Do this:** recompute both rows in `docs/qa/pricing-recommendations.json` before
step 5 runs against that file.

---

## Step 4. Replace the 50% floor with the tier table

Owner approved dropping the flat floor on 2026-08-04. Tiers are in
`docs/pricing-study-2026-08.md` section 2:

| Tier | Target | Applies to |
|---|---|---|
| Differentiated | 55%+ | Comfort, anxiety, grooming systems |
| Comparable | 40 to 50% | Price-checkable in one search |
| Traffic and basket | 25 to 35% | Cheap impulse items that build baskets |
| Bundle-only | n/a as a single | Cannot clear 25% at market |

Repoint `config/margin_guard.py` at a per-product tier table rather than one
global number. **Do this before step 5**, or the guard will fight the new prices.

---

## Step 5. Apply the price changes

Per-product recommendations in `docs/qa/pricing-recommendations.json`, with the
two corrections from step 3 applied first. Catalogue price sum falls about 23%.

Standardise `.99` endings in the same pass. Keep `.00` for kits only.

**Check every price against `docs/qa/delivered-price.json`, not against the
pricing study's item-price tables.** Market prices are delivered prices; ours
are item prices plus $5.95 under the $60 threshold. The delivered-price file is
the like-for-like comparison and it is the one that is right.

---

## Step 6. Drop two products, swap two others

**Drop.** Neither is fixable by price or by re-sourcing.

| Product | Margin at market delivered | Why it cannot be fixed |
|---|---|---|
| Crinkle Plush Buddy | -29.5% | The cheapest item in CJ's entire plush category still lands above its $8 market ceiling. |
| Anti-Spill Floating Water Bowl | -8.4% | 1,833g, $26.59 freight on an $11.69 product. Also the thing that broke the Enrichment kit. |

Archive rather than delete, the way `config/archive_dropped.py` handled the
duplicate sneaker toy.

**Swap.** Both are straight upgrades on the same job.

| Replace | With CJ SPU | Effect |
|---|---|---|
| Squirrel Squeaky Plush | `CJPT2915091` | 70g against 112g. 12.6% to **39.6%** at market. |
| Lick Bowl with Ball | `CJYD2951433` | $0.86 of goods against $5.00. 19.6% to **54.6%**. |

Same pairing mechanics as step 2. Eyeball images, check `sku[:11]` for
duplicates.

---

## Step 7. Add the free-shipping progress bar

**The highest effort-to-return item in either study.** With $4.43 of fixed parcel
cost, an item a customer adds to reach the $60 threshold costs $1 to $3 to ship
and sells for $12 to $22:

| Product | Cost to add to an existing parcel | Market delivered price |
|---|---|---|
| Finger Toothbrush | $0.81 | $13.99 |
| LED Waste Bag Dispenser | $1.82 | $11.99 |
| Watermelon Rope Frisbee | $2.31 | $14.99 |
| Sneaker Chew Buddy | $2.94 | $16.99 |
| Barnyard Squeaker | $3.02 | $15.99 |
| Talk Button | $3.19 | $22.00 |

Benchmarks put a progress bar at an 8 to 14% conversion lift on top of the
free-shipping effect.

**Keep the threshold at $60.** It sits inside the 2026 pet AOV band of $55 to
$110, above every single item and below every kit, which is exactly the
incentive the fixed parcel cost wants.

**Related hazard:** `config/shipping_rates.py` still has `FREE_THRESHOLD = 50.00`
in its constants and docstring while the store is set to $60. Running it with
`--apply` today would move the threshold back and give away $5.95 on every order
between $50 and $60. Fix the constant, or do not run it.

---

## Step 8. Launch the Calm & Comfort Kit

Four of the highest-contribution products in the catalogue are in no kit at all.
Quoted live:

| Composition | Price | Weight | Freight | Margin | Contribution |
|---|---|---|---|---|---|
| Heartbeat Sloth + Thunder Wrap + Cooling Comfort Pad | **$85.99** | 1,120g | $17.34 | **51.3%** | $44.10 |
| Add Paw Print Fleece Blanket | $100.99 | 1,340g | $20.19 | 53.0% | $53.52 |

$44.10 is more contribution than any existing kit. Start with the three-item
version at $85.99; the four-item one is above the AOV band's midpoint.

**Do not add the Waterproof Snuggle Blanket.** Quoted with it in, the kit goes to
2,340g and $32.15 of freight, and margin falls to 33.6%.

---

## Step 9. Theme copy fixes

Four exact find-and-replace edits in `templates/product.json`, all appearing on
**every** product page: three en/em dashes, one trust badge, and a "Care & use"
block that tells customers to rinse and dry disposable wipes and still mentions
"older or anxious dogs".

Exact text: `docs/qa/theme-copy-fixes.md`. About five minutes in the theme
editor. Claude cannot do this from any device: live theme writes are refused by
policy. Every other theme file was scanned and is clean.

---

## Step 10. The 41 missing size variants

Four products are missing sizes CJ actually sells: sofa cover 12, snuggle blanket
9, fleece blanket 12, cooling pad 8. Exact SKU list with CJ costs is the appendix
of `docs/qa/variant-audit-2026-08.md`.

Sequence, one product at a time:

1. Pair each SKU in the CJ browser app. Verify `matchitem.shopType ===
   'Shopify'` and `first.shopSku === last.SKU` before confirming. A failed
   confirm nulls `matchitem` and every later attempt throws until reload.
2. Claude resolves freight through `config/freight_floor.py` and prices each size
   against its **tier** floor (step 4), levelling colours up to the most
   expensive variant. Review the price table before anything is written.
3. Claude creates the Shopify variants, wires `variant.image_id`, sets inventory.

**Expect freight to kill the largest sizes.** The sofa cover is already 1,340g at
Medium; the Large will be worse. Drop the ones that fail rather than pricing them
under floor, and record which and why.

Rename the sofa cover size labels in the same pass: our Small, Medium and Large
are really CJ's XS, S and M of seven sizes.

---

## Step 11. Reviews

Task #63, and the pricing study's highest-return recommendation. Purchase
likelihood rises about 270% between zero and five reviews. Judge.me free tier or
similar; owner installs the app, Claude configures it.

---

## Still open, and why

| Question | Status |
|---|---|
| **Waterproof Snuggle Blanket**, 1,220g, -12.4% | No like-for-like exists at CJ under the ceiling. Everything that clears 15% is a lighter, smaller, non-waterproof blanket. Either sell that and describe it honestly, or source from a US warehouse. |
| **Waterproof Sofa & Furniture Cover**, 1,340g, +9.3% | The scan did not answer it. Furniture covers are not in any of the 16 pet categories mapped in `config/research_freight.py`; they sit in CJ's home-textiles tree. Positive margin, so not urgent. |
| **US-warehouse scan of the heavy categories** | Highest-value sourcing question left. `/product/list` accepts `countryCode` and it works: 70 of 350 plush toys are US-stocked, which the `CJBQ` prefix test never sees. The advantage is a pure weight effect: a 1,171g cooling pad quotes $14.65 from the US against $18.00 from China. Run it on Blankets and quilts, Pet mats and Pet bowls. About 15 minutes. |
| **Duty** (task #64) | CJ's freight quote is provably value-independent, so it contains no ad-valorem tariff. Whether the 20% in `pricing.py` is billed elsewhere or is pure conservatism is worth 20% of product cost on every order. One support ticket, owner-raised, order-gated, and order #1001 exists. |
| **GA4 and Meta pixel** (task #59) | Needs the owner's own measurement and pixel IDs. Store has zero analytics, which blocks ad spend and any AOV measurement. |
| **NY sales tax** (task #57) | Owner files DTF-17 at NY Business Express. Needs SSN or EIN, so it is the owner's to do. |
| **Lifestyle image audit** (task #66) | Every product now has one, but only the dematting comb has been checked against the CJ reference, and it was wrong. Do this before paying for traffic. |

---

## Do not do these

1. **Do not switch suppliers.** US dropship wholesalers price at 40 to 50% below
   MSRP, but MSRP is the market price we compete at, so a $15 toy costs $8.25
   wholesale plus $6 domestic shipping. Independent reviews put US and EU
   suppliers at 30 to 40% margins against 45 to 55% on Chinese sourcing, and
   flag low-ticket items as exactly where the model breaks. Platform fees run
   $34.99 to $59.99 a month on top.
2. **Do not sign a 3PL.** $2.75 first item and $0.50 per additional to pick and
   pack, $10 to $14 all-in per order including carriage, and monthly minimums
   averaging over $500. That is $6,000 a year before the first order.
3. **Do not buy bulk inventory speculatively.** It genuinely works: air freight
   DDP from China is $4 to $8 per kg with duty included, so a 300g item lands
   for $1.20 to $2.40 against $8.00 today, and CJ will hold it in its own US
   warehouse with 90 days free storage then $0.80 per cubic metre per day. But
   the MOQ is 10 per variant and 100 total, which is $300 to $500 committed per
   product before a single sale. Revisit for **one** product once it is selling
   more than about 20 units a month.
4. **Do not open TikTok Shop catalogue-wide.** Median pet price there is $15.53,
   69% sell under $20, and all-in costs run 35 to 55% of revenue. Only the four
   high-contribution items and the kits could work.

The one exception worth pursuing: a zero-fee US supplier for the two heavy
fabric items. **Essential Pet Products** is the candidate, and opening the
account needs your store name and tax ID, so it is yours to do, not mine.
Shopify Collective is also free and plugs straight into the store, and is worth
applying to on those grounds alone.

---

## Before saying any of this is done

Verify against the live system, not the tool's return value. Re-fetch the object,
load the storefront, check the rendered HTML. Several "successful" writes in this
project's history did nothing.

For prices and kits specifically: run `config/margin_guard.py`, run
`config/kit_margins.py`, and re-quote through `config/research_kits.py`. Freight
moved 57% and 72% on two products in a single month, so **a price set against a
freight quote is perishable** and the guard is what catches it.
