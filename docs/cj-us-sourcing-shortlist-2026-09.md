# CJ US-warehouse sourcing: what to add, what to replace, and what it costs

**2026-09-01.** A comprehensive sweep of every dog-relevant CJ category for
US-warehouse stock, verified product by product against live stock rows and
carrier quotes. This is the "stay with CJ but prioritise US stock" programme.

## Method, and why the obvious shortcut is wrong

`/product/list` accepts `countryCode=US`, which really does filter (it cuts Pet
Chew Toys from 443 products to 16). `warehouseCountryCode` is silently IGNORED
and returns the unfiltered set - using it would make every product on CJ look
US-warehoused.

Swept **57 dog-relevant leaf categories** (excluding bird, fish and cat-only)
from CJ's own category tree: **1,532 distinct US-warehouse products**.

Filtered to **175 candidates**: dropped 768 cat/bird/fish items, 26 self-pickup
and test listings, 99 with no price, 1 SPU the store already sells, and 463
whose 20% floor price exceeded $55 retail.

**The `countryCode=US` filter is a CLAIM, not a guarantee.** 34 candidates went
to live verification against `/product/stock/queryBySku` and
`/logistic/freightCalculate`, and **6 came back with zero US units** on their
first variant despite being returned by the US filter - every one of them an
apparel item. Verify before pairing, always.

**28 of 34 confirmed**, holding 5 to 1,984 units in US warehouses and quoting
**3 to 5 or 3 to 7 day** domestic carriers (Amazon Logistics, USPS, UPS, FedEx,
DHL, GOFO).

### Pricing

`landed = (goods + freight) x 1.03`, `margin = (price - landed - 0.03103 x price
- 0.30) / price`, floor 20%, rounded up to a .99 price point.

Freight is planned at **$5.50**. Every US-origin quote returned **$0.00**, which
`freight_floor.py` already knows is missing data rather than free carriage; the
only real US domestic numbers observed on this account are USPS+ $5.10 to $5.26
and GOFO+ $4.98. **Confirm freight per product at pairing time** - the carrier
the price was modelled on must be the carrier actually used.

---

## The honest headline: US stock costs roughly double

This is the trade the whole programme turns on, and it should be stated before
any product list.

| | current China sourcing | CJ US warehouse |
|---|---|---|
| median goods cost | $2.88 | $39.12 (all), ~$11 (the shortlist) |
| typical delivery | 10 to 14 business days, unpredictable | **3 to 7 days, predictable** |
| Screaming Chicken, as an example | $12.99 today | **$22.99** for the US equivalent |

Nothing on this list is a like-for-like swap at the same price. Every US
replacement needs a higher retail. That is the deal the owner already accepted
("I would rather charge more for higher quality products"), but it means the
sub-$15 shelf cannot survive a wholesale move, and the programme should be run
product by product rather than as a catalogue-wide switch.

---

## RECOMMENDED: additions that fill real gaps

Ranked by how proven they are (`sellers` = other merchants listing the same SPU
on CJ, the best available demand signal) and by US stock depth.

| Product | Retail @20% | Margin | US units | Sellers | Speed | Why |
|---|---|---|---|---|---|---|
| **LED Safety Halo Collar** | **$25.99** | 22.4% | 230 | **806** | 3-5d | The single most-listed item found. Night-walk safety is a real need the store does not serve at all, and it pairs naturally with the existing collar-free catalogue. |
| **Dog GPS Tracker, geofencing** | **$27.99** | 22.6% | 34 | 295 | 3-5d | Highest-value gap on the list. Anxiety-adjacent, sits beside the Calming Wrap, and is the kind of product people buy without price-shopping. Stock is thin at 34 units. |
| **Dog Training Collar** | **$22.99** | 20.1% | 96 | 356 | 3-7d | Training is a whole category the store is absent from. Margin is thinnest here at 20.1%, so price it at $24.99 rather than the floor. |
| **Washable Pee Pads, 2 pack reusable** | **$40.99** | 20.4% | 230 | 187 | 3-5d | Consumable-adjacent and repeat-purchase, which nothing in the current catalogue is. Good stock. |
| **3-in-1 Travel Collapsible Bowl** | **$24.99** | 22.5% | 230 | 143 | 3-5d | Complements the Travel Water Bottle directly; natural bundle component for the Travel Kit. |
| **Dog Puzzle Toys, treat enrichment** | **$33.99** | 20.9% | 270 | 171 | 4-8d | Enrichment is a category POD cannot touch and the store barely covers. |
| **Dog Ramp** | **$21.99** | 21.6% | 11 | 297 | 3-7d | Strong demand signal and a senior-dog niche, but **only 11 units** - treat as a trial, not a launch. |
| **Pet Photo Props toy** | **$10.99** | 21.3% | 25 | 228 | 3-7d | Cheap, seasonal, social-media friendly. Low stock; low stakes. |

**Deliberately NOT recommended despite good numbers:**

* **Dog Car Seat Cover** ($36.99, 702 sellers) - **1 unit in stock.** The demand
  signal is the second best on the list and the stock is a rounding error. Watch
  it; do not list it.
* **Pet Calming Spray** ($25.99, 541 units) - only **4 other sellers**. Plenty of
  stock, no demand evidence, and a claims-sensitive category (calming products
  invite efficacy questions the store cannot answer).
* All six apparel items - **zero US units**, see verification note above.

---

## RECOMMENDED: replacements for products already sold

These upgrade an existing product from China sourcing to US stock. The retail
must rise; the delivery promise falls from ~14 business days to 3 to 7.

| Replaces | New product | Retail @20% | Margin | US units | Sellers |
|---|---|---|---|---|---|
| Screaming Chicken ($12.99) | 3pcs Latex Screaming Chicken set | **$22.99** | 21.6% | 137 | 328 |
| various squeakers | 4pcs Latex Chew Toys with sound | **$24.99** | 20.8% | 226 | **349** |
| various squeakers | Hiphoppet Latex Interactive Chew Toys | **$22.99** | 22.6% | 228 | 186 |
| Slow Feeder Bowl ($13.99) | Fish-Shaped Treat Dispenser, slow feed | **$21.99** | 21.5% | 230 | 85 |
| Slow Feeder / Lick Bowl | Adjustable Treat Dispensing Puzzle Ball | **$25.99** | 20.0% | 193 | 193 |
| Watermelon Rope Frisbee ($10.99) | 5pc Rope Chew Toy Set | **$22.99** | 23.3% | 24 | 214 |
| Dental Chew Stick | Pet Dental Powder | **$23.99** | 23.1% | **1,984** | 103 |
| Travel Water Bottle ($18.99) | Portable Water Bottle, BPA-free | **$23.99** | 23.0% | 150 | 12 |
| Anti-Spill Water Bowl ($24.99) | Stainless Steel Hanging Bowl, detachable | **$28.99** | 21.3% | 230 | 118 |
| Anti-Spill Water Bowl | Stainless Steel Hanging Bowl (M) | **$21.99** | 22.8% | 31 | 77 |
| — | Absorbent Feeding Mat | **$31.99** | 20.7% | 50 | 22 |

**The three highest-confidence replacements** are the Dental Powder (1,984
units, deepest stock found anywhere), the 4pc Latex Chew Toys (349 sellers,
226 units) and the Screaming Chicken set (328 sellers, 137 units). Those three
have both the demand evidence and the stock depth to survive real traffic.

---

## How to run this programme

1. **Do not switch the catalogue wholesale.** Every replacement roughly doubles
   retail. Run it product by product and watch conversion.
2. **Start with the three highest-confidence replacements** plus the LED Halo
   Collar and the GPS Tracker as additions. Five products, all with real stock
   depth, all 3 to 7 day delivery.
3. **Confirm freight at pairing time** for each. Every US quote read $0.00.
4. **Re-verify US stock before every listing** - six of thirty-four candidates
   failed this check.
5. **The stock-exhaustion hazard is the one that will bite.** Nothing currently
   fires when US stock empties. A variant silently reverts to China sourcing
   while still showing a 3-to-7-day promise, which manufactures a breach that
   cannot be seen. Before promising per-product speed, extend
   `guard_unshippable.py` to poll `countryCode: US` rows and hold a product back
   when they empty.
6. **Only then consider a split delivery promise** (US items 3 to 7 days, China
   items 10 to 16). Until the guard exists, publish the single slower promise.

Raw data: `cj_us_full.json`, `us_candidates.json`, `verified.json` in the
session scratchpad; sweep script `config/survey_cj_us_warehouse.py`.
