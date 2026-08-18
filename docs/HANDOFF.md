# Session handoff — read this first on any device

> Protocol: every Claude session starts by reading this file, and updates it
> (plus commits and pushes) before the user switches devices or ends a work
> session. This file IS the conversation continuity between devices.

**Last updated:** 2026-08-18, home PC (fall/viral pricing fully done: 6 prices cut, all 10 in price_book.json with real floors, size guides live, fall lineup COMPLETE)

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

Current state: **1 order (the test). The measurement stack EXISTS (verified
2026-08-08, superseding the older "no pixels" note):** all three channel
pixels are registered on the storefront through Shopify's web-pixels-manager
(they do NOT appear as classic script tags, so grep for the config, not for
gtag/fbq):

- **GA4** via Google & YouTube channel: measurement id `G-W6EC4B37P0`, tag
  `GT-WPLLWG52`, events wired including search and begin_checkout
- **Meta** pixel `1770353747621287`
- **Pinterest** tag `2612708372364`

Product feeds: every active product is published to Google & YouTube,
Facebook & Instagram and Pinterest. **One structural limit found: Shopify's
Pinterest channel REJECTS bundle products** ("Channel Pinterest does not
support bundle products"), so the six kits cannot enter the Pinterest
catalogue; their components all can and do. Phase 1's promoted pins linking to
the kit page still work; Pinterest CATALOGUE/shopping ads for kits are
impossible. What remains of phase 0 is the gate itself: a real test purchase
visible in all three tools (#75), plus the email automations (#76a).

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
| `docs/marketing/email-flows-2026-08.md` | All five flows, paste-ready, plus the WELCOME10 record and the flow 2 build guide. |
| `docs/marketing/landing-page-audit-2026-08.md` | Pre-spend audit of the Calm & Comfort Kit page, the phase 1 destination. |
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

- **ALL 10 FALL/VIRAL PRODUCTS REPRICED AND FULLY IN `price_book.json`
  (2026-08-18).** None of the 10 fall-lineup/viral-launch products were ever
  really in the book — they launched priced against cost alone (margins came
  out 40-53%, roughly triple the catalogue median) and were never checked
  against what a real competitor charges. Live market research (Walmart
  marketplace, the unbranded/volume-seller comparison this store needs,
  matching `market_bands.py`'s own methodology) found 6 were priced well above
  their category and cut them to the market low (or the price needed to clear
  25% margin, whichever binds), all `.99`-rounded UP so nothing crosses the
  floor:

  | Product | Was | Now |
  |---|---:|---:|
  | 3-in-1 Steam Grooming Brush | $26.99 | $16.99 |
  | Glow Skeleton Suit | $24.99 | $15.99 |
  | Pumpkin Hoodie | $21.99 | $15.99 |
  | Roast Turkey Sniff Toy | $22.99 | $17.99 |
  | Jack-o-Lantern Sweater | $17.99 | $12.99 |
  | Thanksgiving Turkey Sweater | $19.99 | $15.99 |

  Held at current price: **Big Dog Costume** and **Pumpkin Snuffle Mat** are
  already at/under their direct market comps; **Pumpkin Chew Toy** is already
  at its margin floor; **Ball Launcher** ($94.99) is held deliberately despite
  the formula saying $91.99 — its freight comes from a CJ $0.00 domestic quote
  falling back to an $11 flat estimate calibrated on a 450g reference item, and
  this SKU is 1800g. A different call pattern elsewhere in the repo would price
  the same $0 quote at $26.20, which would put TODAY's price at ~11% margin,
  not 27.6%. Do not cut this one until real freight is confirmed against an
  actual order. Task flagged: `task_6d9443f0`.

  All 6 cuts verified correct three ways (direct per-variant Admin API reads,
  storefront `.js`, and a repeat pass). Script:
  `config/reprice_fall_lineup.py` (dry-run by default).

  **All 10 are now correctly in `price_book.json` with real calibrated
  floors**, each replacing the 25% `DEFAULT_FLOOR` they'd been silently
  running on:

  | Product | floor_margin_pct |
  |---|---:|
  | Glow Skeleton Suit | 19.8% |
  | Jack-o-Lantern Sweater | 17.7% |
  | Thanksgiving Turkey Sweater | 17.4% |
  | Steam Grooming Brush | 19.9% |
  | Ball Launcher | 19.6% |
  | Pumpkin Hoodie | 21.3% |
  | Big Dog Costume | 36.7% |
  | Pumpkin Snuffle Mat | 35.8% |
  | Roast Turkey Sniff Toy | 17.8% |
  | Pumpkin Chew Toy | 18.6% |

  Getting there took CJ's daily API points quota running out mid-session — not
  a code problem, a real budget CJ enforces separately from its documented
  1 req/sec throttle, and this session's pricing sweeps plus the quota's own
  natural drain from the 6-hourly scheduled job emptied it. `config/
  book_fall_lineup.py` was made RESUMABLE so each retry banks whatever it
  resolves before hitting the wall again rather than discarding it, and it
  took four short runs, spaced a few minutes apart, to get all ten booked.
  Full finding, including a real risk this poses to the next scheduled
  6-hourly job if the quota is down when it fires, in
  `docs/knowledge/cj-api-points-quota.md`.

  That investigation also surfaced a genuine 8-month-old bug: `add_fall_lineup
  .py` and `add_fall_wave2.py` had been writing floor entries keyed by product
  HANDLE instead of numeric ID, which every reader (`margin_guard.py`,
  `calibrate_floors.py`) looks up by ID — so all ten fall/wave2 products had
  been silently running on `DEFAULT_FLOOR` since launch despite the code
  visibly "setting" a floor each time. Fixed in both scripts for future
  launches; the ten dead stub entries were removed from `price_book.json`
  once the real ones existed to replace them.

  One more unrelated thing found and fixed along the way: Shopify's Admin API
  `products.json?handle=X` list endpoint served a stale embedded `variants`
  array for several minutes after a fully-successful write, which looked
  exactly like a partial price-cut failure and was not one
  (`docs/knowledge/shopify-liquid-and-cdn-traps.md`, trap 4).

  Still flagged as background tasks, not yet done: hardening `cj_api.call()`
  itself to detect quota exhaustion once rather than per-caller
  (`task_ffc85935`), and the freight-model uncertainty behind the held Ball
  Launcher price (`task_6d9443f0`).

- **FALL COLLECTION IS SEASONAL ONLY AGAIN (2026-08-18).** The Automatic Ball
  Launcher and the 3-in-1 Steam Grooming Brush were sitting in
  `fall-halloween`. They came from the separate "viral products" brief, and
  both `add_fall_lineup.py` and `add_fall_wave2.py` added every product they
  created to the seasonal collection unconditionally. Neither carries a `fall`
  or `seasonal` tag, which is the tell.

  This was costing money, not just tidiness: the homepage "Dressed for fall"
  row is a `product-list` bound to that collection with `max_products: 8`, so
  two year round products were taking two of the eight slots from the costumes
  in the weeks they have to sell in. Removed with
  `config/fix_fall_membership.py`, which refuses to remove a product that is
  not already in another collection. The launcher keeps `toys-play` (smart,
  rule tag=toy), the brush keeps `grooming`. Both verified buyable and listed
  on the live storefront.

  Also normalised `product_type`: 4 products used `Toys` against 15 using
  `Toys & Play`, all four from the fall batch. Nothing reads product_type
  except the kit filters, which match `Bundles & Kits`. Two ARCHIVED products
  (Halloween Squeaky Bones, Halloween Snuffle Mat) are still collects on the
  fall collection; they do not render and were left alone.

  `audit_fall_imagery.py` was scoped to the collection, so the two moved
  products silently fell out of the gate. It now names them in `ALSO_CHECK`:
  collection membership is a marketing decision and the wrong thing to hang an
  imagery check on. Back to 11 products, 27 images, 0 CJ.

- **SIZE GUIDES ON ALL 15 SIZE PRODUCTS, AND A 2x SIZING ERROR FIXED
  (2026-08-18).** Every product with a Size option now carries a per-size table
  of real dog measurements. Nine had nothing at all, including every costume
  and jumper. `config/apply_size_guides.py` writes them,
  `config/audit_size_guides.py` is the standing gate, and all 15 verified on
  the storefront, not on the write's return value.

  **The Quick-Dry Bath Robe was telling customers the wrong size.** Its old
  table said XS fits a 9 to 16 lb dog and named the Chihuahua. The maker's
  chart says XS is 8 to 15 **kg**, which is 18 to 33 lb: someone read an
  unlabelled weight column as pounds and converted it again, halving every row.
  The chest column proves it (XS is graded for a 45 to 55 cm chest, a Chihuahua
  is about 35 cm). Anyone who bought by that table got a robe about two sizes
  too big. Corrected, and the Grooming and Travel kits inherit the fix because
  their Size drives the robe.

  Why it went unnoticed: **CJ hides its size charts in `<img>` tags inside the
  product `description` HTML.** They are not in the API, not in
  `productImageSet`, and `variantLength/Width/Height` are the postage carton
  (the hoodie reports the same 300x200x30mm for XS and 9XL). Every earlier
  script stripped the description to plain text first and so threw the charts
  away. Full write-up, including the Jack-o-Lantern label offset and the
  Skeleton Suit's stretch contradiction, in
  `docs/knowledge/cj-size-charts.md`.

- **HOUSE ART DONE ON ALL 10 FALL PRODUCTS (2026-08-18).** Every one now LEADS
  with a cream #F7F2E9 studio shot, and 116 of 126 variants point at their own
  art. Scripts: `apply_fall_art.py` (upload + wire) then `promote_fall_art.py`
  (make it position 1).

  Multi-look products were shot as ONE master and recoloured so pose, framing,
  lighting and shadow stay locked: Pumpkin Hoodie 5 colours, Big Dog Costume
  Tiger/Rabbit/Dinosaur, Turkey Sweater Turkey/Boo/Plaid, Jack-o-Lantern Sweater
  Orange Stripe/Orange Pumpkin. Singles: Skeleton Suit, Ball Launcher, Snuffle
  Mat, Roast Turkey, Pumpkin Chew, Steam Brush.

  Both text-bearing garments reproduced faithfully rather than avoided: the
  embroidered "Happy Thanksgiving" and the "BOO" with its purple witch hat. Text
  on the REAL product is described precisely; supplier marketing text burnt into
  a CJ photo (the Steam Brush's "Daily cleaning kit") is banned explicitly.

  **RESOLVED: the 10 unphotographed sweater variants are gone.** The
  Jack-o-Lantern Sweater sold four colourways while CJ photographs only two.
  "Black Embroidered" and "Black Jacquard" had NO reference image in any of CJ's
  nine photos, so they fell back to the Orange Stripe photo, meaning a customer
  picking Black Jacquard saw an orange striped sweater. Owner approved removal
  and `config/drop_unphotographed_colorways.py` deleted those 10 variants. The
  sweater now sells 10 variants across Orange Stripe and Orange Pumpkin, every
  one with its own photograph. The script refuses to run if art later appears
  for a retired colourway, and refuses to empty a product.

  Lead images default to the alphabetically first look (Black hoodie, Dinosaur
  costume, Boo sweater). Fine seasonally; reorder one image each if you want
  different heroes.


- **HOUSE ART: 7 OF 10 FALL PRODUCTS DONE, 106 VARIANTS WIRED (2026-08-18).**
  Cream #F7F2E9 masters shot with `nano-banana-pro`, recoloured per look so
  pose, framing, lighting and shadow stay locked, uploaded and wired by
  `config/apply_fall_art.py`, then led by `config/promote_fall_art.py`.

  Done: Pumpkin Hoodie (5 colours, 65 var), Big Dog Costume (Tiger/Rabbit/
  Dinosaur, 16 var), Turkey Sweater (Turkey/Boo/Plaid, 12 var), Skeleton Suit,
  Ball Launcher, Pumpkin Snuffle Mat, Roast Turkey Sniff Toy.

  **STILL ON CJ PHOTOGRAPHY, 3 products:** Jack-o-Lantern Sweater (4 colours,
  20 variants), 3-in-1 Steam Grooming Brush (2 colours, NOTE its CJ references
  carry burnt-in English marketing text so ban text explicitly), Pumpkin Chew
  Toy (1). Drop files into `config/branding/fall/` as
  `<handle>__<option value>.jpg` and rerun both scripts; they are idempotent.

  **TWO TRAPS WORTH KEEPING.** Uploading art is NOT enough: a new image lands
  LAST, so the CJ photo stays position 1 and remains the COLLECTION CARD and
  product hero. Every swatch was correct while every product card still showed
  the old photo. `promote_fall_art.py` fixes that and verifies position 1 on the
  live product. Second, `variant.image_id` drives the CART THUMBNAIL, not just
  the gallery, so an unwired variant shows the wrong colour at the moment of
  purchase.

  Lead image is currently the alphabetically first look (Dinosaur, Black, Boo).
  Fine for now; if you want Tiger leading the costume, reorder that one image.


- **HOUSE-STYLE ART STARTED. Pumpkin Hoodie DONE, 65/65 variants wired
  (2026-08-18).** `config/apply_fall_art.py` uploads from
  `config/branding/fall/<handle>__<option value>.jpg` and points
  `variant.image_id` at the matching colour, which is what drives the CART
  THUMBNAIL as well as the swatch.

  Pipeline that works: shoot ONE master per product on cream #F7F2E9 with
  `nano-banana-pro` from the CJ reference, eyeball it, then RECOLOUR the
  approved master for each colourway so pose, framing, print and shadow stay
  locked. The Black/Blue/Red/Pink hoodies are recolours of the Grey master and
  are pixel-consistent with it.

  | Product | Art done | Variants wired |
  |---|---|---|
  | Pumpkin Hoodie | 5 of 5 colours | **65/65** |
  | Big Dog Costume | Tiger only | 6/16 |
  | Turkey Sweater | Plaid only | 4/12 |
  | other 7 fall products | none yet | on CJ photos |

  **REMAINING ART, 4 design shots then 7 single masters:** Big Dog Costume needs
  Rabbit and Dinosaur; Turkey Sweater needs Turkey and Boo (the Boo design is
  black knit with orange trim and an embroidered BOO in orange, purple and green
  with a witch hat on the B, see CJ image 5 of CJGD1841040). Then single masters
  for Skeleton Suit, Ball Launcher, Snuffle Mat, Roast Turkey, Pumpkin Chew,
  Steam Brush (2 colours) and Jack-o-Lantern Sweater (4 colours).

- **TWO DESCRIPTIONS WERE WRONG AND ARE FIXED.** Both caught by opening the CJ
  photography at full size, which the option values and listing titles did not
  reveal. The "Thanksgiving Turkey Coat" is a KNIT SWEATER with a mock neck, not
  a lapel coat; renamed to **Wagvive Thanksgiving Turkey Sweater** and rewritten.
  The Glow Skeleton Suit now states plainly that its sizes are SMALL BREED and
  points large-dog buyers at the Pumpkin Hoodie (XS-9XL) and Big Dog Costume
  (3XL-8XL). `config/fix_fall_copy.py`.


- **FALL LINEUP COMPLETE AT 11 PRODUCTS, 124 VARIANTS, ALL BUYABLE (2026-08-18).**
  Wave 1 (`add_fall_lineup.py`) then wave 2 (`add_fall_wave2.py`).

  **Wave 2 fixed three real weaknesses in wave 1:**
  * Squeaky Bones and the first Snuffle Mat were ARCHIVED. Cheap cartoon prints,
    and CJ's own snuffle-mat copy is a template calling it an "Odor pad".
  * **Size coverage.** The Glow Skeleton Suit is kept but its own CJ copy says
    "your small dog", so its S-XL is SMALL BREED and the description now says so.
    The **Pumpkin Hoodie runs XS to 9XL** and the **Big Dog Costume 3XL to 8XL**,
    so every size is covered between them.
  * Better enrichment twice: **Pumpkin Snuffle Mat** (non-slip base) and
    **Roast Turkey Sniff Toy** (treats hide in removable vegetables).
  * **Automatic Ball Launcher $94.99** on US warehouse stock.

  Live: Skeleton Suit 4, Jack-o-Lantern Sweater 20, Turkey Coat 12, Steam Brush
  2, Ball Launcher 1, Pumpkin Hoodie 65, Big Dog Costume 16, Pumpkin Snuffle 1,
  Roast Turkey 1, Pumpkin Chew 1, Squirrel Plush 1 = **124/124 buyable**.

  Homepage: "Dressed for fall" band sits directly under "Start with a kit" with
  all 11. Nav: "Fall & Halloween" is 2nd in main menu and in footer-shop.
  Collection `fall-halloween` (517682135329).

  **HORIZON TRAP, cost avoided:** product-list takes a BARE collection handle
  ("bundles-kits"). Writing "collections/fall-halloween" renders an EMPTY band
  that still looks like a real section. Also `max_products` had to go to 12; at
  the inherited 6 the band cut off at 8 and the hero costume was missing.

- **CJ PAIRING DONE FOR ALL TEN FALL PRODUCTS (2026-08-18).** Verified pair by
  pair on `shopSku === CJ SKU` before every Confirm. `audit_cj_connections.py`
  is GREEN: 46/46 products have a compliant carrier, every SKU resolves, stock
  is at the sellable location only, everything buyable, every kit intact.

  **The runbook was NOT obsolete and now says so.** CJ React-rebuilt the
  CONNECTED table at `/mine/products/connection`, which has no `angular` object,
  but pairing still runs in the old Angular app reached via the Unconnected tab
  at `/my.html#/products-connection/pending-connection`. The exact working
  sequence is written up in `docs/knowledge/cj-pairing-runbook.md` section 4b.
  The one real trap: the shipping select uses `ng-options` over OBJECTS, so
  setting `select.value`, dispatching `change`, or `$setViewValue` all silently
  fail. Set the model object on the select's own scope and call
  `getwuliuway()` inside `$apply`.

  **audit_cj_connections.py had three faults, all fixed:** it guessed shipping
  origin from a `CJBQ` prefix (origin is in the STOCK ROWS; the CJCT-prefixed
  launcher is US-warehoused and was quoted from China), it did not retry
  `/product/query` (one flaky run produced nine false "not found in CJ" alarms
  on live products), and it treated a **$0.00 quote as no carrier** (it is
  missing data, but Fedex US to US genuinely ships the launcher in 3 to 7 days;
  now a note that the US domestic fallback is used).

- **STILL OPEN: house-style imagery.** All ten launched on CJ's own verified
  photography, not cream #F7F2E9, and there is no per-variant `image_id` wiring,
  so colour swatches do not swap photos. This is now the ONLY outstanding item
  on the fall lineup. Plan: shoot a master per product with `nano-banana-pro`
  (several CJ references carry burnt-in English text, so ban text explicitly),
  then recolour the approved master per variant, then wire with
  `apply_colorway_covers.py`-style variant image assignment. Biggest wins first:
  Pumpkin Hoodie (5 colours), Big Dog Costume (3 designs), Turkey Coat (3),
  Jack-o-Lantern Sweater (4).

- **FALL LINEUP COMPLETE AT 11 PRODUCTS, 124 VARIANTS, ALL BUYABLE (2026-08-18).**
  Wave 1 (`add_fall_lineup.py`) then wave 2 (`add_fall_wave2.py`).

  **Wave 2 fixed three real weaknesses in wave 1:**
  * Squeaky Bones and the first Snuffle Mat were ARCHIVED. Cheap cartoon prints,
    and CJ's own snuffle-mat copy is a template calling it an "Odor pad".
  * **Size coverage.** The Glow Skeleton Suit is kept but its own CJ copy says
    "your small dog", so its S-XL is SMALL BREED and the description now says so.
    The **Pumpkin Hoodie runs XS to 9XL** and the **Big Dog Costume 3XL to 8XL**,
    so every size is covered between them.
  * Better enrichment twice: **Pumpkin Snuffle Mat** (non-slip base) and
    **Roast Turkey Sniff Toy** (treats hide in removable vegetables).
  * **Automatic Ball Launcher $94.99** on US warehouse stock.

  Live: Skeleton Suit 4, Jack-o-Lantern Sweater 20, Turkey Coat 12, Steam Brush
  2, Ball Launcher 1, Pumpkin Hoodie 65, Big Dog Costume 16, Pumpkin Snuffle 1,
  Roast Turkey 1, Pumpkin Chew 1, Squirrel Plush 1 = **124/124 buyable**.

  Homepage: "Dressed for fall" band sits directly under "Start with a kit" with
  all 11. Nav: "Fall & Halloween" is 2nd in main menu and in footer-shop.
  Collection `fall-halloween` (517682135329).

  **HORIZON TRAP, cost avoided:** product-list takes a BARE collection handle
  ("bundles-kits"). Writing "collections/fall-halloween" renders an EMPTY band
  that still looks like a real section. Also `max_products` had to go to 12; at
  the inherited 6 the band cut off at 8 and the hero costume was missing.

- **STILL OPEN ON THE FALL LINEUP. Both matter.**

  1. **CJ PAIRING IS NOT DONE, AND THE RUNBOOK IS OBSOLETE.** None of the 10 new
     products is connected to CJ, so **orders for them will not reach
     fulfilment**. CJ has REBUILT `/mine/products/connection` in React: there is
     no `angular` object on the page any more, so the runbook's
     `injector().get('dsp').postFun('...pullPlatformProduct')` sync hook does not
     exist. The new page has Connected / Unconnected tabs and an
     "+Add Sourcing Connection" button. The new products are NOT yet in CJ's
     cache, so the first job is finding what replaced the sync call.
     `docs/knowledge/cj-pairing-runbook.md` needs rewriting against the new UI.

  2. **House-style imagery not shot.** All 10 launched on CJ's own (verified
     clean) photography, not cream #F7F2E9, and no per-variant `image_id` wiring,
     so colour swatches do not swap photos. Deliberate trade for the Halloween
     deadline, but it is the biggest remaining quality gap.


- **FALL LINEUP LIVE, 6 PRODUCTS, 47 VARIANTS (2026-08-18).** Sourced from a
  5,535 product CJ sweep (`config/scout_fall.py`), costed on live freight,
  created by `config/add_fall_lineup.py`. All active, published to all five
  channels, stocked, and verified buyable. New "Fall and Halloween" collection
  (517682135329).

  | Product | Price | Var | Floor | SPU |
  |---|---|---|---|---|
  | Glow in the Dark Skeleton Suit | $24.99 | 4 | 46.4% | CJGD2143164 |
  | Halloween Snuffle Mat | $32.99 | 1 | 44.9% | CJYD2183039 |
  | Jack-o-Lantern Sweater | $17.99 | 20 | 37.5% | CJGD1809813 |
  | Halloween Squeaky Bones | $15.99 | 8 | 46.3% | CJYD2146653 |
  | Thanksgiving Turkey Coat | $19.99 | 12 | 31.7% | CJGD1841040 |
  | 3-in-1 Steam Grooming Brush | $26.99 | 2 | 45.5% | CJYD2256797 |

  **TWO THINGS STILL OPEN ON THESE, both needed:**
  1. **CJ PAIRING.** None of the six is connected to CJ yet, so orders will NOT
     flow to fulfilment. Browser only, owner's real Chrome, one product at a
     time per `docs/knowledge/cj-pairing-runbook.md`.
  2. **House-style art.** They launched on CJ's own (verified clean) photos, not
     cream #F7F2E9. Deliberate: Halloween is 31 October and orders must land by
     about 10 October, so early beat perfect. Reshoot and swap with
     `replace_product_image.py`.

- **US WAREHOUSE: available, and it does fix freight, but not cost.**
  446 US-stocked pet products found (`config/scout_us_warehouse.json`); the
  signal is `shippingCountryCodes` containing a bare "US" on the product list
  row, NOT the CJBQ sku prefix and NOT a stock-row country you assumed. US stock
  pays no duty and flat $11 Fedex regardless of weight, so an 1,800g launcher
  and a 350g toy cost the same to ship. But US wholesale runs 4 to 10x China
  ($19-52 vs $1-5), because someone already imported and stored it. At the
  catalogue's median 16.6% floor two clear market: the **automatic ball launcher**
  (CJCT2567740, $52.59, floor price $82 against a $80-130 market, 167 units,
  337 listings) and the **7pc grooming kit** (CJHR2665670, floor $40 against
  $40-70, but only **30 units**). Neither is built yet; the launcher is the
  better bet and is genuinely demo-able.


- **THE "UNSHIPPABLE" SCARE WAS A FALSE ALARM. RESOLVED 2026-08-18.**

  On 2026-08-17 I concluded that ten variants across five products could not be
  shipped by CJ, because `/product/stock/queryBySku` returned an empty `stock`
  array for them, and the item blamed for order #1002 was among them. I changed
  `cj_stock()` to return 0 in that case and held all ten at zero.

  **That was wrong.** CJ's own UI settles it: the Bouncy Egg Squeaker product
  page shows **"Inventory: 46587 (CJ: 0, Factory: 46587)"**, carrier **"LuWei
  Ordinary US - Available"**, processing 1 to 3 days, and no sold-out state. The
  API had been saying the same thing and I misread it: all five products return
  `status: 3`, carry 48 to 86 other sellers' listings, and quote **27 carrier
  options each**; CJ flags **no line of order #1002 abnormal**, and CJ's
  **Abnormal Orders tab reads 0**.

  Also disproved along the way: I had treated order #1002 being stuck as
  corroboration. Order **#1003 is stuck identically** (both Pending, paid the
  same second, tracking assigned) and **every one of its five components is
  healthy**. CJ's own banner explains Pending: it becomes Processing "when a
  tracking number is generated and products have been well prepared in our
  warehouses". Both orders are simply awaiting warehouse prep.

  **What was reverted:** `cj_stock()` falls back to `totalInventoryNum` again
  when there is no stock record, which is the figure CJ's product page displays.
  All ten variants were restored from CJ and are buyable again on the storefront.
  `audit_cj_shippability.py` and its qa log were DELETED: the predicate was
  wrong and a misleading audit is worse than none.

  **What was kept, and why.** The Toy Kit and Dog Enrichment Kit stay on their
  new components (Woodland Rope-Limb Plush, Dental Chew Stick) at $50.00. The
  replacements are good products, both kits are live at 3/3 with fresh art and
  verified copy, and churning back would be cost for no gain. The frisbee and
  egg are simply standalone products again. Reverting is possible if wanted:
  edit `config/kit_colorways.py`, then validate, rebuild, re-shoot.

  **What replaced the bad check.** `config/guard_unshippable.py` now asks the
  question that actually matters: it requests a LIVE CJ FREIGHT QUOTE per
  variant and requires at least one carrier inside the 12 business day promise,
  then asserts on the live storefront that anything failing is not orderable. It
  runs 3-hourly in `scheduled-ops.yml` after the sync steps. **All 145 variants
  currently pass.** Unanswerable SKUs are UNKNOWN and never zeroed.

  **The lesson worth keeping:** "how many units exist" and "can this be
  fulfilled" are different questions. Answer the second by asking CJ for a
  carrier, never by inferring meaning from a stock field. And a single stable
  signal correlating with one failure (n=1) is not proof; three cheap checks
  (product status, other sellers' listings, freight quote) would have caught
  this before anything was zeroed.

  Still genuinely unexplained: why CJ notified about #1002 at all. Both orders
  remain Pending at CJ, which is worth chasing with CJ support if they do not
  move.

- **INVENTORY AUDITED END TO END, INCLUDING KITS (2026-08-11).** Answering
  "is Shopify still tracking everything and matching CJ?". Verdict: yes, with
  one 4-unit drift corrected. Coverage is **184 variants = 145 singles + 39 kit
  variants**, and the two halves are guarded by different mechanisms:

  - **145 single variants**, every one carrying a CJ SKU: `sync_inventory.py`
    found exactly ONE out of step (Pet Hair Remover Mitt / Classic, 8087 vs CJ
    8083, ordinary CJ movement) and it was applied. `fix_locations.py` reports
    every variant stocked at the sellable location ONLY, so no double counting.
  - **39 kit variants**: NEW `config/verify_kit_inventory.py`. All pass.

  **Why kits needed their own check.** `sync_inventory.py` only walks variants
  that carry a SKU. Kits are bundle parents with no SKU, so it never touches
  them and its "all in step" verdict says NOTHING about kits. If a kit parent
  held its own stale stock, Shopify would sell a kit whose component had run
  out at CJ.

  **A Shopify fact I got wrong first, now in CLAUDE.md.** I assumed a healthy
  bundle parent must NOT have `tracked: true`, and the first run duly flagged
  all 39 variants. That assumption was false: bundle parents ARE tracked, just
  like singles. Comparing a kit against the Sneaker Chew Buddy showed the real
  distinction: the kit's inventory level exists but carries **no `available`
  quantity** (`{}`) while a single's carries `available/committed/on_hand`, and
  `requiresComponents` is true. So the decisive test is arithmetic, and it is
  what the script now does: recompute `min(component available // qty needed)`
  independently and require it to equal Shopify's derived
  `sellableOnlineQuantity`. **All 39 match exactly** (e.g. Calm & Comfort 5104,
  bound by the Heartbeat Sloth; the Travel and Grooming kits are bound by the
  Paw Washing Cup). 82 distinct component SKUs all match CJ.

  That is the third audit this week that cried wolf on a healthy store. The
  pattern is worth remembering: **verify the rule against a known-good control
  before trusting the alarm.**

  Also green: `audit_cj_connections.py` (36/36 buyable, freight compliant), and
  `.github/workflows/scheduled-ops.yml` still runs `sync_inventory --apply`,
  `fix_locations --apply` and report-only `margin_guard` every 6 hours at :17.
  Run history could not be read from this machine (no `gh`, private repo), but
  the tiny observed drift is consistent with the job running normally.

- **HOMEPAGE V2: FEWER WORDS, MORE DOGS (2026-08-08, same day, owner call).**
  Two changes on top of the kits-first rebuild, both live and verified:

  **1. Copy cut to quick blurbs everywhere.** Hero sub is now "Six dog care
  kits. One job each. Less than buying the pieces apart."; the trust row runs
  one-liners; the story band is one sentence; the flagship band lists the five
  components and two numbers. All still computed at apply time by
  `homepage_kits_first.py`.

  **2. All six collection tiles are now house-style dogs WITH OUR PRODUCTS**
  (`config/apply_collection_tiles.py --apply`, art in
  `config/branding/collection-tiles/<handle>.jpg`). The old tiles were stock
  photos showing other brands' gear; two collections had no image at all. Four
  takes needed re-shoots before approval: the Toys tile invented two green
  creatures we do not sell, and the Travel tile included a LEASH, which is not
  in the catalogue; a shopping tile must not show unsellable merchandise.

  **Two Shopify traps found and now handled in the scripts:**
  - `collectionUpdate` SILENTLY keeps the old image if the collection already
    has one: no userErrors, mutation "succeeds". Clear with `image: null`
    first, then set. Caught only because verification re-fetches and compares
    FILENAMES, not image presence.
  - Homepage HTML still serves mixed stale/fresh CDN renders minutes after a
    write; the same check failed then passed across two fetches. Poll.

- **HOMEPAGE REBUILT KITS-FIRST (2026-08-08, after the pairing work).** Owner
  call: before marketing spend, make the homepage sell the kits. Full research,
  decisions and sources in **`docs/homepage-redesign-2026-08.md`**; applied by
  `config/homepage_kits_first.py --apply` and verified live.

  The short version: the hero video stays but the H1 now states the offer and
  the primary CTA goes to the bundles collection; the six-kit grid with live
  price + compare_at anchoring is the FIRST content section (it used to be
  seventh, behind eight singles); the old duplicate kit band is now a Calm &
  Comfort flagship spotlight ("$109.00 together, $26.95 less than apart") over
  a new Runway banner built from the kit's real component photos
  (`wagvive-band-calm-kit.jpg` in Files); singles and categories are demoted to
  secondary paths. Also fixed stale facts ("Five kits", "four essentials") and
  two British spellings ("ageing", "grey muzzles").

  **Things to know:**
  - Every dollar figure on the page is computed from the live storefront at
    apply time and the script REFUSES to write if a savings claim would be
    false. **Re-run `homepage_kits_first.py --apply` after any kit repricing**
    to refresh the marquee, band, and FAQ numbers.
  - Rollback: PUT `config/theme-backup/templates__index__2026-08-08-pre-kit-redesign.json`
    back to `templates/index.json`.
  - Deliberately NOT done: no fake reviews (add real stars to kit cards once
    Judge.me exists), no WELCOME10 on the page (wire the signup incentive into
    the newsletter block only when welcome flow #76a is live, or it becomes a
    permanent price cut), no urgency theatre.
  - When GA4 lands, watch homepage CTR to /collections/bundles-kits, kit share
    of orders, and AOV against the +20 to 30% bundling benchmark.

- **COLORWAY COVERS FINISHED AND THE WIPES REPLACEMENT IS LIVE (2026-08-08).**
  Two of the three jobs are done and verified against the live system. The third,
  CJ pairing, is **NOT done** and is described in its own section below.

  **1. All 39 kit variants now carry their own colorway photo.** The last 12
  covers are shot, wired and live across Grooming, Enrichment, Travel and Calm &
  Comfort. `/products/<handle>.js` returns 18 distinct `featured_image`s across
  the six kits with all 39 variants buyable.

  Four takes were rejected on inspection before upload, which is the entire
  argument for that step:
  - **Grooming Pink**: the paw washing cup lost its moulded white paw print. The
    blanket "no logos" ban had deleted a real product feature. Name such
    features explicitly as part of the product.
  - **Travel Natural**: the cream backdrop rendered as seamed rectangular panels
    rather than one sweep; a later take then drew **two** paw cups, which would
    have misstated the kit contents. Fixed by pinning object COUNT in the prompt
    ("exactly one cup appears in the whole image").
  - **Calm Blue**: the sloth's orange module came back with a debossed circular
    paw badge, the same supplier-brand-mark class the unbranded master exists to
    avoid.
  - **Calm Grey**: the plush rendered as a floppy-eared animal, then as a
    top-down teddy, before the side-on sloth pose held on the third attempt.

  **The toothbrush scale clause needs adapting per kit.** As written it anchors
  the toothbrush against "the sneaker toy", which is not in the Grooming kit, so
  naming it risks the model drawing one. Anchored to the nail grinder pen
  instead, which is in frame; it renders finger-sized in all three.

  **2. The Dental Chew Stick replaces the retired wipes.** Live, verified:
  3 of 3 variants buyable, 4 images, $14.99, in the Grooming collection, and
  back in the cart cross-sell pool in the slot the wipes vacated.
  `config/add_dental_chew.py` is the whole job, re-runnable, with `--finish`.

  CJ SPU **CJGY2091358**, 140g natural rubber, listed by 184 CJ stores (3.3x the
  next dog-only dental candidate). All ELEVEN of CJ's photos were checked at
  ORIGINAL resolution: no packaging at all, no text or logo on the product, dogs
  only. Deliberately not a liquid, since CJ's liquid freight rise is what killed
  the wipes.

  Cost $3.46 + freight $6.04 (LuWei Ordinary US, 5 to 11 days, chosen by
  `freight_floor.resolve()` from 27 carriers) = landed $10.50. At $14.99 that is
  **24.9% margin, $3.73 contribution**, against the wipes' 21.6% on $13.99.
  `floor_margin_pct` 16.9. 50% would have needed $23.02, which is far above
  market and no longer the rule: no product carries a floor at or above 50% and
  the median is 16.6%. Owner picked $14.99 from a costed range.

  **THREE TRAPS WORTH REMEMBERING, all caught by re-fetching rather than
  trusting a write:**

  - **CJ returns TWO stock row shapes, and CLAUDE.md only describes one.**
    Summing `inventory + factoryInventory` returned **0** for all three new
    variants, which would have launched every variant unbuyable. A known-good
    control SKU returned 0 the same way: for these rows those two fields are
    **null** and only `totalInventoryNum` is populated.
    **`sync_inventory.cj_stock()` already handles both shapes. Always call it;
    never reimplement the sum.** Real stock was 14813 / 13247 / 11116.
  - **A new product is published to Point of Sale ONLY.** It was ACTIVE, stocked,
    imaged and in the collection, and still **404'd on the storefront**, because
    Admin API creation does not publish to Online Store. `add_dental_chew.py` now
    copies the channel set from a product known to be live.
  - **`inventory_quantity` in products.json lags and is not evidence.** It read 0
    straight after a correct write; `inventory_levels` showed the right figures
    at Shop location and nothing at the legacy CJ location.

  **3. Two audit bugs fixed, both of which were hiding real signal.**
  - `audit_kits.py` counted every colorway cover as an "extra" gallery image and
    failed **all six kits at once**, a false alarm loud enough to bury a true
    one. It now splits colorway covers out by alt tag and checks them in their
    own right: a MISSING colorway cover is now a reported problem, because that
    variant would fall back to another colorway's photo. Note it matches the alt
    suffix against real colorway values, since the position-1 flat-lay is tagged
    "<title> - everything included" and was being counted as a fourth colorway.
  - `apply_colorway_covers.py` in report mode returned 0 unconditionally, so as a
    release gate it **could only ever pass**. It now returns 1 when covers are
    missing.

- **CJ PAIRING: DONE AND VERIFIED (2026-08-08).** Both halves complete, in the
  owner's real Chrome, following `docs/knowledge/cj-pairing-runbook.md`.

  **1. Dental Chew Stick is paired.** Shopify 10487573774625 to CJ SPU
  CJGY2091358, all three variants, every one on **LuWei Ordinary US** — the
  carrier `freight_floor.resolve()` picked for this exact SKU, which is the
  carrier the $14.99 price was modelled on:

  | Store variant | CJ SKU | Carrier | CJ stock |
  |---|---|---|---|
  | Teal 53215841190177 | CJGY209135802BY | LuWei Ordinary US | 14813 |
  | Yellow 53215841222945 | CJGY209135803CX | LuWei Ordinary US | 13247 |
  | Green 53215841255713 | CJGY209135804DW | LuWei Ordinary US | 11116 |

  Both runbook pre-confirm checks passed before the single Confirm click:
  `matchitem.shopType === 'Shopify'`, and all 3 pairs satisfying
  `first.shopSku === last.SKU`. Automatic Connection was left ON (SKUs match
  exactly on both sides) and inventory sync left OFF, which the dialog itself
  confirmed with "The inventory sync is off".

  **2. The archived Dental & Ear Wipes are un-paired.** SPU CJYD2169796 now
  returns no rows on the Connected list.

  **What made it work this time, on top of the runbook.** The `iframe#guid-frame`
  overlay was the real cause of the earlier failure: it silently swallowed clicks
  on the right-hand search box, which read as "this field will not take input".
  Removing it after every navigation fixed it. Two details the runbook did not
  yet name have been added to it: the right-hand search binds to
  **`searchinfostr`** (not `souresearchinfo`), and the right-hand CJ list is
  **`shop2`** while the left store list is `shop`.

  **Verified from outside CJ**, which is the check that does not depend on CJ's
  UI telling the truth:
  - `audit_cj_connections.py` green.
  - **New: `config/verify_cj_pairing_sanity.py`.** `audit_cj_connections` proves
    every SKU RESOLVES; it cannot prove it resolves to the RIGHT thing, which is
    how the water bowl was once mapped to a cat bed. This resolves all 36 SPUs
    through CJ and compares the CJ product name against our title. No product
    resolves to a listing for another animal or category. The Dental Chew Stick
    scores 100%. Note the alarm only fires on a LOW word overlap: CJ listings
    name every compatible species, so the Pet Hair Remover Mitt's "For Dog Cat
    Rabbit" is a correct pairing at 100% overlap, not a mismapping.
  - **Full live sweep of all 42 active products**: every one on the storefront,
    fully buyable, imaged, and priced per SKU to the price book. The new product
    renders, the retired wipes 404, Grooming lists the chew stick and no longer
    lists the wipes, and the smart Toys & Play collection picked it up via the
    `toy` tag.

- **KITS REBUILT ONTO SIZE + COLORWAY, COVERS PART DONE (2026-08-07).**

  **Kits (done, verified).** Full per-component variant choice is impossible on
  Shopify: products cap at 3 options and 2048 variants, every kit needed 4 or 5
  option slots, and Travel would have needed 15,552 variants. Confirmed in the
  API docs, error OPTIONS_OVER_LIMIT. So kits now expose one **Size** that drives
  every size-varying component at once, plus one curated **Colorway**. 39 variants
  instead of 234. `config/kit_colorways.py` is the source of truth;
  `validate_colorways.py` proves every value resolves to a live buyable variant;
  `verify_kit_variants.py` checks all 39 by component IDENTITY, not count.

  **The trap:** `productVariantRelationshipBulkUpdate` derives the parent price
  from the sum of its components, silently overwriting what `productSet` wrote.
  Reprice AFTER relationships. `rebuild_kits.py --reprice-only` fixes it without
  re-running productSet (which would destroy every variant and relationship).

  **Colorway covers (2 of 6 kits done).** New Puppy and Toy are complete: 9 of 39
  variants carry their own colorway image, wired via `variant.image_id` (which
  also drives the cart thumbnail). **12 covers remain**: Grooming, Enrichment,
  Travel, Calm & Comfort, 3 each. Run `config/apply_colorway_covers.py` with no
  flags: it names every missing cover and exits non-zero until all exist.
  `scratchpad colorway_refs.json` logic lives in the same script; regenerate that
  mapping by re-running the per-kit query if needed.

  Art goes in `config/branding/kit-covers/colorway/` as `<handle>__<Colorway>.jpg`.
  Size is deliberately NOT in the filename: the three sizes photograph identically,
  so they share one image. **Every cover must be built from that colorway's exact
  component VARIANT photos**, and eyeballed before upload. That check has caught a
  sneaker rendered as a real shoe, a toothbrush with no nubs, and a supplier logo
  rendered as garbled text.

  **Toothbrush scale is solved.** It rendered banana-sized. The fix is an explicit
  clause: "a finger-sized silicone sleeve about 6 cm long, clearly the SMALLEST
  object in frame, roughly one third the length of the sneaker toy. Do not enlarge
  it." Include it in every Grooming prompt.

  **Wipes are gone.** Archived (not deleted: order #1001 contains them). Removed
  from the Grooming collection, the FAQ, and the cart cross-sell pool. Storefront
  404s. The typos were on the REAL supplier packaging, verified against CJ's own
  photos, so they could not be fixed without misrepresenting the product.

  **Still open:** 12 colorway covers, and a replacement product for the wipes
  (task #85) needing listing, master + lifestyle imagery, Grooming collection,
  and CJ pairing. CJ pairing IS doable by me via Claude in Chrome against the
  owner's logged-in session; it is browser-only, not owner-only.

- **SUPPLIER BRAND MARK REMOVED, AND A WORSE ONE FOUND (2026-08-07).** The
  Heartbeat Soothing Sloth photo carried a supplier's brand ("FUDI JINTIN" plus a
  paw logo) embossed on the orange heartbeat module. Retouched with Runway in
  edit mode, reframed, and published to BOTH places it lived: the product's own
  position-1 image and the copy inside the Calm & Comfort Kit gallery. Verified
  live: no image anywhere still resolves to the branded master.

  Two reusable tools came out of it. `config/replace_product_image.py` swaps one
  image while preserving position, alt and **variant wiring** (deleting an image
  silently nulls `variant.image_id`, which breaks the cart thumbnail with no
  error anywhere). `config/match_framing.py` measures the subject's bounding box
  in the old and new shots and crops the new one to land in the same place at the
  same scale, because Runway re-renders the whole scene even when asked to
  retouch one small surface, and the subject drifts.

  **Then a full sweep of all 141 product images turned up something worse.** The
  **Dental & Ear Wipes** listing shows the SUPPLIER'S TUB PACKAGING, and it is
  bad on three counts at once: it is not Wagvive branding, it shows CATS on a
  dog-exclusive store, and the label has visible typos ("Unsented", "Freshman
  Breath&prevent Bad Breath", "Generate For Cats And Dogs").

  **This one is NOT a straight retouch and was deliberately left for the owner.**
  Generating Wagvive-branded tubs would show a package the customer will never
  receive, which is a misleading product image, not a cleanup. The honest options
  are: photograph the wipes out of the tub, use a plain unbranded tub, or drop
  the SKU. That is a call about what we are willing to represent, so it is the
  owner's. See task #83.

  Everything else in the catalogue is clean. The nail grinder's "Grinder" label
  is a generic functional word, not a brand, and stays.

- **CJ CONNECTION RE-AUDITED AFTER ALL OF THE ABOVE (2026-08-07).** Clean:
  36 distinct SPUs all resolve to live CJ variants, 144 sellable variants, stock
  only at the canonical Shop location, every variant buyable on the storefront,
  all six kits intact, and all 36 products have a carrier inside the 5 to 12
  business day promise. Log in `docs/qa/cj-connection-audit-2026-08-07.json`.

  **Know what that audit does and does not prove.** It resolves our SKUs against
  CJ's catalogue via `/product/query`, so it proves the SKUs are real and
  sellable. It does NOT read the Shopify-to-CJ pairing itself: that binding lives
  in CJ's Angular app (`cj-platform-web`), which has no public API. Nothing this
  session touched SKUs or variants, so the pairing could not have been affected,
  but if you ever need to prove pairing directly it is a browser job or a real
  test order.

- **KIT COVERS AND CROSS-LINKS REBUILT (2026-08-07).** Two things shipped, both
  verified live.

  **1. Every kit has a real cover photo.** The tiled grid covers are gone.
  `config/apply_kit_covers.py --apply` published a styled overhead flat-lay for
  all six kits, generated with Runway from the SAME component photos as tagged
  references, and confirmed live via `/products/<handle>.js` (`featured_image`
  now contains `kit-flatlay-`). Only position 1 changed; the per-component
  gallery shots below it are untouched, which is what `audit_kits.py` reads.

  **Three takes were rejected on inspection, so do not skip that step.** The
  Sneaker Chew Buddy rendered as an actual child's sneaker with a rubber sole
  instead of the soft chew toy; the finger toothbrush lost its all-over nubs;
  and both Calm & Comfort takes reproduced the supplier's embossed brand mark on
  the sloth's orange module as garbled pseudo-lettering. The fix for the last
  one is an explicit instruction to render that surface unmarked. Approved
  source art is in `config/branding/kit-covers/flatlay/`.

  Recentring is done deterministically in `apply_kit_covers.py` by CROPPING to a
  centred square, never by translating pixels, because a translation leaves a
  region to fill and any fill seams against the background vignette. New Puppy
  was 10.4% off centre and is now correct.

  `make_kit_covers.py` (the grid) is kept as the fallback for a new kit with no
  art. **Never run it with `--force`** or every flat-lay reverts to a grid.

  **2. A component page now names EVERY kit it belongs to.** `custom.kit` was a
  single product_reference, so the Cooling Pad advertised the Travel Kit and
  said nothing about Calm & Comfort, the highest-contribution kit at $43.06.
  `config/link_kits_multi.py --apply` created `custom.kits` (a list) and filled
  it from live bundle membership; six of the twenty two components are in two or
  three kits. The snippet promotes the biggest dollar saving and names the rest
  on a quiet line under it. `config/verify_kit_callout.py` confirms all 22
  component pages render correctly.

  **The Liquid trap that cost the most time here: Shopify Liquid will not index
  an array with a variable.** `kit_list[best_idx]` silently evaluates to nil,
  the entire callout vanishes, and NO Liquid error appears anywhere. A literal
  index works, which makes it look impossible. Capture the winner with
  `assign kit = k` inside the loop instead. Proven live with a probe:
  `{% assign zz = 0 %}{{ kl[zz].title }}` rendered empty while the same list
  iterated fine in a `for`.

  Also learned: the theme **assets endpoint is eventually consistent**. A GET
  straight after a PUT can return the pre-write body, so `deploy_snippet.py`
  polls before reporting failure. And storefront product pages served mixed
  stale and fresh renders for several minutes: across two verifier runs the SAME
  pages passed and failed alternately, so `verify_kit_callout.py` retries per
  page. `?nocache=` does not reliably defeat this.

  Open, low priority: the live product photo for the Heartbeat Soothing Sloth
  shows a SUPPLIER's brand embossed on the orange module. Not introduced by this
  work, but it is a third-party mark sitting on a Wagvive product page.

- **FIRST EMAIL AUTOMATION IS LIVE (2026-08-05).** Abandoned checkout, three
  emails at 1h / +23h / +48h, confirmed **Active** in Messaging › Automations.
  `WELCOME10` appears in email 3 only.

  **This overturned a wrong conclusion.** The flows doc said Claude could not
  build these because there is no Admin API. The API part is true; the
  conclusion was not. The Messaging email editor has a **Custom Liquid block**
  that takes raw HTML with Liquid, so every marketing email is now authored in
  this repo and pasted in. Paste-ready blocks:
  `config/email-templates/marketing-abandoned-{1,2,3}-block.html`.

  Six traps, each of which cost an attempt, are written up in
  **`docs/knowledge/shopify-messaging-custom-liquid.md`. Read it before
  building any remaining flow.** Most important: do not rebuild the page
  wrapper inside the block (it overflows), `{{ unsubscribe_link }}` emits a
  whole anchor so it must never go in an href, and Shopify adds its own Footer
  block that duplicates the address and unsubscribe unless you leave them out.

  Also confirmed dead ends: **Shopify Flow does not help** (`.flow` files are
  hash-signed with a proprietary algorithm, and Flow's send-marketing-email
  action opens the same editor), and **automations are invisible to the API**
  (`marketingActivities` and `marketingEvents` both return 0), so the only
  verification is the admin UI or a real send.


- **PC SESSION 2026-08-05, after merging the web session.** The web branch
  `claude/project-progress-check-2mb93r` was merged to main; its nine commits
  had never landed, so from the owner's side none of that work was visible.
  Then, on the PC:

  1. **Task #71 applied and verified.** `config/fix_product_care_copy.py --apply`.
     The four wrong text blocks are gone from all 42 product pages, including
     the "Care & use" accordion that told buyers to rinse a heartbeat plush.
     Its verifier had TWO false negatives, both fixed: it probed
     `/products/<handle>?sections=main`, which returns null because Shopify
     will not render a product's main section standalone, and its dash check
     scanned raw HTML, which always contains em dashes inside Shopify's own
     `<style>` comments. **The section rendering API works for footer and
     homepage sections but NOT for product templates**; use the full page there.

  2. **SEO title and meta description written for all 42 products**
     (`config/marketing/seo_meta.py`). Every one was null. This directly feeds
     the two free channels the plan leads with: Google free listings rank
     partly on it, and Pinterest rich pins read the meta description.

  3. **The en dash is out of every page title.** `snippets/meta-tags.liquid`
     used `&ndash;` as the `<title>` separator, so it appeared in every browser
     tab, search result and shared link preview. Now a pipe, matching the
     homepage SEO title. It survived the 2026-08-04 dash sweep because that
     sweep read rendered body copy, where `<title>` does not appear.

  **One loose end:** `/products/calm-comfort-kit` still renders the old title
  and description. Admin is correct, 41 of the 42 pages render both fixes, the
  response is `cf-cache-status: DYNAMIC` so it is not Cloudflare, and a forced
  `productUpdate` touch did not clear it. No handle collision, no redirect.
  It is a stuck render cache on Shopify's side. **This is the phase 1 landing
  page, so confirm it before spending:**

  ```
  curl -s "https://wagvive.com/products/calm-comfort-kit" | grep -o "<title>.*</title>"
  ```

  Expect `Dog Anxiety Kit: Heartbeat Toy, Calming Wrap, Cooling Mat | Wagvive`.
  If it is still wrong after a day, unpublishing and republishing the product
  to the Online Store channel will force it, at the cost of a brief 404.


- **MARKETING PHASE 0 STARTED (2026-08-05, web session).** Three things.

  1. **`WELCOME10` is LIVE.** 10% off the entire order, **minimum $45**, one use
     per customer, no expiry, `discountClass: ORDER`, ACTIVE with 0 uses,
     `gid://shopify/DiscountCodeNode/1678979858721`. Live summary reads
     `10% off entire order • Minimum purchase of $45.00 • One use per customer`.
     Verified with four draft orders, all deleted after: Calm & Comfort $109 to
     $98.10 with free shipping held, Dog Enrichment $46 to $41.40 (the cheapest
     kit, the boundary case), and a $31.99 single correctly getting **nothing**.
     **The plan's "10 to 15%" needed correcting twice.** First, my claim that a
     blanket code sends singles negative was wrong: it came from
     `cac_ceiling.py` excluding the $5.95 shipping the customer pays under $60,
     and counted properly nothing goes negative at either rate. Second, the rate
     is 10% not 15% because 15% drops Grooming Essentials to $59.50, under the
     free-shipping threshold. The **$45 minimum** then does what a kits-only
     restriction was meant to do without the "code not valid" experience: all
     six kits qualify (cheapest $46), no single does (most expensive $33.99).
     Cost if every first order uses it is $6.68, about 20% of average kit
     contribution, against $43.75 per order for paid acquisition at the plan's
     own phase 1 assumptions. **Watch incrementality, not margin:** if coded
     orders exceed ~75% of all orders it has become a permanent price cut.

  2. **All five email flows are drafted:**
     `docs/marketing/email-flows-2026-08.md`. Paste-ready copy plus a
     step-by-step flow 2 build guide. **Claude cannot build the automations from
     any device** and this is now confirmed rather than assumed: Shopify exposes
     no Admin API for marketing automations, `marketingEvents` is read-only and
     there is no create mutation. Owner has switched Settings › Checkout ›
     Abandoned checkouts OFF, so the duplicate-send conflict is resolved and
     flow 2 is clear to build.

  3. **Pre-spend landing page audit:**
     `docs/marketing/landing-page-audit-2026-08.md`. **It found that task #71
     was never applied and had silently fallen out of this file.** The theme's
     global "Care & use" accordion tells every buyer on all 42 product pages to
     "rinse or wipe clean after use and let it dry fully", to introduce
     "grooming tools" gradually, and refers to "older or anxious dogs". On the
     Calm & Comfort Kit, which is where phase 1's $150 lands, all three are
     wrong. Exact replacement text has been sitting in
     `docs/qa/theme-copy-fixes.md` since 2026-08-04. The same four edits clear
     four live en and em dashes and a hyphenated day range.

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

## NEXT PC SESSION: the complete plan, about 60 minutes

Everything below needs either `config/shopify.env` (PC only) or the Shopify
admin UI (no API exists). Work top to bottom. Copy, delays and decisions are all
settled; none of this needs thinking about, only doing.

### Step 1. Theme copy, task #71. Two minutes.

```
python config/fix_product_care_copy.py            # read the diff
python config/fix_product_care_copy.py --apply    # write and verify
```

Fixes four text blocks that render on **all 42 product pages**, including the
one phase 1 buys traffic for. The worst is the "Care & use" accordion telling
every buyer to "rinse or wipe clean after use and let it dry fully" and
referring to "grooming tools" and "older or anxious dogs" on, for example, a kit
made of a heartbeat plush, a compression wrap, a fleece blanket and a cooling
pad.

The script refuses to write if any dash survives, entities included, verifies
the admin asset, then re-renders through the section rendering API rather than
the cached page. If it reports "still stale after retries", the admin asset is
already correct and the CDN will catch up.

### Step 2. Build the five email automations. About 45 minutes.

**Shopify admin › Marketing › Automations.** There is no API for these, so this
is hands-on-keyboard work on every device. Full copy and the click path per flow
are in `docs/marketing/email-flows-2026-08.md`, section "Building all five".

Build in this order, which is by value, so stopping early stops in the right
place:

| # | Flow | Template to start from | Delays | Time |
|---|---|---|---|---|
| 1 | **Abandoned checkout** | Abandoned checkout | 1h, 24h, 72h | 15 min |
| 2 | **Welcome** | Welcome new subscriber | 0, 2 days, 5 days | 12 min |
| 3 | **Post-purchase** | Order fulfilled trigger | 1 day, 21 days | 8 min |
| 4 | **Browse abandonment** | Abandoned product browse | 4h | 5 min |
| 5 | **Winback** | Win back customers | 60 days | 5 min |

**The trap, and it applies to every multi-email flow.** Shopify puts the exit
condition on the FIRST email only. Steps you add do not inherit it. On every
added email add a Condition first:

- Abandoned checkout: *Checkout completed, is false*
- Welcome: *Customer has not placed an order*

Miss it and you email people who already bought.

**Two things to leave alone:**

- Flow 4's second email (the day-21 review request) stays **unpublished** until a
  reviews app exists. Its button has nowhere to point. Judge.me free tier is the
  plan's choice.
- Settings › Checkout › Abandoned checkouts is already **off**. Leave it off, or
  the first recovery email sends twice.

Send yourself a test on every email before switching each flow on.

### Step 3. The gate test purchase. Ten minutes.

Buy something real, end to end. This is the phase 0 gate in the marketing plan
and it is the only way to confirm three things nothing else can:

1. `WELCOME10` applies at a real checkout and respects the $45 minimum.
2. Whether it stacks with the *"Any 3 toys, 15% off"* automatic discount. The
   `combinesWith` flags say it should, giving about 23.5%. Draft orders do not
   evaluate automatic discounts so this could not be tested any other way. Worst
   case across all 455 possible three-toy baskets is $13.07 of contribution, so
   it is safe either way; this is confirmation, not a risk check.
3. The abandoned checkout sequence fires exactly once, not twice.

If GA4, the Meta pixel and the Pinterest tag are installed by then, this same
purchase is the tracking verification too, and phase 1 unlocks.

### Step 4. Whenever you have the accounts

Google (GA4 + Merchant Center), Meta (pixel + CAPI, data sharing Maximum),
Pinterest (tag + catalogue). Send back the measurement ID, pixel ID and tag ID
and Claude configures and verifies each. Google first: free listings are the only
zero-CPC channel and the 42 feed titles are already written in
`config/marketing/feed_health.py --titles`.

---

### Do these first

Nothing is carried over from 2026-08-08: colorway covers, the wipes replacement
and CJ pairing are all done and verified. The next work is marketing phase 0,
below, which gates every dollar of paid spend.

| Task | What | Who |
|---|---|---|
| **#71** | **Now scripted:** `python config/fix_product_care_copy.py --apply` from the PC. See NEXT PC SESSION step 1. REINSTATED 2026-08-05: written 2026-08-04, never applied, and dropped out of this file in a rewrite. The "Care & use" block is wrong on all 42 product pages and the page phase 1 pays for is one of them. | Owner runs the script |
| **#76a** | **Build all five automations.** See NEXT PC SESSION step 2 for the ordered plan and `docs/marketing/email-flows-2026-08.md` for the copy. About 45 minutes. No API exists for marketing automations on any device. | Owner, Marketing › Automations |

### Then: the rest of marketing phase 0. Free, and it gates everything paid.

| Task | What | Who |
|---|---|---|
| #75 | GA4 property, Meta pixel + Conversions API (data sharing = Maximum), Google Merchant Center with free listings on, Pinterest business account + tag | **Owner creates the accounts**, Claude configures and verifies |
| #75a | Declare "these products have no GTIN" in the Google channel, then apply the 42 feed titles from `config/marketing/feed_health.py --titles` | Claude, once the channel exists |
| #76 | **Copy is DONE** (`docs/marketing/email-flows-2026-08.md`). Remaining: build flows 1, 3, 4 and 5 in Marketing › Automations. Flow 4.2 stays unpublished until a reviews app exists. Shopify native, NOT Klaviyo. | Owner builds, copy is ready |
| #77 | `marketing/ads_report.py`, `marketing/ad_guardrail.py`, `marketing/weekly_brief.py`. Build once ad accounts exist; wire into `scheduled-ops.yml` | Claude |

**Gate before any spend:** a real test purchase must appear in GA4, Meta and
Pinterest. Then phase 1 is $150 on Pinterest against the Calm & Comfort Kit
only. Full reasoning in `docs/marketing-plan-2026-08.md`.

### Watch: skeleton suit SEO head tags

The Glow in the Dark Skeleton Suit's SEO description was corrected on
2026-08-18 (the maker's chart says the fabric does not stretch, so the copy no
longer claims it). Verified correct at source through BOTH the metafield
endpoint and GraphQL `product.seo.description`, but Shopify's server side page
cache was still serving the old wording in `meta description`, `og:description`
and `twitter:description` half an hour later. The body copy on the same page
response was already fresh. Re-check with:

    curl -s "https://wagvive.com/products/wagvive-glow-skeleton-suit" | grep -c "stretch knit"

Expect 0. If it still reads 3 after a day it is not a cache and needs a real
look. Mechanism and the levers that did NOT work are in
`docs/knowledge/cj-size-charts.md`.

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

Paste this verbatim. It points at documents rather than restating them, so there
is only ever one source of truth.

> Read `docs/HANDOFF.md` first, then `git pull`. CLAUDE.md is binding.
>
> **Use my REAL Chrome (the claude-in-chrome tools) for anything involving CJ,
> from the very start. Do not use the in-app browser for CJ: it is signed out,
> which makes pairing look impossible when it is not.** Confirm which browser
> you are on before you touch CJ.
>
> The store is fully built, paired and verified: 42 products live and buyable, 39
> kit variants each with their own colorway photo, every SKU paired to CJ on the
> carrier its price was modelled on. Nothing is carried over.
>
> The next work is **marketing phase 0**, which gates every dollar of paid spend:
>
> 1. **#75 measurement stack.** GA4, Meta pixel + CAPI (data sharing Maximum),
>    Google Merchant Center with free listings, Pinterest tag. Owner creates the
>    accounts; I configure and verify. Google first, since free listings are the
>    only zero-CPC channel and the 42 feed titles are already written in
>    `config/marketing/feed_health.py --titles`.
> 2. **#76a the five email automations** in Marketing › Automations. Copy is
>    written in `docs/marketing/email-flows-2026-08.md`; read
>    `docs/knowledge/shopify-messaging-custom-liquid.md` first. Watch the exit
>    condition trap: Shopify puts it on the FIRST email only.
> 3. Then the phase 0 gate: a real test purchase appearing in all three
>    analytics tools, after which phase 1 is $150 on Pinterest against the Calm &
>    Comfort Kit only.
>
> Rules: verify against the live system by re-fetching, never the write's return
> value. Never enter my credentials. Show me numbers before any write that
> changes a price, product or bundle. Tell me plainly if something turns out to
> be wrong or impossible, with the numbers behind it.
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
