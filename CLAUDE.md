# Wagvive — operating rules

Dog-products dropshipping business: Shopify storefront (wagvive.com) + CJ
Dropshipping fulfilment. This file is read automatically at the start of every
Claude Code session, on any device. Everything here was learned the hard way —
treat it as binding, not advisory.

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
- `cjdropshipping` (113382293793) — a THIRD_PARTY fulfilment-service location

Variants are `fulfillment_service: manual` (created via Admin API, and REST
silently ignores attempts to change this). **Shopify will not sell a manual
variant from a service location**, so stock written there is inert. Worse,
`inventory_quantity` SUMS across locations, so stock in both places reads double.

Rules:
- Stock lives at `Shop location` only. `config/fix_locations.py --apply` strips
  service-location levels and mirrors CJ's figures to the canonical one.
- `config/sync_inventory.py --apply` copies CJ stock in. **Without `--apply` it
  is report-only** — a silent no-op that has been mistaken for success.
- CJ's webhook writes to its own location and may recreate the double count at
  any time. That is why the scheduled job re-runs `fix_locations.py`.
- CJ's true shippable quantity is `inventory + factoryInventory` summed over all
  stock rows — NOT `totalInventoryNum`, which undercounts.
- **Verify availability with `/products/<handle>.js` and check `available`**, not
  admin inventory numbers. A catalogue once showed thousands in stock while every
  variant was unbuyable.

## Shopify API gotchas

- REST is capped at **2 calls/second** and answers 429. Any script that walks the
  catalogue needs `time.sleep(0.55)` per call plus backoff. Never pipe a
  long-running script through `tail` — it masks the exit code and hides
  tracebacks.
- Collection product order needs the GraphQL `collectionReorderProducts`; the
  REST collect approach 422s.
- Auto-managed policies reject `shopPolicyUpdate`; disable with
  `privacyFeaturesDisable(featuresToDisable:[PRIVACY_POLICY])` first.
- Shopify's CDN serves **mixed stale/fresh renders for minutes** after a theme or
  policy write. Verify a change by re-fetching with a unique `?nocache=` param,
  and check all the fields you care about in the SAME response.

## Things that have NO API (must be done in a browser)

- **CJ product pairing.** CJ's Angular app only. The Sync button validates a
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
  sync_inventory.py fix_locations.py            inventory correctness
  cj_api.py scout*.py                           CJ sourcing
  build_email_templates.py email-templates/     notification emails
  branding/                                     logos, kit covers, email assets
.github/workflows/                              scheduled ops
```

Secrets live in `config/shopify.env` and `config/cj.env` — gitignored, never
committed. Copy the `.example` files to create them.

## Before saying something is done

Verify against the live system, not the tool's return value: re-fetch the object,
load the storefront, check the rendered HTML. Several "successful" writes in this
project's history did nothing.
