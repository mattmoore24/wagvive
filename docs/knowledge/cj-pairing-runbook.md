# CJ pairing runbook — step by step, in the owner's real Chrome

Companion to `cj-shopify-connection-procedure.md`, which explains *why* each step
exists. This is the ordered checklist. Follow it exactly; nearly every step here
exists because skipping it cost an hour at least once.

## Before you touch anything

**Use the owner's REAL Chrome — the `claude-in-chrome` tools.** Not the in-app
browser. The CJ session lives in the real browser; the in-app one is signed out,
so pairing looks impossible there and is not. Confirm which browser you are on
before you start:

- `mcp__claude-in-chrome__list_connected_browsers` then `select_browser`
- Load `https://www.cjdropshipping.com/mine/products/connection` and confirm you
  see the connection table, not a login screen.

If Chrome is not connected, say so and stop. Do not fall back to the in-app
browser and do not ask for credentials — the owner never hands those over.

CJ account is `abezff-5d`, store "Wagvive", shopId `2607280059043535300`.

## 0. Know what you are pairing, and on which carrier

Never pick a carrier by habit. Battery and liquid items only offer "sensitive"
lines, and the wrong choice silently drops the product under its margin floor:
the Lick Bowl on CJPacket Ordinary came out at 47.1% against 51.0% on LuWei
Ordinary US. Get the answer first:

```
python -c "import sys; sys.path.insert(0,'config'); import freight_floor; print(freight_floor.resolve.__doc__)"
```

then resolve the specific SKU and use exactly that carrier. If freight comes back
`$0.00` that is MISSING DATA, never free carriage — stop and investigate.

## 1. Navigate correctly

Go to `https://www.cjdropshipping.com/mine/products/connection`.

Do **not** use the hash route `/my.html#/products-connection/goods`. It renders
the 3PL "Add Service Product" screen, shows "No product yet", and looks exactly
like an empty catalogue.

## 2. Kill the chat overlay, every time

An `iframe#guid-frame` chat overlay ("Hello, I'm Alex") covers the viewport and
swallows every click. It **reappears after each navigation**, and its text is
invisible to `document.body.innerText`, so it blocks clicks while appearing
absent.

```js
document.getElementById('guid-frame')?.remove()
```

Re-run it after every navigation.

## 3. Sync the store cache FIRST

The connect modal's `shopList` comes back **empty** if CJ's cache of your Shopify
catalogue is stale, so a brand-new product cannot be paired until you sync.

**The Sync button silently no-ops under automation.** It reads a `storeinfo`
variable held in a JS closure that only the dropdown widget can set. DOM-level
dropdown fiddling paints the right store on screen but never reaches the closure,
so `renovation()` takes its `else` branch and shows "Please select a store
first!" through `layer.msg` — which does not appear in `body.innerText`. The
symptom is zero backend requests and a mirror that never updates.

Call the app's own service instead:

```js
angular.element(document.body).injector().get('dsp')
  .postFun('cj-platform-web/product/pullPlatformProduct',
           {shopId:'2607280059043535300'},
           r => console.log(JSON.stringify(r)))
```

Success is `{code:200, message:"Congratulation! Well done!"}`. A plain `fetch()`
to that endpoint returns `601 not logged in` — the auth headers are added by
`dsp`, so go through the service, never raw fetch.

**Then wait 2 to 5 minutes.** The pull is asynchronous. Do not proceed until the
new product appears in Unconnected.

## 4. Pair ONE product, and verify before confirming

Filter the left list to a single row using the "Enter SKU/Product Name" box
before clicking Match. The list re-renders and re-orders constantly, so a
coordinate click lands on the wrong product.

Coordinate clicks are unreliable generally here — the screenshot is scaled about
1568/1728 against the real viewport. Drive the DOM.

Then: **Match** on the store row → **Connect** on the CJ card → pick a Shipping
Method (mandatory; Confirm stays disabled without it) → **Confirm**.

The visible Confirm is a `span.new-btn.confirm-btn`. The `<button>Confirm</button>`
elements on the page are all zero-size and inert.

**Leave Automatic Connection ON when the SKUs match exactly on both sides.** It
pairs correctly and beats eight manual clicks. Turn it off only when they differ.

**Verify before you click Confirm.** Walk up to the scope with `$id===7` and check:

- `scope.matchitem.shopType === 'Shopify'`
- every pair in `scope.arr` satisfies `p.first.shopSku === p.last.SKU`

**Never re-click Confirm.** A failed or duplicate Confirm nulls `matchitem`, and
every later attempt throws `Cannot read properties of null (reading 'shopType')`
— invisible unless you are reading the console. Once that happens the page is
stuck: reload before retrying.

If auto-match returns nothing (it missed the Talk Button), use the right-hand
"Enter SPU/SKU/Product Name" box and search the SPU directly. Match on the left
row still sets the store side.

## 5. Leave inventory sync OFF

In the connect dialog, leave "Sync CJ's Inventory Levels" **off**. Stock is
written by `config/sync_inventory.py` into `Shop location`; CJ writing to its own
legacy location creates the double-count described in CLAUDE.md. The store-level
"Not Sync" switch is the real guarantee, but leave this off for cleanliness.

## 6. Audit the result, do not trust the dialog

Read the connection table at `/mine/products/connection` and confirm each row's
Store Product and CJ Product describe the same thing. On 2026-07-28 the
Anti-Spill Floating Water Bowl was found silently mapped to a **cat bed** — an
order would have shipped the wrong item.

**The Unconnected tab over-reports.** It is served from CJ's cached sync, so a
fully-mapped product keeps appearing until you re-Sync. To tell a real gap from
stale cache: open Match → Connect, and if the left "Store Product" pane is empty,
every variant is already connected.

**The six bundle kits will sit in Unconnected permanently.** They carry no SKUs
and route through their component variants, which are connected individually.
That is correct and is not a gap to fix.

## 7. Confirm from outside CJ

```
python config/audit_cj_connections.py
```

Every SKU must resolve to a live CJ variant, stock must sit only at
`Shop location`, and every variant must be buyable on the storefront. This is the
check that does not depend on CJ's own UI telling the truth.

## Changing a carrier after connecting

Connected tab → filter by SPU → gear icon (`i[class*=fromShipActionIcon]`) in the
Shipping Method cell → Edit. The Ant Design combobox options are virtual-scrolled
and zero-height, so select by text and dispatch mousedown/mouseup/click rather
than clicking coordinates. Then row **Save**, then modal **Confirm** (`div.yes-btn`).
