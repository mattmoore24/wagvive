# Session handoff — read this first on any device

> Protocol: every Claude session starts by reading this file, and updates it
> (plus commits and pushes) before the user switches devices or ends a work
> session. This file IS the conversation continuity between devices.

**Last updated:** 2026-08-04, from a claude.ai/code web session

---

# START HERE: the PC session works from the implementation plan

Two studies finished on 2026-08-04 and between them they produced a queue of
changes that need a keyboard, a CJ browser login and theme access. That queue is
written up as a single runbook:

### → `docs/pc-implementation-plan-2026-08.md`

Eleven ordered steps, each with the reasoning, the exact data, the sequencing
traps, and how to verify it worked. **Work from that file.** The task table
further down this document is the index; the plan is the instructions.

The two things that are losing money right now, and should be done first:

1. **Dog Enrichment Kit** is live at $98 returning **24.1%** and needs $137.38
   to clear 45%. Plan step 1.
2. **Dental & Ear Wipes** is live at $22.00 against a $13.99 market it cannot
   reach, after CJ's freight on liquids rose 57% in a month. Plan step 2.

### All research, and what each file is for

| File | Use it for |
|---|---|
| `docs/pc-implementation-plan-2026-08.md` | **The runbook.** What to do, in order. |
| `docs/shipping-and-sourcing-study-2026-08.md` | How CJ charges freight, kit designs with live quotes, replacement products, supplier assessment. Newest and most authoritative. |
| `docs/pricing-study-2026-08.md` | Observed market prices for every product, and the pricing science. Revised 2026-08-04 with **REVISED** callouts where the shipping study corrected it. |
| `docs/qa/delivered-price.json` | Per product: measured freight, delivered-price floors, margin at market, and the marginal cost of adding it to a parcel already shipping. **Check here before calling anything unsellable.** |
| `docs/qa/kit-designs.json` | Every on-theme kit combination scored, with live CJ quotes for the leaders and all five current kits. |
| `docs/qa/freight-research.json` | Raw study: carrier menus, quantity ladders, multi-item baskets, US-warehouse scan, replacement candidates. |
| `docs/qa/pricing-recommendations.json` | Recommended price per product. Two rows are wrong; see plan step 3. |
| `docs/qa/variant-audit-2026-08.md` | The 41 missing size SKUs with CJ costs. |
| `docs/qa/theme-copy-fixes.md` | Four exact find-and-replace edits for the theme. |
| `docs/knowledge/` | Durable how-it-works notes, e.g. the CJ inventory sync model. |

Tooling built for this work, all read-only against CJ and runnable from the PC:

| Script | Does |
|---|---|
| `config/research_freight.py` | Measures CJ freight end to end. Runs in Actions via `cj-freight-research.yml`. |
| `config/research_kits.py` | Ranks on-theme kit combinations, then quotes the leaders live. Triggered by touching `config/kit_run.json`. |
| `config/delivered_price.py` | Offline. Scores every product on delivered price. No CJ calls. |
| `config/freight_floor.py` | The one place that decides what freight to trust. Now rejects placeholder quotes as well as zeros. |

---

## Where the business stands

wagvive.com is LIVE and fully operational: 41 active products (36 singles + 5
variant-selectable bundle kits), all CJ-paired. **Margin status is no longer
"all above the 50% floor", and has not been since 2026-08-04**: the margin guard
only ever checked the 147 single variants, never the kits, and the shipping
study found the Dog Enrichment Kit at 24.1% and the Dental & Ear Wipes below
water at its live price. See the implementation plan. First real order (#1001) completed the full loop: checkout → CJ →
paid → shipped → tracking back → branded emails from hello@wagvive.com.
Storefront password is off, SEO/social cards are set, all 18 notification
emails are branded.

Operations run themselves: GitHub Actions (`scheduled-ops.yml`) syncs CJ stock
into Shopify, repairs inventory locations, and checks margins **every 6 hours**.
A failed run emails the owner — silence means healthy.

## What just happened (most recent work)

- **SHIPPING AND SOURCING STUDY (2026-08-04).** Report:
  `docs/shipping-and-sourcing-study-2026-08.md`, data in
  `docs/qa/freight-research.json`, `docs/qa/kit-designs.json` and
  `docs/qa/delivered-price.json`. Measured CJ live across all 36 products.
  **Task #72 is answered: CJ ships every one of the five live kits as ONE
  parcel.** Freight is a parcel charge of about **$4.43 fixed plus $11.90 per
  kg**, fitted with no residual over $1.56 from 30g to 1.8kg, and it does not
  depend on declared value at all: two 100g products costing $1.45 and $3.45
  both quote $5.59. So adding a 100g toy to an order already going out costs
  $1.19 of freight against $5.62 to ship it alone, and consolidation is worth
  $46.99 across the five kits. Three things it changed:
  (1) the **Dog Enrichment Kit returns 24.1% at $98** and needs $137.38 to clear
  45%, because the Anti-Spill Water Bowl is 1,833g of its 2,429g (task #76);
  (2) the **Dental & Ear Wipes is live above a price it cannot sustain** after
  CJ's liquid freight rose 57% in a month (task #77);
  (3) the **slicker brush and paw trimmer were priced on a $3.00 placeholder
  freight quote** from a single carrier, the same bug class as the $0.00 quote
  already in CLAUDE.md. `freight_floor.py` now rejects anything under 75% of the
  weight-fitted estimate (task #78).
  Scored on DELIVERED price rather than item price, which is the like-for-like
  comparison against Amazon, **30 of 36 products clear 15% at market**, so the
  pricing study's nine write-offs were too harsh and named the wrong products.
  Supplier verdict: **stay on CJ.** US wholesalers raise landed cost on
  everything except heavy goods, a 3PL is $10 to $14 an order plus a $500
  monthly minimum, and bulk is a working-capital decision for one proven
  product. The one real gap is the two heavy fabric items, where a US warehouse
  would change the answer; CJ's `/product/list` does accept `countryCode`, which
  the CJBQ prefix test never sees.

- **PRICING STUDY (2026-08-04).** Full market research on all 36 products plus
  the pricing literature. Report: `docs/pricing-study-2026-08.md`, data in
  `docs/qa/pricing-recommendations.json`. Headline: **33 of 36 products are
  priced above the top of their observed market range**, several at 2 to 3x,
  and on six of seven plush toys the brand-name leader (KONG, ZippyPaws,
  PetSafe) is cheaper than our generic. But the binding constraint is not
  markup, it is **freight at a median 73% of landed cost** and roughly fixed
  per parcel, which makes cheap goods structurally unsellable. Owner has said
  the 50% floor can go; the report proposes a four-tier margin system instead
  (55%+ differentiated, 40 to 50% comparable, 25 to 35% basket, bundle-only).
  At market prices the median margin is 49% and 27 of 36 products clear 25%;
  nine cannot work as singles and two lose money at any market price.
  **Nothing has been repriced yet.** Tracked as #72 to #75.

- **CATALOGUE AUDIT (2026-08-04, web session).** Full pass over all 41 products
  against CJ source data (`docs/qa/cj-variants.json`, regenerate via the
  `cj-variant-audit` workflow by editing `config/audit_spus.json`).
  1. **Five missing lifestyle images added** and verified live: Barnyard
     Squeaker, Woodland Rope-Limb Plush, Crinkle Plush Buddy, Big Squeak
     Plush, Dental Wipes. Each generated from its own studio master and
     eyeballed against it before upload. Owner is checking accuracy
     themselves. The Pet Hair Remover Mitt and Dematting Comb stay
     master-only by owner decision.
  2. **Sizing guides written for all seven size or capacity products** from
     CJ's own charts: bath robe (by dog weight), paw washing cup, snuggle
     blanket, fleece blanket, cooling pad, sofa cover, water bowl. Copy lives
     in `config/sizing_copy.py`, applied via Admin GraphQL.
  3. **Two real copy errors fixed.** The fleece blanket's M size was listed as
     100 x 75cm when CJ says 76 x 104cm, and the sofa cover claimed its range
     reached "a full three-seater" when the largest stocked size is 39 x 57in.
  4. **Dimensions added** to the dental duck, squirrel plush, cuddle teddy,
     LED nail clippers and travel bottle. Deliberately NOT added elsewhere:
     CJ's per-variant numbers are package dimensions, and for soft goods those
     are not product dimensions. Do not treat them as such.
  5. **Variant gaps found, nothing added.** See
     `docs/qa/variant-audit-2026-08.md`. Four products are missing real sizes
     (sofa cover, snuggle blanket, fleece blanket, cooling pad) and the sofa
     cover's Small/Medium/Large are actually CJ's XS/S/M of seven. Adding any
     of them needs CJ pairing in the browser plus a margin-floor check, so it
     is owner-gated. Tracked as #67.
- (Web session, 2026-08-04) Confirmed live Shopify access works from
  claude.ai/code via the Shopify connector; capabilities section below
  rewritten to match. Added `config/fetch_cj_refs.py` + the `cj-image-refs`
  dispatch workflow so credential-less sessions can pull CJ reference images.
  Ran that workflow for the Wagvive Dematting Comb (SPU CJYD2754094; note the
  CJ query endpoint wants the SPU, not the variant SKU): our
  `master-dematting.png` matches CJ's photos feature for feature (handle,
  collar, thumb shield, tooth count and serration) — the master is ACCURATE and
  stays. Only nit: the axle's hex nut is subtler in our shot than in CJ's.
  References live in `docs/qa/dematting/`.
- The comb's LIFESTYLE image FAILED QA (owner spotted it; a 4-pass review, one
  adversarial, confirmed the tool head was invented — a closed hoop instead of
  the real open rake). Six Runway regeneration rounds across nano-banana-pro,
  nano-banana-2 and seedream-5 each fixed the named flaw and broke something
  else on the head; the version that briefly shipped was pulled because the
  axle bar did not line up with the handle. **OUTCOME: the lifestyle image is
  REMOVED. The product page now carries only the studio master** (media
  47588547887393, still featured; verified in Admin and on the live
  storefront). Owner will revisit creating one another time — everything
  needed is in `docs/qa/dematting/` with a README: CJ ground truth, the two
  failed images, the best attempt (`best-attempt-v6.png`, correct
  collinearity), and the prompt description of the real tool. Tracked as #65.
  The other 40 products' lifestyle images have NOT been audited — tracked as
  #66, and the more important of the two, since this one was live since launch.
- CJ's stock-writing disabled store-wide via the authorization page's Sync
  Settings → "Not Sync" (see docs/knowledge/cj-inventory-sync-model.md, "kill
  switch"). `sync_inventory.py` is now the ONLY inventory writer. Verified: 144
  variants, zero double-counts, zero out-of-stock, CJ↔Shopify parity exact.
- Archived duplicate product "Wagvive Sneaker Squeaky Toy" (same CJ SPU as
  Sneaker Chew Buddy, and its colour names were wrong). New audit rule: check
  for duplicate source SKUs (`sku[:11]`), not just titles.

## Open tasks, in priority order

This table is the index. **The instructions are in
`docs/pc-implementation-plan-2026-08.md`**, which orders these into eleven steps
with the data and the sequencing traps. Do not work from this table alone.

| # | Task | Status / notes |
|---|---|---|
| 59 | GA4 + Meta pixel | NEXT UP, but owner-gated: needs a GA4 measurement ID (G-XXXX) and a Meta pixel ID from the owner's own accounts. Once those exist Claude installs both. Store has zero analytics; blocks #62 and any ad spend. |
| 76 | **Rebuild the Dog Enrichment Kit** | NEW 2026-08-04, URGENT, the only live loss-maker of its size. **Sequencing: the $52.99 is 20% off the RECOMMENDED singles, which are not live yet. Against today's prices it reads as 43.6% off and would cannibalise the singles. Either do #74 first, or recompute the kit price against whatever the singles actually are.** It is live at $98 and returns **24.1%**; it needs $137.38 to clear 45%. The Anti-Spill Floating Water Bowl is 1,833g of the kit's 2,429g and takes freight to $45.42, so consolidation saves only $2.71. Replace with Slow Feeder Bowl + Lick Bowl with Ball + Talk Button + Sneaker Chew Buddy at **$52.99** for 47.0%, quoted live at CJ. Full working in `docs/shipping-and-sourcing-study-2026-08.md` section 5. |
| 77 | **Fix or withdraw the Dental & Ear Wipes** | NEW 2026-08-04, URGENT. Live at $22.00 with a delivered floor of $18.38 against a $13.99 market: -10.7% at market. It was healthy in July and broke because CJ's liquid-carrier freight went from $7.88 to $12.38 in a month. Options, in order: **swap to CJ SPU CJYD2449710** ("Cat Dog Ear Teeth Cleaning Finger Stall", $0.48 at 90g against the incumbent's 354g, **46.9% at the market ceiling**, listed by 18 sellers, and it pairs with the Finger Toothbrush we already sell); or a smaller pack of the same product; or withdraw. Do NOT go to larger counts, see #70. Do not leave it at $22.00. |
| 78 | **Recompute the slicker brush and paw trimmer prices** | NEW 2026-08-04, blocks #74. Both were costed against a CJ freight quote of exactly $3.00 from a single carrier, which is a placeholder, not a price. `config/freight_floor.py` now rejects it. Corrected: brush $5.37 estimated and still 43.4% at market, so the pricing study's "re-source or drop" verdict is void; trimmer $6.34 estimated and 35.1%. Their rows in `docs/qa/pricing-recommendations.json` are wrong. |
| 79 | **Add a free-shipping progress bar** | NEW 2026-08-04, highest effort-to-return item in the study. Freight is $4.43 fixed plus $11.90/kg, so an item a customer adds to reach the $60 threshold costs $1 to $3 to ship and sells for $12 to $22. Benchmarks put the bar at an 8 to 14% conversion lift on top of the free-shipping effect. Keep the $60 threshold: it sits inside the $55 to $110 pet AOV band, above every single item and below every kit. |
| 80 | **Launch the Calm & Comfort Kit** | NEW 2026-08-04. Heartbeat Sloth + Calming Thunder Wrap + Cooling Comfort Pad at **$85.99** for 51.3% and $44.10 of contribution, more than any existing kit. Four of our highest-contribution products are currently in no kit at all. Do NOT add the Waterproof Snuggle Blanket: quoted with it in, freight goes to $32.15 and margin to 33.6%. |
| 82 | **Fix the stale free-shipping constant in `shipping_rates.py`** | NEW 2026-08-04, small but a live hazard. The script's `FREE_THRESHOLD = 50.00` and its docstring both say $50, while the store is actually set to free over **$60** and the site copy says $60. Running `config/shipping_rates.py --apply` today would silently move the threshold back to $50 and give away $5.95 on every order between $50 and $60. Update the constant and the docstring; do not run it with --apply until then. |
| 81 | **Swap two products for better-economics equivalents** | NEW 2026-08-04. Squirrel Squeaky Plush (12.6% at market) to CJ SPU CJPT2915091, 70g against 112g, giving 39.6%. Lick Bowl with Ball (19.6%) to the silicone feeding mat CJYD2951433, $0.86 of goods against $5.00, giving 54.6%. Same pairing mechanics as #67; eyeball the images against the CJ reference and check `sku[:11]` for duplicates first. |
| 73 | **Replace the 50% floor with the tier system** | NEW 2026-08-04. Owner has approved dropping the flat floor. Tiers proposed in `docs/pricing-study-2026-08.md` section 2. Repoint `config/margin_guard.py` at a per-product tier table rather than one global number. Do this BEFORE repricing. |
| 74 | **Apply the price changes** | NEW 2026-08-04, blocked by #73. Per-product recommendations in `docs/qa/pricing-recommendations.json`. Catalogue price sum falls about 23%. Standardise `.99` endings at the same time; keep `.00` for kits only. |
| 75 | **Drop the two products that cannot be fixed** | REVISED 2026-08-04. Was "nine non-viable"; scored on DELIVERED price rather than item price, 30 of 36 products clear 15% at market and only six fail. Drop the **Crinkle Plush Buddy** (-29.5%, and the cheapest thing in CJ's plush category still lands above its $8 ceiling, so no supplier can fix it) and the **Anti-Spill Floating Water Bowl** (-8.4% as a single and the thing that broke the Enrichment kit). The other four failures are the wipes (#77), the snuggle blanket and the sofa cover (both heavy, need a US-warehouse source, see the study section 8) and the squirrel plush (#81). The five "bundle only" toys all clear 15% as singles on corrected freight. |
| 71 | **Fix four dashes and the wrong care text on every product page** | NEW 2026-08-04, OWNER ACTION, quick. `templates/product.json` carries two en dashes in the shipping copy, one in a trust badge, one em dash in returns, and a "Care & use" block telling customers to rinse and dry the product before storing, which is wrong for disposable wipes and plush toys and still mentions "older or anxious dogs". Claude CANNOT fix this: live theme writes are refused by policy. Exact find and replace text is in `docs/qa/theme-copy-fixes.md`, about five minutes in the theme editor. Every other theme file was scanned and is clean. |
| 67 | **Add the 41 missing size variants (HOME PC)** | NEW 2026-08-04. Four products are missing sizes CJ actually sells. **Exact SKU list with CJ costs is in the appendix of `docs/qa/variant-audit-2026-08.md`** so pairing is mechanical: sofa cover 12, snuggle blanket 9, fleece blanket 12, cooling pad 8. Sequence: (1) owner pairs each SKU in the CJ browser app, one product at a time, verifying `matchitem.shopType === 'Shopify'` before confirming; (2) Claude resolves freight via `freight_floor.py` and prices each size to clear its **tier** floor (#73, not the retired 50% floor), levelling colours as usual; (3) Claude creates the Shopify variants and wires variant images. Freight, not product cost, will decide whether the biggest sizes are viable, so expect some to fail the floor and be dropped. Freight is $4.43 fixed plus $11.90/kg, and the sofa cover is already 1,340g at Medium, so Large is the one to watch. |
| 67a | Rename the sofa cover's size labels | Depends on #67. Our Small/Medium/Large are CJ's XS/S/M of seven sizes, so the labels stop making sense the moment bigger sizes are added. Rename to the true range at the same time. Renaming option values rewrites variant titles, so do it in one pass with the additions, not before. |
| 68 | Decide on lifestyle images for the five kits | NEW 2026-08-04. All five kits (New Puppy, Toy, Grooming Essentials, Enrichment, Travel) have a cover plus component shots and no in-use photo. That looked deliberate so nothing was changed. If you want them, the components are already shot and a kit scene is straightforward. |
| 69 | Real product dimensions for the remaining products | NEW 2026-08-04. Dimensions were added only where CJ states them explicitly. For most toys CJ publishes package dimensions only, which for soft goods are not product dimensions, so nothing was stated. To finish this properly, either measure samples on arrival or ask CJ for product dimensions per SKU. Do NOT infer from `variantLength/Width/Height`. |
| 70 | ~~Consider larger wipe counts~~ | CLOSED 2026-08-04, researched and rejected. Freight is $4.43 fixed plus $11.90/kg, so every extra wipe is pure weight and larger counts make the economics worse, not better. The 50-count tub at 354g is already why this product fails: $12.38 of freight against a $13.99 market. The move is SMALLER, not larger. See #77 and the study section 6. |
| 66 | Audit ALL lifestyle images against CJ references | PARTLY DONE 2026-08-04: every product now HAS a lifestyle image except the two the owner excluded, and all descriptions were checked for sizing accuracy. Still outstanding: confirming each existing lifestyle image actually depicts the right product, which the owner is doing themselves. Fully unblocked — no owner action, tooling already built (`cj-image-refs` workflow + `config/fetch_cj_refs.py`). The dematting comb's "in use" photo depicted a tool that does not exist and had been live since launch; the rest of the catalogue has never been checked the same way. Misleading imagery drives returns and chargebacks, so do this BEFORE paying for traffic. Method and failure patterns: `docs/qa/dematting/README.md`. |
| 63 | Post-purchase reviews | Biggest untouched conversion lever. Judge.me free tier or similar; needs app install (owner clicks, Claude configures). |
| 57 | NY sales tax registration | OWNER ACTION: file DTF-17 at NY Business Express (needs SSN/EIN). Then Claude adds the Certificate of Authority number in Shopify tax settings. |
| 64 | DDP/DDU confirmation with CJ | Owner raises a CJ ticket (order-gated; order #1001 exists now). Margin model assumes duties included — DDU would mean surprise customer charges. |
| 60 | TikTok Shop | RESEARCHED 2026-08-04 and the answer is mostly no. Median pet price there is $15.53 and 69% sell under $20, while all-in costs run 35 to 55% of revenue (referral + affiliate + Shop Ads). Most of the catalogue cannot be profitable there at any price. Only credible candidates are the four high-contribution items (nail grinder, thunder wrap, heartbeat sloth, sofa cover) and kits. Do not open catalogue-wide. |
| 61 | Short-form video for social-first products | Runway videos for screaming chicken, talk button, paw washing cup, LED clippers. |
| 65 | Recreate the dematting comb lifestyle image | Deferred by owner 2026-08-04 after six failed regeneration rounds. Product page currently ships master-only, which is accurate, so this is cosmetic not urgent. Start from `docs/qa/dematting/best-attempt-v6.png` (handle/axle collinearity already correct). Prompting alone has not worked — consider compositing the master's tool into a scene, or a photographed sample, before burning more Runway credits. |
| 62 | Ad-spend guardrails | Blocked on #59. |

## Device capabilities — what works where

**Any device (claude.ai/code on the repo):** planning, research, copy, code,
email templates, audits of committed state, editing the Actions workflow.
**Live Shopify edits work from web sessions too** when the Shopify MCP
connector is attached (verified 2026-08-04): products, collections, inventory,
orders, discounts, plus arbitrary Admin GraphQL reads/writes. A Runway
connector is typically attached as well. What web sessions still CANNOT do:
run the repo's Python scripts live (`config/*.env` are gitignored and exist
only on the PC; the sandbox's network policy also blocks direct calls to
Shopify/CJ domains — only the connectors get through), and anything CJ-side.
For CJ API reads without credentials, dispatch the `cj-image-refs` workflow
(fetches a product's record + images and commits them to the branch), or
route work through the Actions job. Pricing changes should still be computed
against `config/pricing.py` logic before any write.

### Prompt to start the PC session

Paste this. It deliberately points at one document rather than restating it, so
there is only ever one source of truth for the plan.

> Read `docs/HANDOFF.md`, then `git pull`, then read
> `docs/pc-implementation-plan-2026-08.md` in full. That plan is the work for
> this session. Start at step 1 and go in order.
>
> Rules for the whole session:
> - Show me the numbers BEFORE any write, and wait for my approval on anything
>   that changes a price, a product or a bundle.
> - Re-quote freight through `config/research_kits.py` or
>   `config/freight_floor.py` rather than trusting the figures in the plan. They
>   were measured on 2026-08-04 and freight moved 57% on one product in a month.
> - Verify every change against the live system by re-fetching it, not against
>   the tool's return value.
> - For anything needing the CJ browser app, tell me exactly which SKUs to pair
>   and wait for me to confirm each product before continuing.
> - Tell me plainly if something in the plan turns out to be wrong.
> - Never enter my credentials anywhere. Logins, payment details, tax filings
>   and supplier account registrations are mine to do. Flag and hand off.
>
> Before you start, tell me in one list everything you will need FROM me across
> the whole session, so I can gather it once instead of being interrupted: which
> CJ SKUs to pair, the GA4 measurement ID and Meta pixel ID (#59), and whether I
> want you to prepare anything for #57 (NY tax filing) or #64 (the CJ duty
> ticket).
>
> When the writes are done, run `config/margin_guard.py`,
> `config/kit_margins.py` and `config/sync_inventory.py --apply`, check the
> affected pages on the live storefront, then update `docs/HANDOFF.md`, commit
> and push.

**The full queue, with reasoning and data, is
`docs/pc-implementation-plan-2026-08.md`.** In one line each:

| Step | What | Task # |
|---|---|---|
| 1 | Rebuild the Dog Enrichment Kit, live at 24.1% | #76 |
| 2 | Fix or withdraw the Dental & Ear Wipes, live above its ceiling | #77 |
| 3 | Recompute the slicker brush and paw trimmer on real freight | #78 |
| 4 | Replace the 50% floor with the tier table | #73 |
| 5 | Apply the price changes | #74 |
| 6 | Drop two products, swap two others | #75, #81 |
| 7 | Free-shipping progress bar, and fix the stale threshold constant | #79, #82 |
| 8 | Launch the Calm & Comfort Kit | #80 |
| 9 | Theme copy fixes, owner action, about 5 minutes | #71 |
| 10 | The 41 missing size variants | #67, #67a |
| 11 | Reviews | #63 |

Steps 1 and 2 are losing money today. Step 3 must precede step 5, and step 4
must precede step 5. **Owner actions that do not need the PC and have been
waiting**: #57 (NY tax filing) and #64 (the CJ duty ticket, which is worth 20%
of product cost on every order).

**Home PC only:** CJ UI work (pairing, sync settings — no API exists),
theme editor work (Claude's live theme writes are refused by policy),
Shopify admin settings screens (do not render in background tabs), visual
storefront QA in the user's logged-in Chrome, and anything needing
`config/shopify.env` / `config/cj.env` which live only there.

## Standing rules (full set in CLAUDE.md — binding)

50% margin floor after all costs · never enter the owner's credentials ·
confirm before spending money or irreversible actions · hello@wagvive.com is
the only customer-facing email · no em-dashes or hyphenated ranges in store
copy · verify against the live system, never trust a write's return value.

## How to hand off

Before ending a session or switching devices:
1. Update this file (state, open tasks, what changed, anything in flight).
2. Commit and push everything.
3. Tell the user the handoff is committed.

On this session's device (home PC) the prior chat history also survives
locally — but treat THIS FILE as the source of truth for state, because other
devices may have moved things since.
