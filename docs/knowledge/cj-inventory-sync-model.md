---
name: cj-inventory-sync-model
description: "CJ syncs Wagvive inventory natively by webhook — never write Shopify stock by script, and watch the two-location trap that doubles every count"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-01T13:59:34.315Z
---

**CJ already syncs inventory. Do not write Shopify stock from a script.** CJ pushes real
counts over a webhook whenever stock moves. Verify it per product at Store Products →
row's `...` menu → **Inventory Sync Log**, which lists every variant with Store SKU, CJ SKU,
Sync Source (`Webhook` / `Manual Setting`), Sync Status and the reason for failures. That log
is the only place that shows variant-level mapping *correctness* — the Connected/Unconnected
tabs only show whether a mapping exists, not whether it points at the right CJ variant.

**The two-location trap — and CJ's stock is INERT.** The store has two locations:
`cjdropshipping` (113382293793) and `Shop location` (113363058977).

`cjdropshipping` is a **THIRD_PARTY fulfilment-service location**. Our variants are
`fulfillment_service: manual`, because they were created through the Admin API rather than
imported by the CJ app — and REST **silently ignores** attempts to set `fulfillment_service`
on a variant (the PUT returns 200 with the old value). Shopify will not sell a manual variant
from a service location. So:

- **Availability is governed by `Shop location` only.** CJ's webhook faithfully writes to its
  own location, and that stock does nothing for the storefront.
- On 2026-07-31 I moved all stock to the CJ location believing `Shop location` held phantom
  units. It did not — it was the sellable stock. That made all 48 variants
  `available: false` while displaying thousands in stock. Caught only by loading the
  storefront and seeing struck-through variant swatches. **Always verify with
  `/products/<handle>.js` and check `available`, not just inventory numbers.**
- Corrected 2026-08-01: `config/fix_locations.py` now treats `Shop location` as canonical and
  strips levels at the service location, and `config/sync_inventory.py` is a **writer** again,
  copying CJ's figures into `Shop location`. Without it, a sold-out CJ item stays buyable.
- `inventory_quantity` SUMS across locations, so stock must live in exactly one of them or
  every figure reads double.

**CJ's stock number is not `totalInventoryNum`.** That field counts only the warehouse row.
CJ also ships from factory stock and its webhook sends the **sum of every `stock[]` entry**
(`inventory` + `factoryInventory`). Slicker Brush: warehouse 2097 + factory 11408 = 13505,
which is exactly what CJ pushed. A checker that reads `totalInventoryNum` will report false
drift. `config/sync_inventory.py` is now read-only and does this correctly.

**The first-variant mis-mapping bug.** Every product's original variant existed before SKUs
were assigned, so CJ matched it **positionally** and never re-matched after SKUs were added.
Four products were wired to the wrong CJ item — Gloves Dark Brown → Classic, Wipes
Ear&Teeth($44) → Ear-only($30), Water Bowl Pink/1.5L → White, Slow Feeder Green → wrong
colour — and all six affected variants had a failed sync reading *"Store variant sku is empty"*.
Fixed by disconnecting each product and reconnecting with **Automatic Connection on**, which
pairs strictly by exact SKU. See [[cj-shopify-connection-procedure]] for the UI mechanics.

**Store-level kill switch (found 2026-08-04).** CJ's authorization page
(my.html#/authorize/Shopify) -> Inventory Sync column -> **Setting** link opens a
per-store "Sync Settings" modal mapping the cjdropshipping location to a sync
mode. Set to **"Not Sync"**: CJ stops writing stock for ALL products at once —
no per-connection editing needed (the per-row "Inventory Management" label in
the connection list is not clickable anyway). The three switches in that table
row are Email Permission / Auto-Sync (Order&Product) / Delivery Profile — they
are NOT the inventory toggle; leave them ON or order flow breaks. After this
change sync_inventory.py is the only stock writer and the double-count can
never recur.
