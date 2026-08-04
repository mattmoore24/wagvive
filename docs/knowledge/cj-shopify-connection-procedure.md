---
name: cj-shopify-connection-procedure
description: "How to re-pair a Wagvive Shopify product to a CJ product, and why the mapping must be audited after any product change"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-02T05:02:01.684Z
---

Re-pointing a Wagvive SKU at a different CJ product (CJ account `abezff-5d` / store "Wagvive"):

1. **CJ product page → "Added Products"** button. The connect modal only searches products
   already in your CJ list, so this must happen first or the search returns nothing.
2. **Store Products → Unconnected → pick the store in "Select Store" → Sync.** Skipping this
   is the trap: CJ caches your Shopify title/price/variants, and the connect modal's
   `shopList` comes back **empty** if the cache is stale, so nothing can be paired. The
   progress dialog also silently stalls at 0% if no store was selected first.
3. **Store Products list → hover the row → Disconnect icon** to drop the old pairing.
4. Back on Unconnected: **filter the left list to one row** using the "Enter SKU/Product Name"
   box before clicking Match — the list re-renders and re-orders constantly, and a coordinate
   click will otherwise land on the wrong product.
5. Click **Match** on the store row, then **Connect** on the CJ card, turn **Automatic
   Connection off**, click one variant on each side, pick a Shipping Method, Confirm.
   Leave Automatic Connection **on** when the SKUs match exactly on both sides — it pairs
   them correctly and is far quicker than 8 manual clicks. Carriers are chosen per product
   from `config/express_check.py`, not one house default: Nail Grinder uses YunExpress
   Sensitive, Slow Feeder and Water Bowl use YunExpress Ordinary, Gloves CJPacket Sensitive.

**Audit the mapping after every product change.** On 2026-07-28 the Anti-Spill Floating Water
Bowl was found silently mapped to a cat bed (SPU `CJJJCWMY01390`) — an order would have
shipped the wrong item. The connection table is at
`https://www.cjdropshipping.com/mine/products/connection`; read each row's Store Product vs
CJ Product and confirm they describe the same thing. See [[wagvive-placeholder-product-art]]
for how to pull CJ imagery and search their catalogue.

**Browser automation notes** (learned the hard way 2026-07-30):

- Reach the page by **navigating to `/mine/products/connection`**, not the hash route
  `/my.html#/products-connection/goods` — that hash renders the 3PL "Add Service Product"
  screen instead, showing "No product yet" and looking like an empty catalogue.
- An `iframe#guid-frame` full-viewport chat overlay ("Hello, I'm Alex") swallows every click
  and **reappears after each navigation**. Remove it with
  `document.getElementById('guid-frame').remove()` before interacting. Its text is invisible
  to `document.body.innerText` because it lives in the iframe, so it can block clicks while
  looking absent.
- Coordinate clicks are unreliable here — the screenshot is scaled ~1568/1728 against the real
  viewport. Drive the DOM instead. The visible Confirm in the connect modal is a
  **`span.new-btn.confirm-btn`**, not a `<button>`; the `<button>Confirm</button>` elements on
  the page are all zero-size and inert.
- The store dropdown is an Angular widget: click `.selectShop` inside the row containing the
  Sync button, then click the `.select-option-item` matching the store handle.
- **Shipping Method is mandatory** before Confirm enables. It also pins the carrier for
  fulfilment, so pick the cheapest one inside the published delivery window — otherwise the
  margin model in `config/margin_guard.py` is priced against a carrier CJ will not use.

**The Sync button silently no-ops under automation** (2026-08-02, cost an hour). `Sync` calls
`renovation()` in `static/components/sync_store/sync_store.js`, which checks a `storeinfo`
variable held in a **closure** — set only by the dropdown widget emitting `currStoreId`.
Setting the `<select>` value (or any DOM-level dropdown fiddling) paints the right store on
screen but never reaches that closure, so `renovation()` hits its `else` branch and shows
"Please select a store first!" via `layer.msg`, which does not appear in `body.innerText`.
Symptom: clicking Sync fires **zero** backend requests and the mirror never updates. The
reliable path is to call the app's own service directly from the page:

```
angular.element(document.body).injector().get('dsp')
  .postFun('cj-platform-web/product/pullPlatformProduct', {shopId:'<store ID>'}, cb)
```

Store ID lives on the search component's scope (`vm.shopselectlist`); Wagvive `abezff-5d` is
`2607280059043535300`. A plain `fetch()` to that endpoint returns `601 not logged in` — the
auth headers are added by `dsp`, so go through the service, not raw fetch. Success is
`{code:200, message:"Congratulation! Well done!"}`; the pull then takes **2–5 minutes**.

**Pair one product at a time, and never re-click Confirm.** The connect dialog nulls
`matchitem` after a failed/duplicate Confirm, and every later attempt throws
`Cannot read properties of null (reading 'shopType')` — invisible unless you read the console.
Once that happens the page is stuck; reload before retrying. Verify before clicking Confirm:
`scope.matchitem.shopType === 'Shopify'` and every pair in `scope.arr` satisfies
`p.first.shopSku === p.last.SKU` (walk up to the scope with `$id===7`).

**Auto-match misses some products** — Talk Button returned nothing. Fall back to the right-hand
"Enter SPU/SKU/Product Name" box and search the SPU directly; Match on the left row still sets
the store side.

**Carrier lists are per-product.** Battery items (Talk Button) offer only "sensitive" lines —
no CJPacket Ordinary. Never pick a carrier by habit: run `freight_floor.resolve()` over
`/logistic/freightCalculate` and use that exact carrier, or the listing silently drops below
the floor. The Lick Bowl booked on CJPacket Ordinary ($9.19) came out at **47.1%** vs 51.0% on
LuWei Ordinary US ($7.97). Current: bottle + lick bowl = LuWei Ordinary US, talk button +
bouncy egg = CJPacket Super Pure Electricity.

**Changing a carrier after connecting**: Connected tab → filter by SPU → gear icon
(`i[class*=fromShipActionIcon]`) in the Shipping Method cell → Edit → the Ant Design combobox
options are **virtual-scrolled and zero-height**, so `document.querySelector('.ant-select-item-option')`
by text and dispatch mousedown/mouseup/click; then row **Save**, then modal **Confirm**
(`div.yes-btn`).

**The Unconnected tab over-reports.** It is served from CJ's cached sync, so a product whose
variants are all mapped keeps appearing until you re-Sync. To tell a real gap from stale
cache, open Match → Connect: if the **left "Store Product" pane is empty**, every variant is
already connected. Expect the two bundle kits to sit in Unconnected permanently — they carry
no SKUs and route through their component variants, which are connected individually.
