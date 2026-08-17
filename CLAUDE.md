# Wagvive — operating rules

Dog-products dropshipping business: Shopify storefront (wagvive.com) + CJ
Dropshipping fulfilment. This file is read automatically at the start of every
Claude Code session, on any device. Everything here was learned the hard way —
treat it as binding, not advisory.

## FIRST ACTION in every session

Read `docs/HANDOFF.md`. It carries the current state, open tasks and what the
previous session (possibly on another device) just did — it is the conversation
continuity across devices. Before the user switches devices or a work session
ends, UPDATE it, commit, and push. If working on the home PC, `git pull` first:
another device may have moved things.

## Non-negotiables

1. **50% gross margin floor on every variant and every kit**, after ALL costs:
   product + shipping + duties + payment fees + returns allowance. It must hold
   even when CJ prices drift. `config/margin_guard.py` is the enforcement.
2. **Never enter the user's credentials anywhere.** Logins, payment details and
   identity steps are the user's to perform. Flag and hand off.
3. **Confirm before spending money or taking irreversible actions.**
4. **Plain language in all customer-facing copy.** No em/en dashes anywhere on
   the site (`config/dedash.py`), and no hyphenated day ranges — write
   "5 to 12 business days", which is the promise used site-wide and in emails.

## Money model

`config/pricing.py` is the single source of truth. `landed()` = product cost ×
(1 + duty) + freight, all × (1 + returns rate). Margin subtracts payment fees
and a flat allowance.

**Freight is where this goes wrong.** Always resolve it through
`config/freight_floor.py::resolve()`, which picks the cheapest carrier inside the
12-business-day promise. A CJ freight quote of **$0.00 means missing data, never
free carriage** — taking it literally once made an item look 60% margin when it
was under floor. The carrier chosen at CJ pairing time must match the carrier the
price was modelled on, or the margin is fiction.

Colour variants of one product are priced identically (levelled up to the most
expensive variant's requirement), so the storefront never shows odd per-colour
pricing.

## Inventory: the two-location trap

Two Shopify locations exist:
- `Shop location` (113363058977) — **canonical, the only one that can sell**
- `cjdropshipping` (113382293793) — a LEGACY fulfilment-service location.
  GraphQL's `locations` connection does not even return it; REST flags it
  `legacy: true`.

Variants are `fulfillment_service: manual` (created via Admin API, and REST
silently ignores attempts to change this). **Shopify will not sell a manual
variant from a service location**, so stock written there is inert. Worse,
`inventory_quantity` SUMS across locations, so stock in both places reads double.

**Why we cannot just let CJ's webhook do it.** CJ's webhook works fine — it
writes accurate stock to its own location, which cannot sell. Making that the
sellable stock would require the variants to be owned by the CJ fulfilment
service, which is only set when the CJ app creates the products. There is no
supported API to reassign fulfilment service on existing variants. Rebuilding 42
products through CJ's importer would discard every custom title, description,
Runway image and kit structure. So: CJ owns fulfilment (it reads orders and
writes tracking back regardless of location — order #1001 fulfilled "from Shop
location"), and `sync_inventory.py` owns the numbers. That split is deliberate,
not a workaround left half-done.

**CJ inventory writing is disabled at the STORE level (2026-08-04).** CJ's
authorization page (my.html#/authorize/Shopify → Inventory Sync → Setting) has a
per-store Sync Settings modal; `cjdropshipping` location is set to **"Not
Sync"**. That one switch stops CJ writing stock for every product, current and
future — per-connection toggles were never needed. The three row switches next
to it (Email Permission, Auto-Sync Order&Product, Delivery Profile) are
UNRELATED and must stay ON; the sync-settings modal is reached only via the
"Setting" link. `sync_inventory.py` (6-hourly via GitHub Actions) is now the
single writer of stock. When pairing new products the connect dialog's "Sync
CJ's Inventory Levels" option should still be left OFF for cleanliness, but the
store-level Not Sync is the real guarantee.

**Duplicate-source check:** before creating any product, verify the CJ SPU is
not already used by an existing product — a duplicate slipped through once
because the audit compared titles, not source SKUs. The margin/catalog audits
now must compare `sku[:11]` across the catalogue.

Rules:
- Stock lives at `Shop location` only. `config/fix_locations.py --apply` strips
  service-location levels and mirrors CJ's figures to the canonical one.
- `config/sync_inventory.py --apply` copies CJ stock in. **Without `--apply` it
  is report-only** — a silent no-op that has been mistaken for success.
- CJ's webhook writes to its own location and may recreate the double count at
  any time. That is why the scheduled job re-runs `fix_locations.py`.
- **An empty `stock` array is NOT a shipping block.** For two days this repo
  believed only a concrete `stockId` proved CJ could ship, and zeroed ten
  healthy variants across five products. CJ's own UI disproved it: the Bouncy
  Egg Squeaker shows "Inventory: 46587 (CJ: 0, Factory: 46587)", carrier "LuWei
  Ordinary US · Available", 1 to 3 day processing. Those products also return
  status 3, carry 48 to 86 other sellers' listings, and quote 27 carriers each;
  CJ flags no line of order #1002 abnormal and its Abnormal Orders tab reads 0.
  `cj_stock()` falls back to `totalInventoryNum` when there is no stock record,
  which is the number CJ's product page displays.
- **"How many units exist" and "can this be fulfilled" are different questions.**
  Answer the second by asking CJ for a CARRIER, never by reading a stock field.
  `config/guard_unshippable.py` quotes freight per variant and requires one
  option inside the 12-business-day promise; it runs 3-hourly and asserts on the
  live storefront. All 145 variants currently pass.
- **An EMPTY answer from CJ is not evidence of anything** — retry it. One run
  came back empty for seven healthy SKUs at once; acting on that would have
  zeroed live kit components. Treat unanswerable as UNKNOWN, never as a finding.
- **Never read CJ stock by hand. Call `sync_inventory.cj_stock(sku)`.** CJ returns
  TWO different row shapes and the right answer depends on which you got. Some
  SKUs carry nested per-warehouse entries, where the quantity is
  `inventory + factoryInventory` summed over all rows and `totalInventoryNum`
  undercounts (the Slicker Brush reads 2097 that way against a real 13505).
  Others carry only `totalInventoryNum`, with `inventory` and `factoryInventory`
  **null**, and summing those two returns 0. Getting this wrong publishes a
  product with every variant unbuyable, which happened to the Dental Chew Stick
  on 2026-08-08 and was caught only by re-fetching. `sync_inventory.cj_stock`
  handles both; nothing else should try.
- **Kits hold NO stock of their own, and that is correct.** A bundle parent has
  `inventoryItem.tracked: true` just like a single, so tracked proves nothing.
  What identifies a healthy bundle is `requiresComponents: true` plus an
  inventory level that exists but carries **no `available` quantity**; Shopify
  derives `sellableOnlineQuantity` from the components. `sync_inventory.py` only
  walks SKU-carrying variants, so it never touches kits and its "all in step"
  verdict says nothing about them. `config/verify_kit_inventory.py` is the check
  that does: it recomputes `min(component available // qty needed)` and requires
  it to equal Shopify's derived figure for all 39 kit variants.
- **Verify availability with `/products/<handle>.js` and check `available`**, not
  admin inventory numbers. A catalogue once showed thousands in stock while every
  variant was unbuyable. `inventory_quantity` in the products.json payload also
  LAGS: it read 0 immediately after a correct write. `inventory_levels` is the
  admin-side truth, the storefront is the real one.
- **A newly created product is published to Point of Sale ONLY.** Admin API
  creation does not add it to Online Store, so it can be ACTIVE, stocked, imaged
  and in a collection and still 404 on the storefront. Copy the channel set from
  a product known to be live (`publishablePublish`), as
  `config/add_dental_chew.py` does.

## Shopify API gotchas

- REST is capped at **2 calls/second** and answers 429. Any script that walks the
  catalogue needs `time.sleep(0.55)` per call plus backoff. Never pipe a
  long-running script through `tail` — it masks the exit code and hides
  tracebacks.
- Collection product order needs the GraphQL `collectionReorderProducts`; the
  REST collect approach 422s.
- **`product.bundleComponents` is STALE after a kit rebuild** and stayed wrong
  for at least 50 minutes, naming components the kit no longer had. A bundle's
  real composition is `variant.productVariantComponents`. Anything that reads
  the product-level field will assert the OLD contents and may write them back.
- **Kit art scripts are idempotent BY FILENAME**, so reshot art under the same
  name is skipped: delete the old image first. But then do NOT let anything
  replace "position 1" blindly — with the cover gone, position 1 is a component
  still, and `apply_kit_covers.py` ate two of them that way. It now matches the
  cover by alt text.
- Auto-managed policies reject `shopPolicyUpdate`; disable with
  `privacyFeaturesDisable(featuresToDisable:[PRIVACY_POLICY])` first.
- Shopify's CDN serves **mixed stale/fresh renders for minutes** after a theme or
  policy write. Verify a change by re-fetching with a unique `?nocache=` param,
  and check all the fields you care about in the SAME response.

## Things that have NO API (must be done in a browser)

- **CJ product pairing.** CJ's Angular app only, and **it must be the owner's
  REAL Chrome (the `claude-in-chrome` tools), never the in-app browser.** The CJ
  session lives in the real browser; the in-app browser is signed out, so pairing
  looks impossible there and is not. This has now cost time twice, once by
  concluding pairing had to be handed to the owner when it did not. Pairing is
  browser-only, NOT owner-only: Claude can do it, in the owner's Chrome, without
  ever touching credentials because the session is already signed in.
  The Sync button validates a
  store held in a JS closure that DOM manipulation cannot reach; call the app's
  own service instead:
  `angular.element(document.body).injector().get('dsp').postFun('cj-platform-web/product/pullPlatformProduct', {shopId:'2607280059043535300'}, cb)`.
  Sync takes 2–10 minutes. Pair one product at a time, verify
  `matchitem.shopType === 'Shopify'` and that every pair satisfies
  `first.shopSku === last.SKU` BEFORE confirming — a failed confirm nulls
  `matchitem` and every later attempt throws until the page is reloaded.
- **Notification email templates.** No API at all. Edit at Settings →
  Notifications. Templates are generated from `config/build_email_templates.py`
  — change the shared shell there and regenerate, never hand-edit the 18 files.
  Shopify rejects saves missing required drops (`{{ custom_message }}` on
  invoices and contact-customer, `{{ url }}` on invites/resets/abandoned
  checkout, `{{ amount }}` on refunds).
- **Shopify admin settings screens** do not render in a background browser tab —
  the React route never mounts, so automation sees an empty page. These need the
  user to foreground the tab.

## Imagery

House style: every product on the same cream (#F7F2E9) background, consistent
framing. Generated with Runway (`nano-banana` for most, `nano-banana-pro` when
label text must survive).

Pipeline: shoot a **master** first, then **recolour the approved master** for
each variant so pose stays locked. Describe the product from LOOKING at the CJ
reference — the model invents plausible-but-wrong products otherwise (it produced
a five-finger glove for an oval mitt, a quilted sofa cover for a plush throw).
Every prompt must ban invented props, stands, packaging and embossed logos, and
**every output must be eyeballed against the CJ reference** before upload.

Wire `variant.image_id` on every variant so swatches swap photos; single-variant
products need it too, for the cart thumbnail.

## Brand

Cream `#F7F2E9` / page `#EFE7DA` / ink `#3A3026`. Support address is
**hello@wagvive.com** (Shopify domain forwarding into a dedicated Gmail; it is
the verified notification sender and is DKIM-signed). It must be the only email
address appearing anywhere customer-facing.

## Layout of this repo

```
config/
  pricing.py freight_floor.py margin_guard.py   money model + enforcement
  price_book.json market_bands.py               per-product prices and floors
  demand_model.py optimise_prices.py            how those prices were derived
  sync_inventory.py fix_locations.py            inventory correctness
  cj_api.py scout*.py                           CJ sourcing

  kit_colorways.py                              KIT SOURCE OF TRUTH: the Size +
                                                Colorway design. Edit this, then
                                                validate, then rebuild.
  validate_colorways.py                         proves every colour/size in it
                                                resolves to a live buyable variant
  rebuild_kits.py                               applies it (--reprice-only exists
                                                because bundle pricing overrides)
  verify_kit_variants.py                        checks all 39 kit variants by
                                                component IDENTITY, not count
  apply_kit_covers.py                           kit cover art (one per kit)
  apply_colorway_covers.py                      per-colorway covers + variant
                                                image wiring; run with no flags
                                                to list what is still unshot
  make_kit_covers.py                            OLD grid fallback. Never --force.

  audit_kits.py audit_cj_connections.py         the two standing audits
  verify_kit_callout.py                         component pages name their kits
  replace_product_image.py match_framing.py     swap one photo, keep framing
                                                and variant wiring
  remove_wipes.py                               worked example of retiring a SKU
                                                everywhere it is referenced

  build_email_templates.py email-templates/     notification emails
  branding/kit-covers/flatlay/                  one cover per kit
  branding/kit-covers/colorway/                 <handle>__<Colorway>.jpg
  branding/retouched/                           photos fixed by hand
  theme-work/ theme-backup/                     snippets we own, and rollbacks
docs/HANDOFF.md                                 READ FIRST. Current state.
docs/knowledge/                                 hard-won platform gotchas
docs/qa/                                        audit logs, newest wins
.github/workflows/                              scheduled ops
```

Run any audit or verify script with no arguments to see what it checks; they all
print a plain-English report and exit non-zero on a real problem.

Secrets live in `config/shopify.env` and `config/cj.env` — gitignored, never
committed. Copy the `.example` files to create them.

## Before saying something is done

Verify against the live system, not the tool's return value: re-fetch the object,
load the storefront, check the rendered HTML. Several "successful" writes in this
project's history did nothing.
