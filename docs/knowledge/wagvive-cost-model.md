---
name: wagvive-cost-model
description: "Per-product price-book floors (flat 50% retired 2026-08-04), what the cost model includes, and the three ways CJ freight data lies"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-05T00:23:46.468Z
---

**The flat 50% floor was retired 2026-08-04 (owner decision).** Prices come from a
per-product demand model (see [[wagvive-pricing-architecture]]); each product's floor
lives in `config/price_book.json` as `floor_margin_pct` and is enforced by
`config/margin_guard.py` (variants; per-product floors) and `config/kit_margins.py`
(bundles; 30%). **Floors must be denominated in the guard's own cost model** (selected
carrier + tax-inclusive fee): recalibrate with `config/calibrate_floors.py --apply`
after any deliberate repricing, or the guard false-alarms on model mismatch, not drift.
Cost model lives in `config/pricing.py`:

    landed = (goods x (1 + duty)) + freight, all x (1 + RETURNS_RATE)
    cost   = landed + PCT x (1 + SALES_TAX_AVG) x price + $0.30

- duty 20% China-origin, 0% US-warehouse (supplier already imported it)
- `SALES_TAX_AVG = 0.07` — sales tax itself is a pass-through and is NOT a margin cost,
  but Shopify's 2.9% is charged on the whole order *including* tax, and that part is ours
- `RETURNS_RATE = 0.03` — 30-day returns; we cover return shipping on faulty/wrong items
- Shipping revenue ($5.95, free over $60) is deliberately excluded, so it is upside

**Three ways CJ's freight data misleads — all now handled in `config/freight_floor.py`:**

1. **A $0.00 quote is missing data, never free carriage.** The old US-warehouse Furniture
   Cover returned $0.00 on UPS, FedEx *and* USPS at 1, 5 and 20 units. Taken at face value it
   looked like 60.7% margin; its real margin was 41.7%. `resolve()` substitutes
   `US_DOMESTIC_FREIGHT_FALLBACK` ($11) and flags the result as estimated.
   **This is systemic to CJ's US-warehouse (`CJBQ…`) listings, not one bad SKU** — all three
   US-warehouse blankets in Pet Blankets & Quilts showed $0.00 freight *and* exactly 50 units
   of placeholder stock. Prefer China-origin, where freight is genuinely quoted. That is why
   the cover was replaced on 2026-07-31 with `CJYD2251860` (China, real LuWei Ordinary US
   quotes, 5–9k stock per size), and the old `CJBQ3005963` archived and disconnected.
2. **An empty combined quote means the kit ships as separate parcels.** A consolidated quote
   only exists if ONE carrier serves every component. The Grooming kit fails that because the
   Slicker Brush has exactly one carrier option, so CJ splits it — real freight $28.38, not
   the consolidated figure. That put the kit at **32.8%** while it was priced $79; it is now
   $109. Never substitute an estimate for an empty combined quote — sum the individual legs.
3. **The cheapest carrier is often outside the delivery promise.** Filter to
   `MAX_DAYS = 12`, matching the published "5-12 business days".

**Consolidated freight is what funds a discount.** Three toys ship together for $7.17 against
$16.20 bought separately, so the "any 3 toys, 15% off" automatic discount still returns 64%
margin — the freight saving more than pays for the discount. The same maths is why the New
Puppy Kit works ($13.37 consolidated, one parcel) and why the Grooming kit is dear ($28.38,
four parcels, no single carrier serves all four). **Always check the consolidated quote before
pricing any multi-item offer**; per-item freight will tell you it is unaffordable when it is not.

**A discount can breach the floor.** Price toys so the *post-discount* price still clears the
product's price-book floor, not the sticker price. Check with `config/margin_guard.py` after
any discount change.

**Pricing to headroom, not the knife edge:** `margin_guard.py --headroom` prices against a
stress case (goods +10%, freight +15%) so a routine CJ move does not breach the floor. Run
`--headroom --apply`, then `config/normalise_prices.py`, which levels colour-driven price
differences up within a size band (White ships dearer than Pink/Blue/Grey on the Water Bowl,
and colour-varying prices read as a bug to shoppers).

Kit compare-at prices must equal the true component retail total, or the saving is a false
claim — and the storefront now *computes* the kit saving from live prices
(`snippets/kit-callout.liquid`, driven by a `custom.kit` product-reference metafield), so a
compare-at that drifts will immediately misstate the discount on seven product pages.

**Never hardcode a price or a saving into copy.** Six product descriptions carried a
"Part of the … Kit" paragraph quoting $95/$79/save $16 and $138/$89/save $49 long after the
real figures became $136/$109/$27 and $108/$79/$29 — and the Comfort version still named the
cooling mat and calming bed, both archived months earlier. All six were stripped on
2026-08-01 in favour of the computed callout.

**Changing a variant breaks any kit that contains it.** Replacing the wipes variants removed a
component from the Grooming Essentials Kit, and Shopify silently moved the kit to **DRAFT** —
invisible on the storefront, discovered only days later. **After touching any variant, check
every kit that uses it is still ACTIVE.** Note (2026-08-04): the old belief that bundle
components cannot be swapped via API is **wrong** — `productBundleUpdate` accepts a full
replacement components array; all six kits were recomposed in place by `config/apply_kits.py`
with handles, links and history preserved. Expect transient HTTP 409 ("being modified") on the
product for a few seconds after each bundle operation; retry, don't abort. The rebuild-and
-retire path (`rebuild_kits.py`) is only needed if an update is rejected outright.

**Rebuilding a kit is four steps, not one.** Shopify keeps a handle reserved even after the
product is archived, so the outgoing kit must be renamed to `<handle>-retired` *before* the
replacement is created or the new kit lands on `senior-dog-kit-1`. Then: `make_kit_covers.py`
(bundles are created with no media), `link_kits.py` (component `custom.kit` metafields still
point at the archived kit, and a component dropped from a kit keeps a stale link unless it is
explicitly deleted), and delete the collection's stale collects — an archived product stays in
`collects.json` and the collection reports duplicate titles. `rebuild_kits.py` now takes kit
titles as arguments; running it bare rebuilds every kit and needlessly re-handles the ones that
did not change.

**Bundles are created with no images at all.** All four kits shipped with a blank placeholder
until `config/make_kit_covers.py` composed a 2x2 grid of their components. Run it after any
kit rebuild — and run it *after* fixing component covers, or it bakes in whatever bad image
the component was leading with.

**Never take CJ's first image as the cover.** Supplier image 0 is frequently a dimensions
diagram or a marketing panel, and grooming products are largely photographed on cats. Build a
contact sheet (`config/branding/audit/`) and hand-pick. `config/fix_covers.py` holds the
chosen indices per SKU.

**Two traps when adding a product:**

- `margin_guard.py` derives SPUs from the SKUs live on the store (SKU[:11]). It used to read
  a checked-in matrix, which meant every newly added product came back "no CJ record" and was
  silently skipped by the floor check. If you see UNRESOLVED rows, that is the bug returning.
- Shopify creates new variants stocked at **`Shop location`**, not `cjdropshipping`. CJ pushes
  only to its own location, so a new product sits at 0 forever until you POST
  `inventory_levels/connect.json` for the CJ location and delete the other level.

See [[cj-inventory-sync-model]] and [[wagvive-sourcing-rules]].
