# What actually went wrong with CJ delivery, measured

**2026-08-31.** The supplier pivot was launched on the belief that "multiple
orders took 3+ weeks to ship" and that two orders had never moved 18 days out.
Before spending money to replace CJ, the three real orders were measured
end to end against CJ's own tracking API. The belief was **half right, and
wrong about the cause** - and the cause turns out to be fixable without
leaving CJ.

## The measurements

Every order was pulled from `/shopping/order/list` and every carrier scan from
`/logistic/trackInfo`. All three orders **delivered**. None was lost.

| Order | Placed | First scan | Delivered | Calendar | Business | Promise |
|---|---|---|---|---|---|---|
| #1001 | Aug 2 | +1 day | Aug 14 | 12 d | ~10 d | **inside 12** |
| #1003 | Aug 12 | same day | Aug 30 | 18 d | ~13 d | 1 day over |
| #1002 | Aug 12 | **+11 days** | Aug 31 | 19 d | ~14 d | 2 days over |

CJ's own quoted `deliveryDay` for these was **8 to 9 days**. It delivered in
12 to 19.

## The cause is pre-shipment handling, NOT transit

This is the finding that matters. Reading the route logs, the parcels move
quickly once they are actually moving - #1002 went Incheon to Brooklyn to
delivered in about six days, which is a normal air lane. The time is lost
BEFORE the parcel exists:

* #1001 sat **4.9 days** at "Order created"
* #1003 sat **8.8 days** at "Order created"
* #1002 produced **no scan at all for 11 days** after the order was placed

So the variable is CJ's pick-pack-and-handover step, which ran between 5 and
11 days on a 3-order sample and is the entire spread between a 12-day delivery
and a 19-day one. Transit is not the problem. **Sourcing from stock that is
already in the United States removes this step completely**, which is why the
US-warehouse question below is the whole ballgame.

## The second, separate failure: we could not see any of it

The owner believed these orders were lost. Reasonably so:

* Shopify records the fulfillment with `tracking_company: "Other"`, so Shopify
  cannot poll the carrier and never populates `shipment_status`.
* Both late orders still read `shipment_status: null` with `updated_at` frozen
  at the day they were fulfilled - the same shape a genuinely dead order has.
* CJ marks the Shopify order fulfilled the moment it generates a label, which
  is up to 11 days before the parcel is handed over. **"Fulfilled" in this
  store does not mean shipped.**
* Nothing in the repo ever compared a promise date against a real scan.

So a 19-day delivery and a lost parcel were indistinguishable from the admin,
for 19 days. That is a monitoring gap, and it exists no matter who supplies
the goods. It should be closed regardless of the pivot decision.

## CJ's US warehouse: measured, real, and expensive

`/product/list` accepts an undocumented-but-honest `countryCode: 'US'` filter
(it cuts the Chew category from 442 products to 16; `warehouseCountryCode` is
ignored and returns the unfiltered set, so it is the wrong parameter).

Sweeping the 13 pet categories this store already shops:

* **410 US-warehouse pet products; 262 dog-relevant.**
* Sampled six against `/product/stock/queryBySku`: every one returned real
  `countryCode: US` rows holding **24 to 230 units**, and quoted **3-5 to 3-7
  day** domestic carriers - Amazon Logistics, USPS, UPS, FedEx, DHL.
* Only 2 of the store's 46 current SPUs hold US stock today (Ball Launcher
  127 units, Hair Remover Mitt 12 units).

**The catch is price.** US-warehouse goods are not the same goods at a better
address; they are a dearer catalogue:

| | current China-sourced | CJ US warehouse |
|---|---|---|
| median goods cost | **$2.88** | **$39.12** |
| median landed | $9.17 | ~$44.62 |
| median min retail @20% | **$12.77** | **$60.16** |

Only 32 of 232 dog products land under $25 retail; 57 under $30. Against the
store's current retails, **11 of 46 could carry a US-warehouse product costing
$8 or more**. Direct replacements do exist for things already sold - a US
slicker brush at $9.00 (47 units), a 2-in-1 grooming glove at $9.13 (27
units), a screaming dog toy at $4.50 (100 units), a bath brush at $10.08 (230
units) - but the sub-$15 toy shelf cannot survive the move at its current
prices.

**Freight caveat:** every US-origin quote in the sample returned **$0.00**,
which `freight_floor.py` already knows means missing data, never free
carriage. The only real US domestic numbers observed were on the Hair Remover
Mitt: USPS+ $5.10 to $5.26, GOFO+ $4.98, FedEx Ground+ $20.01, all 3-7 days.
So ~$5.50 is the planning figure and every candidate must have freight
confirmed at pairing time, per the standing rule that the carrier the price
was modelled on must be the carrier actually used.

## What this means

The pivot's premise needs restating. CJ is not losing parcels and its transit
lane is not broken. CJ is **slow and highly variable at the warehouse step**,
by 5 to 11 days, and the store had no instrument to see it. Two of three
orders breached the published promise, by 1 and 2 business days.

That supports a narrower conclusion than "replace CJ": the thing to escape is
**China-warehouse sourcing for anything where the promise matters**, which is
achievable inside CJ for products the store can price at $25 and up, and only
outside CJ (or not at all) for the sub-$20 toy shelf.

Reproduce with `config/survey_cj_us_warehouse.py`; raw output in
`docs/qa/cj-us-warehouse-survey.json`.
