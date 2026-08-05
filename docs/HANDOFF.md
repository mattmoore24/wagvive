# Session handoff — read this first on any device

> Protocol: every Claude session starts by reading this file, and updates it
> (plus commits and pushes) before the user switches devices or ends a work
> session. This file IS the conversation continuity between devices.

**Last updated:** 2026-08-05, from the home PC session (repricing, compliance review, marketing plan)

---

# START HERE

Two things define the current state. Read both before doing anything.

### A. Marketing is the active project → `docs/marketing-plan-2026-08.md`

The store is repriced, compliant and instrumented-ready, and the next work is
customer acquisition. The plan is built backwards from our own unit economics
and its single most important conclusion is:

**Never advertise a single product. Kits only.** Average single-product
contribution is $4.71, which needs a 19% conversion rate to break even on a
$0.90 Meta click. Kits run $16.76 to $43.06 of contribution. At a realistic
new-store 1% conversion rate our best offer supports a **$0.43 click**, which
rules out Google Search ($3.00) and makes Meta marginal. Pinterest ($0.35) is
the only channel affordable on day one. Run
`python config/marketing/cac_ceiling.py` for the live table, and re-run it
after ANY repricing because every ceiling moves.

**TikTok Shop is closed as not viable** (task #60): it restricts overseas
direct shipping, demands delivery inside about 6 business days against our 5 to
12, and takes about 30% all-in. TikTok as an ads/organic channel to our own
site is still open.

Current state: **1 order (the test), no GA4, no pixels, no Merchant Center.**
Phase 0 of the plan is installing the measurement stack, and nothing paid
happens before it is verified (tasks #75, #76, #77).

### B. The 2026-08-04 repricing is DONE. The store runs on the price book.

The whole catalogue was repriced on 2026-08-04 from a per-product demand model,
and all six kits were rebuilt around freight physics. Everything is applied,
verified live, and green. What a new session must know:

1. **`config/price_book.json` is the source of truth** for all 144 single
   variant prices AND each product's `floor_margin_pct`, which
   `margin_guard.py` now enforces per product. **The flat 50% floor is
   retired** (owner decision). Floors are denominated in the guard's own cost
   model (selected carrier + tax-inclusive fee) minus an 8pt drift buffer;
   recalibrate with `config/calibrate_floors.py --apply` after any deliberate
   repricing, or the guard false-alarms on model mismatch.
2. **The pricing pipeline**, if prices ever need rebuilding:
   `market_bands.py` (observed low/mid/high per product) → `demand_model.py`
   (logistic share-of-consideration) → `optimise_prices.py` (contribution
   maximiser, capped at the competitive ceiling) → `build_price_book.py`
   (per-variant book) → `apply_price_book.py --apply` (write + verify).
3. **Kits:** `optimise_kits.py` enumerates on-theme candidates on the fitted
   freight curve, but winners MUST be re-ranked on LIVE combined CJ basket
   quotes before applying: carrier-eligibility rules are invisible to the
   curve (any basket holding the Talk Button gets forced onto sensitive
   lines, nearly +$25 on a 5-item kit). `apply_kits.py --apply` writes
   compositions, bodies, flat prices and compare_at.
   **`productBundleUpdate` DOES swap components** - the older note in
   `rebuild_kits.py` saying composition changes need a rebuild is wrong.
4. **The old runbook (`docs/pc-implementation-plan-2026-08.md`) is history.**
   Its steps 1/2/6 were based on costs taken from CJ MULTIPACK variants we do
   not sell (water bowl "3pcs" 1833g vs our 620g single) and were voided;
   `config/validate_research.py` now catches that bug class. The same trap
   applies to freight baskets: quote vids from OUR skus only.
5. **CJ keyword search is useless for sourcing** (`/product/list` returns
   newest-first, listedNum ≈ 0 everywhere). Finding proven products needs the
   CJ trending UI in a browser, not the API.

### All research, and what each file is for

**Current, authoritative:**

| File | Use it for |
|---|---|
| `docs/marketing-plan-2026-08.md` | **The active plan.** Channel verdicts, phases, budgets, decision rules. |
| `docs/pricing-and-kit-analysis-2026-08.md` | Why every price and kit is what it is. Method, market bands, demand model, full result tables, and what was tried and rejected. |
| `docs/legal-compliance-review-2026-08.md` | What was fixed, what the owner must decide, what does not apply yet but will. |
| `config/price_book.json` | Machine-readable source of truth for all 144 variant prices and per-product guard floors. |
| `docs/qa/recost-2026-08-04.json` | Cost, weight, freight and carrier snapshot behind the repricing. |
| `docs/qa/cj-connection-audit-*.json` | Latest CJ connection audit result. |
| `docs/knowledge/` | Durable how-it-works notes, e.g. the CJ inventory sync model. |

**Superseded, keep for reference only:**

| File | Status |
|---|---|
| `docs/pc-implementation-plan-2026-08.md` | **VOIDED.** Steps 1/2/6 were costed against CJ multipack variants we do not sell. Do not work from it. |
| `docs/pricing-study-2026-08.md` | Superseded by `pricing-and-kit-analysis-2026-08.md`. Its market figures often captured the premium brand rather than the volume seller. |
| `docs/qa/pricing-recommendations.json` | Superseded by `config/price_book.json`. |
| `docs/qa/delivered-price.json`, `docs/qa/kit-designs.json` | Superseded by the 2026-08-04 re-cost and the live kit re-quotes. |
| `docs/shipping-and-sourcing-study-2026-08.md` | Freight physics and the supplier verdict still hold. Its per-product figures do not. |

Tooling built for this work, all read-only against CJ and runnable from the PC:

| Script | Does |
|---|---|
| `config/research_freight.py` | Measures CJ freight end to end. Runs in Actions via `cj-freight-research.yml`. |
| `config/research_kits.py` | Ranks on-theme kit combinations, then quotes the leaders live. Triggered by touching `config/kit_run.json`. |
| `config/delivered_price.py` | Offline. Scores every product on delivered price. No CJ calls. |
| `config/freight_floor.py` | The one place that decides what freight to trust. Now rejects placeholder quotes as well as zeros. |

---

## Where the business stands

wagvive.com is LIVE and fully operational: 42 active products (36 singles + 6
variant-selectable bundle kits), all CJ-paired. **Every variant clears its
price-book floor** (margin_guard green, per-product floors) and **every kit
clears 30% on live CJ basket quotes**: Puppy 56.5%, Toy 51.0%, Grooming 42.3%,
Travel 41.6%, Calm & Comfort 39.3%, Enrichment 36.2%. First real order (#1001)
completed the full loop: checkout → CJ →
paid → shipped → tracking back → branded emails from hello@wagvive.com.
Storefront password is off, SEO/social cards are set, all 18 notification
emails are branded.

Operations run themselves: GitHub Actions (`scheduled-ops.yml`) syncs CJ stock
into Shopify, repairs inventory locations, and checks margins **every 6 hours**.
A failed run emails the owner — silence means healthy.

## What just happened (most recent work)

- **MARKETING PLAN (2026-08-04).** `docs/marketing-plan-2026-08.md`. Built from
  live contribution figures rather than channel best practice, because at a
  few-hundred-dollar budget the economics rule out most of the best practice.
  Phased: phase 0 is free (instruments, feed, email flows), phase 1 is $150 on
  Pinterest against the Calm & Comfort Kit only, phase 2 is conditional on a
  measured conversion rate, phase 3 gates Google and Meta behind 1.5%
  conversion and 20 orders of history. New runnable tooling in
  `config/marketing/`: `cac_ceiling.py` (the affordability table),
  `feed_health.py` (Merchant Center readiness plus written feed titles for all
  42 products), `utm.py` (link builder that refuses unknown sources so
  attribution stays readable).

- **COMPLIANCE REVIEW (2026-08-04).** `docs/legal-compliance-review-2026-08.md`.
  Found and fixed: the Shipping Policy promised free shipping over $50 while
  checkout charged it over $60 (write_policies.py now refuses to publish on a
  mismatch with shipping_rates.py); Terms of Service had none of the clauses
  that do work (governing law, warranty disclaimer, liability cap, IP, user
  content, indemnity, severability); no written cancellation right for delayed
  orders per FTC 16 CFR 435; **the footer had no links at all** because the
  Footer menu was never wired to a block, so every policy link and the state
  privacy opt-out rendered nowhere. Added /pages/proposition-65 and
  /pages/accessibility, and put FTC endorsement disclosure requirements on the
  Creator programme page. Open owner decisions are in section 3 of that doc,
  the main one being how far to take Proposition 65 compliance.

- **STOREFRONT COPY (2026-08-04).** The homepage FAQ's senior-dog question
  (untrue since the Senior Dog Kit was retired) replaced with a which-kit
  question covering all six. All customer-facing British spellings
  americanized: 23 product option names read "Colour", plus "fulfilment",
  "odour" and "centre" in copy. Source scripts fixed so a rebuild cannot
  reintroduce them.

- **FULL CATALOGUE REPRICING + KIT REBUILD (2026-08-04, PC session).** The
  mega-task is complete and verified live.
  - **Research:** all 36 products re-costed from the SKUs we actually sell
    (`config/reprice_catalogue.py`, snapshot in
    `docs/qa/recost-2026-08-04.json`); live market bands per product from
    retailer research (`config/market_bands.py` documents the premium-brand
    vs volume-seller distinction that had inflated the earlier study); CJ
    listedNum pulled as a demand proxy.
  - **Model:** constant elasticity rejected (it recommends pricing above
    market and never decays); replaced by a logistic share-of-consideration
    curve calibrated on each product's observed band
    (`config/demand_model.py`), with a hard competitive ceiling of mid x1.15
    for outcome goods and mid for everything else.
  - **Applied:** 144 variant prices (headline singles sum $917.86 → ~$615;
    average modelled win rate 24% → 54%), per-size pricing on sized products,
    10 sub-5% variants nudged up by `calibrate_floors.py`. All six kits
    rebuilt IN PLACE via productBundleUpdate with new bodies, covers
    (`make_kit_covers.py`, now dedupes variant-selectable components), flat
    prices, honest compare_at, and `custom.kit` cross-links re-pointed
    (22 components). **Calm & Comfort Kit is NEW** (id 10477056491809,
    $109: Sloth + Thunder Wrap + Fleece + Cooling Pad XXL + Big Squeak).
  - **Guards repointed:** margin_guard enforces price-book floors;
    kit_margins enforces 30%; both green. `shipping_rates.py` constant
    synced to the live $60 threshold (#82). Storefront spot-checked via
    public product JSON: all kit and sample single prices correct,
    available, with images.
  - **Sourcing scan (#68):** no new product added; CJ API search surfaces
    only fresh zero-demand listings. Shortlisting proven fillers needs the
    CJ trending UI.

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

## Open work, in priority order

> **Task-number warning.** An earlier version of this file used numbers #73 to
> #82 for the pricing queue. Those are all DONE or VOIDED, and the live task
> list has since reused #73 to #77 for different things. **Trust the
> descriptions below, not any number you remember.**

### Next up: marketing phase 0. Free, and it gates everything paid.

| Task | What | Who |
|---|---|---|
| #75 | GA4 property, Meta pixel + Conversions API (data sharing = Maximum), Google Merchant Center with free listings on, Pinterest business account + tag | **Owner creates the accounts**, Claude configures and verifies |
| #75a | Declare "these products have no GTIN" in the Google channel, then apply the 42 feed titles from `config/marketing/feed_health.py --titles` | Claude, once the channel exists |
| #76 | Build the five email flows in Shopify (welcome x3, abandoned checkout x3, browse abandonment, post-purchase + day-21 review request, 60-day winback). Shopify native, NOT Klaviyo, which is unjustified under $500K | Claude drafts, owner approves |
| #77 | `marketing/ads_report.py`, `marketing/ad_guardrail.py`, `marketing/weekly_brief.py`. Build once ad accounts exist; wire into `scheduled-ops.yml` | Claude |

**Gate before any spend:** a real test purchase must appear in GA4, Meta and
Pinterest. Then phase 1 is $150 on Pinterest against the Calm & Comfort Kit
only. Full reasoning in `docs/marketing-plan-2026-08.md`.

### Owner actions that have been waiting and need no device

| Task | What |
|---|---|
| #57 | **NY sales tax registration.** File DTF-17 at NY Business Express (needs SSN or EIN). Then Claude adds the Certificate of Authority number to Shopify tax settings. |
| #64 | **CJ duty ticket.** Confirm DDP vs DDU. The margin model assumes duties are included; DDU would mean surprise charges to customers and a policy we would have to rewrite. Order #1001 exists, so the ticket is no longer order-gated. Worth 20% of product cost on every order. |
| Legal | Three decisions in `docs/legal-compliance-review-2026-08.md` section 3: how far to take Proposition 65, whether to add an arbitration clause, and whether the business is an LLC yet. The entity question is the highest-value one. |

### Still open, lower priority

These have no reliable task number left (the old numbers were reused). Work
from the descriptions.

| What | Notes |
|---|---|
| **Post-purchase reviews** (#63 in the live list) | Biggest untouched conversion lever. Judge.me free tier; owner installs the app, Claude configures. The request email itself is part of the #76 flows. |
| **Short-form video** (#61 in the live list) | Screaming chicken, talk button, paw washing cup, LED clippers. Now has a purpose: it is the creative for Pinterest phase 1. See marketing plan section 6. |
| **Verify lifestyle images against CJ references** | Confirm each existing lifestyle image depicts the right product. Owner was doing this personally. Tooling exists (`cj-image-refs` workflow). Worth finishing BEFORE paying for traffic, since misleading imagery drives returns. |
| **Dematting comb lifestyle image** | Deferred after six failed generation rounds; the page ships master-only, which is accurate. Cosmetic. |
| **The 41 missing size variants** | Sofa cover 12, snuggle blanket 9, fleece blanket 12, cooling pad 8, with CJ costs in `docs/qa/variant-audit-2026-08.md`. Needs CJ browser pairing, so home PC only. Price each size through the price-book pipeline, not the retired flat floor, and rename the sofa cover's size labels in the same pass (ours are CJ's XS/S/M of seven). |
| **Kit lifestyle images** | All six kits have a cover plus component shots, no in-use photo. |
| **Real product dimensions** | CJ publishes package dimensions only for soft goods; do NOT infer from `variantLength/Width/Height`. Needs samples or a CJ request. |

### Closed this session

Repricing and kit rebuild (all 144 variants, six kits), the flat-50% floor
retirement and guard repointing, the CJ connection audit, the legal compliance
review, the homepage FAQ fix, the British-spelling sweep, the marketing plan.
**TikTok Shop (#60) is closed as not viable**, not deferred: the blocker is the
fulfillment model, not effort. See marketing plan section 3.1.

## Device capabilities, corrected 2026-08-04

**Home PC (this device).** Everything. `config/shopify.env` and `config/cj.env`
live only here, so every script in `config/` runs. **Live theme writes DO work
from here** and were used repeatedly this session (`fix_home_faq.py`,
`build_footer.py`, `americanize_colour.py`). An older note in this file claimed
Claude cannot write themes; that was wrong and has been removed. Also the only
device for CJ browser work (pairing, sync settings) and for Shopify admin
settings screens, which do not render in background tabs.

**Any other device (claude.ai/code on the repo).** Planning, research, copy,
code, email templates, audits of committed state, editing the Actions workflow.
Live Shopify edits work when the Shopify MCP connector is attached: products,
collections, inventory, orders, discounts, and arbitrary Admin GraphQL. A
Runway connector is usually attached too.

What a non-PC session CANNOT do: run the repo's Python scripts against live
Shopify or CJ (the `.env` files are gitignored and the sandbox blocks those
domains directly, only connectors get through), and anything CJ-side. For CJ
reads without credentials, dispatch the `cj-image-refs` workflow or route the
work through GitHub Actions.

**Verifying theme changes from anywhere:** the cached homepage HTML served
pre-change renders for over seven minutes after a footer write this session,
alternating between two old versions across edge nodes, and a `?nocache=`
parameter does not help because it is not part of the cache key. Use the
section rendering API instead, which re-renders server side and shows the truth
immediately:
`https://wagvive.com/?sections=sections--27042989867297__footer_m9NzUG`

## Prompt to start the next session

Paste this on whichever device you pick up. It points at documents rather than
restating them, so there is only ever one source of truth.

> Read `docs/HANDOFF.md` first, then `git pull`, then read
> `docs/marketing-plan-2026-08.md` in full. That plan is the active project.
>
> Context: the catalogue was fully repriced on 2026-08-04 from a demand model,
> all six kits were rebuilt around freight physics, a legal compliance review
> was completed, and a marketing plan was written. Everything is applied,
> verified live and pushed. The store has ONE order (a test), no GA4, no
> pixels, and no Merchant Center, so marketing phase 0 is next and it is the
> gate on all paid spend.
>
> Start by telling me:
> 1. What you can and cannot do on THIS device (check whether the Shopify
>    connector is attached before assuming).
> 2. Everything you need FROM me across the whole session, as one list, so I
>    can gather it in one go rather than being interrupted. I expect that to
>    include the Google, Meta and Pinterest account setups.
> 3. Which parts of phase 0 you can do right now without any account of mine,
>    and start on the highest-value one.
>
> Rules for the session:
> - Never advertise a single product. Kits only. The reason is in the plan
>   section 1 and it is not a preference, it is arithmetic.
> - Re-run `config/marketing/cac_ceiling.py` before any budget decision, and
>   after any repricing, because every ceiling moves with prices.
> - Verify every change against the live system by re-fetching it, not against
>   the tool's return value. For theme changes use the section rendering API,
>   not the cached homepage.
> - Show me numbers before any write that changes a price, product or bundle.
> - Never enter my credentials anywhere. Logins, payment details, tax filings
>   and supplier registrations are mine to do. Prepare everything up to the
>   login and hand off with exact steps.
> - Tell me plainly if something in the plan turns out to be wrong.
>
> When you finish, update `docs/HANDOFF.md`, commit and push.

## Standing rules (full set in CLAUDE.md, binding)

Per-product price-book floors, NOT the retired flat 50% (`margin_guard.py`
enforces `floor_margin_pct`; kits floor at 30%) · never enter the owner's
credentials · confirm before spending money or irreversible actions ·
hello@wagvive.com is the only customer-facing email · US spelling, no em dashes
and no hyphenated day ranges in store copy ("5 to 12 business days") · verify
against the live system by re-fetching, never trust a write's return value ·
never advertise a single product, kits only.

## How to hand off

Before ending a session or switching devices:
1. Update this file: state, open work, what changed, anything in flight.
2. Commit and push everything.
3. Tell the user the handoff is committed.

Treat THIS FILE as the source of truth for state, because another device may
have moved things since your local chat history was written.
