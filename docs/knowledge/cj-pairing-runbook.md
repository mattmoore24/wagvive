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

A **cookie consent panel** may open and flood the DOM, which makes label
scraping return cookie names instead of buttons. Dismiss it with the
privacy-preserving option (`Reject All`) before anything else.

CJ may also throw a **bot-verification interstitial** that bounces to a login
page with credentials prefilled. Stop there. Completing a CAPTCHA or submitting
that login is the owner's to do, never Claude's.

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

## 1. Navigate correctly. CJ NOW RUNS TWO APPS AND ONLY ONE CAN PAIR.

Corrected 2026-08-18 after this cost a session.

`https://www.cjdropshipping.com/mine/products/connection` is now a **React**
rebuild. It shows the Connected table and it is fine for *reading* what is
already paired, but **there is no `angular` object on it**, so every technique
below (the `dsp` sync call, the `$id===7` scope checks) throws or silently does
nothing. Testing for Angular there and concluding "the runbook is obsolete" is
the wrong conclusion, and I drew it once.

**Pairing still happens in the OLD Angular app.** Get there by clicking the
**Unconnected** tab, which routes to:

```
https://www.cjdropshipping.com/my.html#/products-connection/pending-connection
```

Confirm you are in the right app before doing anything else:

```js
typeof angular !== 'undefined'      // must be true
angular.element(document.body).injector().has('dsp')   // must be true
```

If `angular` is undefined you are on the React page. Click Unconnected.

Do **not** use the hash route `/my.html#/products-connection/goods`. It renders
the 3PL "Add Service Product" screen, shows "No product yet", and looks exactly
like an empty catalogue. The working hash route is `pending-connection`.

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

**The two search boxes bind to different scope variables, and only one is
guessable.** Left is `searchinfoshop` + `searchshopcommodity()`; right is
**`searchinfostr`**. Guessing `souresearchinfo` for the right-hand box burns
time: setting it and calling `search()` silently re-pages the CJ list with
unrelated products, which looks like a failed search rather than a wrong
binding. Set the model through ngModel so the binding actually updates, then
click the Search button next to that input:

```js
const inp = document.querySelector('input[ng-model="searchinfostr"]');
const m = angular.element(inp).controller('ngModel');
m.$setViewValue('CJGY2091358'); m.$render();
```

The two lists are `shop` (left, your store products) and **`shop2`** (right, CJ
products). Confirm `shop2[0].sku` is the SPU you intended before connecting.

Coordinate clicking these inputs does not work even with the overlay gone: a
triple-click lands on the column heading. Drive the DOM.

## 4b. THE EXACT WORKING SEQUENCE, verified 2026-08-18

Every step below was run end to end against the Glow in the Dark Skeleton Suit
(SPU CJGD2143164, 4 variants) and it paired first time. Drive the DOM and the
scope; do not coordinate-click.

```js
// helper: the scope that owns the pairing UI
function s7(){let f=null;document.querySelectorAll('*').forEach(el=>{
  const s=angular.element(el).scope&&angular.element(el).scope();
  if(s&&s.$id===7&&!f)f=s;});return f;}
```

1. **Filter the left list to ONE row.** Set through `$apply` or the digest never
   runs:
   ```js
   const sc=s7(); sc.$apply(()=>{sc.searchinfoshop='Glow in the Dark';});
   sc.searchshopcommodity();
   ```
   Confirm `sc.shop.length === 1` before continuing.

2. **Click Match** (`button.newMediaMatch`, the one whose text is exactly
   "Match"). Then check `sc.matchitem.shopType === 'Shopify'` and that
   `sc.shop2[0].sku` is the SPU you intended.

3. **Click the FIRST Connect button.** The Connect buttons map 1:1 onto `shop2`,
   so index 0 is `shop2[0]`. `sc.arr` then fills with one entry per variant.

4. **THE SHIPPING SELECT IS THE ONLY REAL TRAP LEFT.** It is
   `ng-options="item as showLogisticName(item.nameEn) for item in wuliulist"`
   with `ng-change="getwuliuway(wuliuway)"`, so its option values are Angular
   object hashes like `object:389`. Setting `select.value`, dispatching
   `change`, or calling `$setViewValue` on the ngModel controller ALL silently
   fail: the select stays on "Please select" and Confirm stays `disabledBtn`.
   Set the model object on the select's OWN scope and call the change handler:
   ```js
   const sel=[...document.querySelectorAll('select')]
     .find(s=>s.getAttribute('ng-model')==='wuliuway');
   const ss=angular.element(sel).scope();
   const carrier=ss.wuliulist.find(x=>x.nameEn.trim()==='CJPacket Super Pure Electricity');
   ss.$apply(()=>{ ss.wuliuway=carrier; ss.getwuliuway(carrier); });
   ```
   Use the carrier `freight_floor.resolve()` picked for THAT SKU, matched on
   `nameEn` exactly. Confirm goes from `new-btn confirm-btn disabledBtn` to
   `new-btn confirm-btn` once it takes.

5. **Verify, then Confirm exactly once.**
   ```js
   const ok = sc.matchitem.shopType==='Shopify' &&
     sc.arr.length>0 && sc.arr.every(p=>p.first.shopSku===p.last.SKU);
   if(ok) document.querySelector('span.new-btn.confirm-btn:not(.disabledBtn)').click();
   ```

6. **Verify it landed** by re-searching the same name in the left list. An empty
   result (`storeProTotalNum === 0`) means it moved to Connected. Do not trust
   a toast; there often is not one.

Repeat from step 1 for the next product. Between products, re-read the scope
with `s7()`; the old reference goes stale after a digest.

## 5. Leave inventory sync OFF

In the connect dialog, leave "Sync CJ's Inventory Levels" **off**. Stock is
written by `config/sync_inventory.py` into `Shop location`; CJ writing to its own
legacy location creates the double-count described in CLAUDE.md. The store-level
"Not Sync" switch is the real guarantee, but leave this off for cleanliness.

## 5b. Un-pairing a product

The row's `...` menu is packaging and fulfilment only — there is no Disconnect in
it. The control is an unlink icon in the CJ Product column,
`i[class*=disconnecticon]`. The PRODUCT-level one has a different class suffix
from the per-variant ones, so take the first and confirm it is the row you mean:

```js
const ic = [...document.querySelectorAll('i')]
  .find(e => /disconnecticon/.test(e.className) && e.offsetWidth);
ic.closest('tr').innerText   // READ THIS before clicking
```

It raises a popover ("It may remove all the connection of the product") with a
`Confirm`. Click that once. This page is React, not Angular, so set its search
input with the native value setter plus an `input` event, not through ngModel.

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
