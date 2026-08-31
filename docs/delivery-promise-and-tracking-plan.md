<!-- Generated 2026-08-31 from a 30-agent research pass (read-only; nothing was
written to Shopify or CJ). Verified independently before recording: the
shipping-confirmation.liquid false statements (lines 46, 137), the "Processing:
1 to 3 business days" representation in write_policies.py:137, the checkout
WINDOW in shipping_apply.py:44, and the order-by-order customer split. -->

# WAGVIVE — DELIVERY PROMISE AND TRACKING: FINAL RECOMMENDATION
**2026-08-31. Read-only investigation; nothing was written to Shopify or CJ.**

---

## 1. VERDICT ON THE PROPOSED TRADE

**It is partly right and mostly a false trade. Do the copy change. Do not accept it as a substitute for the tracking work.**

The premise is wrong on the facts. CJ is not withholding data. `/logistic/trackInfo` returns, per parcel: `trackingStatus`, a full `routes[]` scan array, `deliveryDay`, `lastMileCarrier` ("Gofo") and `lastTrackNumber` (a US domestic number). It is a genuine bulk endpoint (up to 10 comma-separated numbers per call; 11 returns HTTP 400 `1600300`) and it costs 10 points a call against a ~58,859/day budget. The blindness is entirely on our side: nothing in this repo has ever read that feed or written a fulfillment event.

Your own store disproves "impossible" more directly. **Order #1001 has complete end-to-end tracking today**: 15 fulfillment events, `shipment_status: "delivered"`, and the customer received branded "out for delivery" and "delivered" emails on Aug 13 and 14 — with `tracking_company: "Other"`, on the same YunExpress lane, with zero code written. #1002 and #1003 have zero events. Whatever produced #1001 is unreliable, but it is not impossible.

**The part he is right about:** the promise is genuinely mis-stated and cannot be fixed by leaning on CJ. The variance sits in CJ's pre-shipment handling step, and no CJ field anywhere quotes it — `deliveryDay` (8/8/9) and `logisticsTimeliness.arrivalTime` ("8-15") describe transit only, and they were roughly accurate for transit. Restating the promise is correct, overdue, and cheap.

**Why the trade is false — the argument that should settle it:** a wider promise makes a customer wait longer before complaining. It does not tell you whether you shipped. And you have a legal obligation that is only operable if you know that.

> CJ marks the Shopify order fulfilled when it generates a **label**, up to 11 days before handover. So Shopify's "fulfilled" is not shipment in any sense — commercial or legal. The FTC Mail Order Rule requires a delay notice *before the promised ship date passes*. **You cannot comply with a rule about shipping without an instrument that tells you whether you shipped.** The only such instrument available is CJ's route feed. Abandoning the tracking work does not simplify the compliance problem; it makes it unsolvable.

There is also a live defect a wider promise does nothing about: **#1002's stored tracking number, `CJPAAN2180601032YQ`, is CJ's internal `cjMailNo`, not a carrier number.** The real one is `YT2623500704973330`. That customer was handed a string no carrier can resolve.

**Two decisions, decided separately. Both yes.**

---

## 2. THE TRACKING FIX

Build in this order. Priority 1 has no customer blast radius and is where nearly all the value is.

### Priority 1 — The owner alarm (build first, ~half a day)

New script `config/track_watch.py`, added as a step to `.github/workflows/scheduled-ops.yml` (already runs `17 */6 * * *`).

**Read side:**
- Shopify: GraphQL `orders(query: "fulfillment_status:shipped")` → per fulfillment: `id`, `trackingInfo{number, company, url}`, `createdAt`, `shipmentStatus`, `events(first: 50){happenedAt, status}`.
- CJ: `/logistic/trackInfo?trackNumber=A,B,C…` — **batch 10 at a time, never one call per order.** It accepts either the carrier number or the `cjMailNo`, so a monitor keyed on whatever Shopify happens to hold still resolves.
- Corroborate with `/shopping/order/list?status=UNSHIPPED` (one call) so an empty tracking answer is never itself a finding.

**Alarm conditions (what the OWNER gets told):**

| # | Condition | Meaning | Threshold |
|---|---|---|---|
| A | Fulfilled N days ago **and** `routes[]` empty **and** order still `UNSHIPPED` | No parcel exists. This is #1002's 11-day hole. | **6 business days** — deliberately inside the 10-day dispatch representation, so there is time to send the delay notice |
| B | Last `routes[].acceptTime` older than 7 days and `trackingStatus` not "Delivered" | Stalled in transit | 7 calendar days |
| C | Shopify `tracking_number` != CJ `trackingNumber` | Wrong identifier written (the #1002 defect) | Immediate |
| D | CJ returns `result:false, code:16900500` | **STOP.** Quota exhausted | Exit 3, never retry, never treat as a finding |

Mirror `margin_guard.py`'s exit-code convention exactly: **1 = a real problem, 3 = could not verify.** Per the standing rule in CLAUDE.md, an empty CJ answer gets one retry and then reads as UNKNOWN — condition A must be confirmed by *two* independent signals (empty routes AND order-level `UNSHIPPED`) before it fires.

**CJ points budget.** Every endpoint bills a flat 10 points regardless of payload.

| Volume | Per cycle | 4 cycles/day | % of ~58,859 budget |
|---|---|---|---|
| Today (3 orders) | 20 pts | 80 | **0.14%** |
| 10 orders/day (~15 in flight) | 30 pts | 120 | 0.20% |
| 50 orders/day (~75 in flight) | 90 pts | 360 | 0.61% |
| 200 orders/day (~300 in flight) | 320 pts | 1,280 | 2.2% |

Negligible next to the ~600/day the existing guards already spend. Wall clock, not points, is the binding constraint (`cj_api.py` sleeps 1.3s/call). **Do not add per-order `getOrderDetail` calls** — batched `trackInfo` plus one `order/list` is sufficient and keeps the cost flat.

**What the repo must store: nothing about customers.** The repo is public. Do not persist a state file of tracking numbers or addresses. Use a **stateless idempotency key**: read the fulfillment's existing `FulfillmentEvent.happenedAt` values back from Shopify each run and post only routes whose `acceptTime` is not already present. Shopify holds the state; the repo holds only thresholds, the route→status mapping, and the carrier-name mapping. `docs/qa/` logs record counts, not order identities.

### Priority 2 — What the CUSTOMER sees (build after the alarm, test on the next live order)

Both mutations run under the existing **Wagvive Ops** token, which already holds `write_fulfillments` and `write_merchant_managed_fulfillment_orders`. No new app, no new scope.

**a) Correct the tracking record** — `fulfillmentTrackingInfoUpdate(fulfillmentId, trackingInfoInput: {number, url, company}, notifyCustomer)`. Use GraphQL, not REST (`fulfillmentTrackingInfoUpdateV2` is deprecated; REST is legacy and caps you at one number/URL).
- Rewrite `number` when CJ's `trackingNumber` differs from what Shopify holds — this is the whole fix for the #1002 class.
- Set `company` to the exact string **`"YunExpress"`** (it is on Shopify's recognised list; capitalisation matters). This stops the emails rendering **"Carrier: Other"** — `shipping-confirmation.liquid:76`, `out-for-delivery.liquid:51` and `shipping-update.liquid:51` all print `{{ fulfillment.tracking_company }}` unguarded.
- Do **not** expect this to buy Shopify's own carrier polling. That runs off a separate, shorter list; assume no.

**b) Push the scan chain** — `fulfillmentEventCreate(fulfillmentId, fulfillmentEventInput: {status, happenedAt, message, city, province, country, zip})`. CJ's `routes[]` maps almost field for field: `acceptTime` → `happenedAt`, `acceptAddress` → city/province/country, `remark` → `message`. `FulfillmentEventStatus` carries exactly what is needed: `CONFIRMED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `ATTEMPTED_DELIVERY`, `DELAYED`, `FAILURE`. This is what sets `shipment_status` and fires the branded `out-for-delivery.liquid` and `delivered.liquid` templates.

**Three hard constraints on (b) — read these before writing a line:**

1. **`FulfillmentEventInput` has NO `notifyCustomer` field.** Posting `OUT_FOR_DELIVERY` or `DELIVERED` emails the customer, unsuppressibly. A non-idempotent poller emails them repeatedly. This is the largest blast radius in the whole build — the read-back idempotency key above is mandatory, not a nicety.
2. **Do not push `estimatedDeliveryAt` from CJ's `deliveryDay`.** CJ quoted 8/8/9 days against actual 12/18/19 calendar. That would put a provably wrong date in front of the customer.
3. **Do not backfill the three existing orders.** #1001 already has a correct chain — writing to it risks breaking the one record that works. #1003 delivered Aug 30 and #1002 Aug 31, so replayed events would email about parcels already in hand. Also note **#1002's buyer is your own address** (`mattmoorefb24@gmail.com`, the HANDOFF #75 test purchase), so exactly **one real customer** (#1003) was ever affected by the silence. Start clean on the next order.

### Priority 3 — CJ push webhooks (defer)

`/setting/get` shows `callback` with all four topics (`product`, `stock`, `order`, `logistic`) registered as `type: "CANCEL"` with empty URLs. Enabling is one `POST /webhook/set`. The `LOGISTIC` payload carries `trackingNumber`, `trackingProvider`, a numeric `trackingStatus` 0-14 and `logisticsTrackEvents`.

**Not worth it at 3 orders.** It needs a public HTTPS endpoint answering 200 within 3 seconds with HMAC-SHA256 signature checking (secret = `openId`), and CJ auto-disables any topic whose success rate drops below 80% over two hours. Your ops stack is GitHub Actions with no server. Revisit around 50 orders/day. Note the status representation differs by channel — poll returns a **string** ("Delivered"), webhook pushes an **int** 0-14; normalise to the numeric scale if you ever build this.

### Browser-only (no API exists)

1. **Notification templates.** Settings → Notifications, hand-pasted. There is no API. Regenerate from `config/build_email_templates.py` first, never hand-edit.
2. **Confirm "Out for delivery" and "Delivered" are still enabled** under Settings → Notifications → Customer notifications. No API. They fired for #1001 on Aug 13/14, so they were on then. Per CLAUDE.md, admin settings screens do not render in a background tab — you must foreground it.

**Explicitly NOT needed:** the CJ Sync Settings switches. The hypothesis that the 2026-08-04 "Not Sync" change broke tracking is **dead** — #1001's event stream ran continuously from Aug 7 to Aug 14, entirely after that date, and on Aug 12 the store ingested events for #1001 while ingesting none for #1002/#1003 fulfilled the same hour. Do not spend a browser session on it.

---

## 3. THE COPY CHANGE

### Recommended wording

The store currently publishes **two contradictory promises on the same product page**: a flat total ("Arrives in 5 to 12 business days") and a compound one ("Dispatched in 1 to 3 business days… 5 to 12 after dispatch" = up to 15). Measured deliveries of ~10, ~13 and ~14 business days are *inside* the compound reading and *outside* the flat one. Kill the compound structure. **Publish one door-to-door number.**

**Customer-facing headline** (product bodies, emails, checkout, FAQ, theme):

> **Arrives in 10 to 16 business days.** We ship direct from our overseas warehouse rather than holding stock in the US, which is how the price stays where it is.

**Shipping policy — "How long it takes" replacement:**

> - **Dispatch:** within 10 business days. Most orders leave sooner.
> - **Delivery:** 10 to 16 business days from the day you order.
> - **Tracking:** emailed when your parcel is handed to the carrier. It can be quiet for the first week or so while your order is being packed, which is normal.

**Notes on the wording, and where I differ from your proposal:**
- **Write "10 to 16", never "10-16".** CLAUDE.md non-negotiable #4 bans hyphenated day ranges. Your "10-15" as typed would violate the house rule the store already enforces.
- **16, not 15.** Observed max is ~14 business days on n=3, with no supplier-quoted ceiling on the handling step. One extra day is cheap insurance; 10 to 15 is defensible if you prefer it, and the difference barely matters next to the dispatch line below.
- **Drop "may arrive sooner."** A range already implies it, and with n=3 (10, 13, 14) there is no basis for promising sooner. It reads as hedging.
- **"Dispatch within 10 business days" is the load-bearing sentence.** It is the FTC's actual hook (section 5), and it is the only number with a defensible basis: dispatch ran 4.9, 8.8 and 11 calendar days, all comfortably inside 10 business days. "1 to 3 business days" has had no reasonable basis since at least Aug 2.

### Complete list of places it must change

**Live customer-facing (20 surfaces):**

| # | Surface | What is there | Change via |
|---|---|---|---|
| 1 | 40 active product bodies | `<p><strong>Arrives in 5 to 12 business days.</strong></p>` | `productUpdate` on `descriptionHtml` |
| 2 | **12 active products with NO delivery line** | absence, not a string | same — these are gaps a replace cannot find |
| 3 | 2 archived products | hyphenated variant | tidiness only |
| 4 | **Checkout, 2 rate descriptions** | `"5-12 business days. Free on orders over $60."` / `"5-12 business days."` | `config/shipping_apply.py` **WINDOW, line 44** |
| 5 | Shipping policy (live) | Processing 1 to 3; Delivery 5 to 12 after dispatch; "leaves the warehouse"; **7-day no-movement chase trigger** | `config/write_policies.py` SHIPPING, ~lines 126-167 |
| 6 | Refund policy | "cancel any time before dispatched"; "if we cannot ship within the time stated" | `write_policies.py` REFUND, lines 78-124 |
| 7 | Terms of service | "A contract is formed when we email you to confirm dispatch" | `write_policies.py` TERMS, lines 169-422 |
| 8 | `/pages/shipping-returns` | live copy, **no generator in repo** | Admin API direct; then fix or delete `config/pages/shipping-returns.json` |
| 9 | `/pages/faq` | "Processing 1 to 3, then typically 5 to 12" | Admin API direct; `config/faq_copy.py` is **dead code, zero importers** |
| 10 | FAQ meta description + 2 social cards | auto-derived from body | no separate edit; re-verify after |
| 11 | Theme `templates/index.json` | homepage FAQ: "typically **arrive in** 5 to 12" | theme write **+ mirror `config/theme-work/templates__index.json` line 1336** |
| 12 | Theme `templates/product.json` | trust badge "Ships in 1 to 3 business days" + "Shipping & delivery" accordion. **Renders on all 65 product pages** | theme write |
| 13 | JSON-LD structured data | follows `body_html` | no separate edit |
| 14 | 4 notification emails | `order-confirmation.liquid` (25 preheader, 61 body), `pending-payment-success.liquid:33`, `abandoned-checkout.liquid:57`, `customer-account-welcome.liquid:39` | regenerate + **hand-paste in admin** |
| 15 | `shipping-confirmation.liquid` | **line 46 "has left the warehouse", line 137 "a day or two to start updating"** | see below |
| 16 | Marketing flow 2 (not live) | `marketing-abandoned-2.html:43`, `-block.html:18`, `docs/marketing/email-flows-2026-08.md` 112/253-254/331 | cheapest place to fix, nothing sending yet |
| 17 | Shopify MCP index (`/api/mcp`) | serves shipping answers from an index of policies/pages | downstream, but **re-ask it after the change** |

**#15 is the single highest-value copy fix in the whole list, and a find-and-replace cannot reach either line.** Both statements are now known to be false: CJ fulfils at label generation, and #1002 produced no carrier scan for 11 days. Replace with language that matches reality — the parcel is *being prepared*, and tracking may not move for a week or more.

**Note the tag-shape trap:** `config/apply_size_guides.py` anchors on `<p><strong>Arrives in …</strong></p>` at lines 212 and 219, with a silent `html + blk` fallback. Changing the number inside that shape is safe. Changing the *sentence structure* makes `strip_old` stop removing the old guide and `insert` append a duplicate, across 15 sized products, with no error. **Keep the tag shape, or update both regexes in the same commit.**

### Regression paths — these silently restore the old copy

1. **Wired to CI.** `.github/workflows/theme-copy-fix.yml` runs `config/fix_product_care_copy.py --apply` on any push to `main` or `claude/**` touching `config/theme_fix_run.json`, or on manual dispatch. Its `EDITS` list writes the old strings **by JSON path, unconditionally, without comparing current content** — lines 56 and 62-64. Update it in the *same commit* as the theme change.
2. `config/shipping_rates.py --apply` would **delete the delivery window from checkout entirely** and resurrect a $15 Express rate that `shipping_apply.py` (lines 14-18) deliberately removed. Two scripts write the same object and disagree. **Retire `shipping_rates.py`.**
3. Five artefacts holding *older, wronger* versions with banned en dashes: `config/build_homepage.py:268-269`, `config/enhance_product_page.py:80,96`, `config/_product_template.json:546,612` (also a stale $50 threshold), `config/pages/faq.json`, `config/pages/shipping-returns.json`.
4. `config/fix_claims.py:40-42` maps 5-11 → 5-12 and would **re-stamp 12 over any new number**.
5. **Nine product-creation scripts** stamp the old promise into every new product: `apply_kits.py` (6 sites), `add_fall_lineup.py` (6), `add_fall_wave2.py` (6), `create_round2_products.py` (4), `create_round4_products.py:56`, `add_dental_chew.py:74`, `fix_fall_copy.py` (2), `update_kit_copy.py` (2), `sizing_copy.py:18`. Plus hyphenated legacy in `build_cover_v2.py:65` and `build_puppy_kit.py:63`. **Centralise on `sizing_copy.DELIVERY` and import it everywhere** — otherwise the next product launch reintroduces the retired promise.
6. `config/audit_claims.py:22-23` — the transit regex matches *any* hyphenated `N-N business days` and still hunts the retired "5-11", so it will flag the new wording. It also does **not** scan shop policies or the delivery profile, which are the two surfaces with the most legal weight. Update the regex and extend the coverage.

### The promise is also code

`MAX_DAYS = 12` is a real constant in **five** files: `freight_floor.py:41`, `guard_unshippable.py:45`, `freight_check.py:69`, `audit_cj_connections.py:39`, `margin_guard.py:52` (used at 201). `carrier_audit.py` imports it and adds `FAST_DAYS = 9`.

It is parsed from `logisticAging`, a **transit-only carrier figure**. It has never included CJ's handling step. That is precisely why `guard_unshippable.py` certified all 145 variants "inside the 12-business-day promise" on orders that breached it.

**My recommendation runs against the obvious move: do NOT widen MAX_DAYS to 16.** If you promise 16 business days door to door and allow 10 for dispatch, the honest transit budget is 6, not 16. Widening the constant would let CJ put parcels on slower, cheaper lanes and spend the entire new headroom on freight savings — reproducing the exact breach at a wider promise. Instead:
- **Keep MAX_DAYS at 12** and fix its comment to say plainly that it is a transit-only carrier ceiling and *not* the published promise.
- Add two separate, clearly-named constants — `PROMISE_DAYS = 16` and `DISPATCH_DAYS = 10` — so the published promise and the carrier ceiling stop being conflated.

Treat any change to MAX_DAYS as a deliberate cost/speed decision with a margin re-run, never as a side effect of a copy edit.

---

## 4. SHOULD THE PROMISE BE SPLIT PER PRODUCT?

**No. Not now.** Publish one promise sized to the slow path.

Shopify can do it — separate delivery profiles per product carry their own rate descriptions, which is a genuinely different promise at checkout. The mechanics are not the obstacle. The economics and the operational hazard are.

- **Only 2 of 46 current SPUs hold US stock**: Ball Launcher (127 units) and Hair Remover Mitt (12 units). Twelve units is one good week. A two-product profile is not a promise, it is a liability.
- **US-warehouse goods are a dearer catalogue, not the same goods at a better address.** Median goods cost $39.12 vs $2.88; median minimum retail at the 20% floor $60.16 vs $12.77. Only 11 of 46 current products could carry a US-warehouse item costing $8 or more. Direct replacements exist at the top of the range (US slicker brush $9.00, grooming glove $9.13, bath brush $10.08) but the sub-$15 toy shelf cannot survive the move at current prices.
- **Freight is unconfirmed.** Every US-origin quote in the survey returned $0.00, which `freight_floor.py` already knows means missing data. The only real numbers observed were USPS+ $5.10-$5.26, GOFO+ $4.98, FedEx Ground+ $20.01, all 3 to 7 days. Plan at ~$5.50 and confirm at pairing, per the standing rule that the carrier the price was modelled on must be the carrier actually used.
- **The killer hazard:** nothing fires when US stock runs out. A variant silently reverts to China sourcing while still displaying a 3-to-7-day promise, and you have manufactured a breach you cannot see. Making this safe means polling `/product/stock/queryBySku` for `countryCode: US` rows and **holding the product back** when they empty — a harder guard than `guard_unshippable.py` already runs.

**The trigger for revisiting is a business decision, not a copy decision:** move the $25-and-up shelf to US-warehouse sourcing as a deliberate programme, get it to a size that justifies its own collection, build the stock-exhaustion guard, *then* split the promise. Until then, one number for everything.

---

## 5. COMPLIANCE

### What the FTC Mail Order Rule (16 CFR 435) requires

1. **A reasonable basis for the stated shipment time, at the moment of the order.** No stated time defaults to 30 days.
2. **"Shipped" means the goods leave your control.** A generated label is not a shipment. **Shopify's "fulfilled" is therefore not evidence of shipment in this store**, since CJ fulfils at label generation up to 11 days early.
3. **If you cannot meet the stated date, a delay option notice — sent before the original date passes**, by a means at least as fast as the order was taken, at no cost to the customer. It must give a **revised definite date** and the **option to cancel for a prompt refund**.
4. **For a first delay of 30 days or less, the notice may treat silence as consent** — provided it says so.
5. **Prompt refund** on cancellation: 7 working days for prepaid, one billing cycle for credit.

### Where the store stands

- **The binding representation is "1 to 3 business days" processing, and it was breached on at least 2 of 3 orders.** First carrier scans came at 4.9, 8.8 and 11 calendar days. Three business days is at most ~5 calendar days.
- **No delay option notice was ever sent.** That is an **independent violation of 435.2(b)**, on top of the missed date — and arguably the more serious of the two, because it is a process failure rather than a supplier failure.
- Legal obligations in the **Refund Policy** ("cancel any time before dispatched") and **Terms of Service** ("a contract is formed when we email you to confirm dispatch") are keyed to "dispatch", a word that currently means "CJ printed a label". Neither contains a day-range string, so both are invisible to a find-and-replace.

### What the store must do that it currently does not

1. **Restate the shipment representation to something supportable.** "We dispatch within 10 business days" clears all three observed orders with headroom. This is the change that actually removes the violation — the delivery estimate is secondary.
2. **Build the delay option notice.** It does not exist in any form. Create it as a new template (it fits `config/build_email_templates.py`, and note that generator currently produces **16 of the 18 `.liquid` files** — `order-confirmation` and `shipping-confirmation` are *not* generated, so CLAUDE.md's "never hand-edit the 18 files" is wrong as written and should be corrected). Required content: a revised definite date, an explicit cancel-for-full-refund option, a cost-free way to exercise it, and the silence-is-consent clause, e.g. *"If we do not hear from you before we ship, we will take it that you are happy to wait."*
3. **Wire the notice to a trigger you can actually observe.** This is where section 2 becomes non-optional: the only signal that a parcel has not shipped is CJ's route feed. Alarm condition A firing at 6 business days is what gives you four business days to send the notice before the 10-day representation lapses.
4. **Fix the two false statements in `shipping-confirmation.liquid`** (lines 46 and 137). Telling a customer their order "has left the warehouse" when it will not exist for 11 days is the clearest consumer-facing misrepresentation in the store.
5. **Rewrite the 7-day no-movement chase trigger** in the shipping policy. Under a 10-day dispatch window, tracking that has not moved for 7 days is normal, not a problem — the current wording invites tickets and chargebacks against your own baseline.

---

## 6. SEQUENCING

**First — today. The copy and the legal fix, in one commit.**
You are in active breach of a live representation, and every order placed under the old wording adds exposure. Do the full sweep from section 3 at once: policies, checkout `WINDOW`, 40 product bodies, both theme templates, the two pages, the 4 notification emails, plus — in the *same* commit — `fix_product_care_copy.py`, `sizing_copy.DELIVERY` centralised across the 9 creation scripts, `audit_claims.py`'s regex, and the retirement of `shipping_rates.py`, `faq_copy.py` and the two stale `config/pages/*.json` seeds. Add `PROMISE_DAYS` / `DISPATCH_DAYS` and fix MAX_DAYS' comment; leave its value at 12. Verify against the live storefront with a `?nocache=` param, not against the write's return value.

**Second — same day. `shipping-confirmation.liquid` lines 46 and 137.** Small, unreachable by search-and-replace, and the most directly misleading thing the store says.

**Third — this week. The owner alarm (`config/track_watch.py`).** No customer risk, ~20 CJ points per cycle, and it is the instrument that made three delivered orders look like lost ones. Ship it before the next order arrives, not after.

**Fourth — this week. The delay option notice template and runbook.** Cheap to write, and it must exist *before* the alarm fires for real. Writing it under time pressure on a live order is how you get it wrong.

**Fifth — next live order. The customer-facing event push.** `fulfillmentTrackingInfoUpdate` first (lowest risk, fixes the wrong-number class and "Carrier: Other"), then `fulfillmentEventCreate` behind the read-back idempotency guard. Test on a real in-flight order with `notifyCustomer` omitted on the tracking update. **Backfill nothing.**

**Can wait, and should:**
- **CJ webhooks** — needs a server you do not have, for 3 orders/day. Revisit at ~50/day.
- **Per-product promise split** — needs a US-sourced shelf that does not exist yet.
- **Re-deriving MAX_DAYS** — a deliberate margin decision with a full re-run, not a side effect. Do it when you next reprice.
- **Diagnosing why #1001 got events and the others did not** — genuinely interesting, and irrelevant to the build. The fix is identical under every candidate explanation. Do not let it gate anything.

---

## 7. RISKS AND UNKNOWNS

**Build risks**

- **The unsuppressible-email risk is the big one.** `FulfillmentEventInput` has no `notifyCustomer` field, so `OUT_FOR_DELIVERY` and `DELIVERED` events email the customer with no way to turn it off. A non-idempotent or re-running poller spams real customers. The read-back idempotency key is load-bearing; treat a bug there as a customer-facing incident, not a script failure.
- **`fulfillmentEventCreate` has never been tested on this store.** Every fulfillment was created by CJ's app on a fulfillment order that is `CLOSED` / `unsubmitted` with `supportedActions: []`. Nothing documented restricts it and the scopes are held, but this lane was read-only. **Test on the next real order before relying on it.**
- **Duplicate events if the unknown mechanism resumes.** If whatever produced #1001's 15 events fires again while your poller is running, you could double-post. Same mitigation, same key.
- **The CJ points quota is the trap that produces confident wrong numbers.** A 200 with `result:false, code:16900500` must exit 3 and must never register as "no scans found" — that is precisely how a healthy parcel would get flagged as stalled. Do not retry into it.
- **Public repo.** Do not let any committed file, QA log or Actions log carry a tracking number, address or customer name. The stateless design avoids this entirely; a "temporary" state file would not.

**Unverified**

- **Why #1001 tracked and the others did not — still unresolved.** Two candidates, and the evidence genuinely splits: CJ's app pushed the events (timestamps match CJ's routes to the second), or Shopify's own tracking resolved the `YT` number and polled it (the message vocabulary differs from CJ's routes, and `cjdropshipping` is registered `tracking_support: false`). Under both readings the build is the same, which is why it does not gate the work — but it means **you cannot predict whether the next order gets events for free.**
- **Whether "Out for delivery" and "Delivered" are still enabled** in Settings → Notifications. No API. They fired Aug 13/14, so they were on then.
- **Whether Liquid renders `tracking_company` as literal `"Other"` or nil** — determines whether customers have been reading "Carrier: Other". Resolvable by sending one test email.
- **Whether `"YunExpress"` buys Shopify's own `shipment_status` polling.** It is on the URL-building list; the polling list is separate and Shopify's own help names only FedEx, Canada Post, DHL Express, UPS and USPS. **Assume no.**
- **Whether the `cjMailNo`-instead-of-carrier-number defect is systematic** or only occurs on Sensitive lines. n=1, and #1002 is the only Sensitive-line order in the sample.
- **The handling step has no quoted ceiling anywhere in CJ's API.** 5 to 11 calendar days on three orders, upper bound unestablished. **Any restated promise, including this one, is an extrapolation from n=3, not a supplier commitment.** Re-derive after ~20 orders and be willing to widen again.
- **`qpsLimit` reads 100 in `/setting/get`** while `cj_api.py` uses `MIN_INTERVAL = 1.3`. Do not loosen the throttle on that alone — the 429s that motivated it were real — but a high-volume monitor should retest rather than assume 1.3s/call.

**One thing that lowers the stakes:** #1002 was your own test purchase. Exactly **one real customer** has been affected by the tracking silence so far, and their parcel arrived yesterday. You are fixing this before it has cost you anything, which is the best position you will ever be in to fix it.

