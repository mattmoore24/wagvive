# Supplier pivot research: POD depth, dropship census, multi-supplier architecture

**2026-08-30.** Fourth and final research pass for leaving CJ Dropshipping.
Constraints set by the owner: dropship/POD only (no inventory before consistent
order flow), kits may split into parcels, minimal/no kit discount, 20% margin
floor on everything, higher quality + predictable US shipping is the point.

Everything in the VERIFIED sections below was obtained first-hand this session
— from public APIs, the suppliers' own pages via browser, or the store itself —
not from search summaries. Sources are named inline.

## The arithmetic every number below is judged against

margin = (price − landed − 0.03103·price − 0.30)/price, landed = (goods+freight)·1.03.
Min retail at the 20% floor: goods at 35% of retail → $21.92; 45% → $29.31;
50% → $35.25; 62% → $68.67; 65% → $90; 80% → impossible.

## VERIFIED: Printful (public API api.printful.com + product pages, browser)

9 pet-tagged products, of which **only 4–5 are US-produced**. The rest are
made in China — which defeats the purpose of the pivot and was invisible until
the per-variant `availability_status` regions were read:

| SKU | Cost | US ship (page-verified) | Region | Min retail @20% |
|---|---|---|---|---|
| AOP Bandana | $10.35 | $4.69 | US/EU | **$20.99 (21.7%)** |
| Pet Feeding Mat 19×14 | $16.88 | $6.69 | US only | **$31.99 (20.1%)** |
| Pet Feeding Mat 30×18 | $27.88 | $6.69 | US only | $46.99 (20.5%) |
| Pet Bandana Collar | $17.93 | $5.89 | US, **1 of 4 sizes in stock** | $32.99 (21.6%) |
| Pet Bowl 18oz | $21.92 | $10.89 | US+3 | $44.99 (21.1%) |
| Throw Blanket 30×40 / 50×60 | $24.62 / $29.36 | $8.29 | US | $44.99 / $50.99 |
| Knitted Pet Sweater | $37.74+ | – | **CN only** | dead on arrival |
| Pet Collar / Leash / Collar+Leash | $17.57 / $20.17 / $33.69 | – | **CN only** | defeats the pivot |

Reviews on Printful's own Pet Bowl page complain of DHL carriage, weeks-long
transit and "shipping cost is 2x what it would cost for USPS priority" — treat
the bowl as weak despite passing arithmetic.

## VERIFIED: Printify (their own catalogue API, printify.com/product-catalog-service, no auth)

**The depth and economics winner.** 18 pet blueprints, 14 US-produced, and the
API exposes per-provider cost, real US shipping, production days AND Printify's
own provider quality scores.

Viable at the 20% floor with ≤7-day production, all US-made, free-shipped:

| SKU | Provider (quality/10) | Cost+Ship | Retail | Margin | Prod days |
|---|---|---|---|---|---|
| Clip-on Pet Bandana | Taylor (9.1) | $8.92+$5.69 | **$19.99** | 20.1% | 1.7 |
| Pet Tag (engraving) | Taylor (9.1) | $8.72+$5.69 | **$19.99** | 21.1% | 4.9 |
| Pet Tag (print) | Printed Mint (8.6) | $11.49+$5.69 | $23.99 | 21.9% | 2.1 |
| Clip-on Pet Collar | Taylor (9.1) | $13.07+$5.69 | $25.99 | 21.4% | 1.9 |
| Pet Bandana (tie) | Printed Mint | $14.53+$5.69 | $27.99 | 21.4% | 2.0 |
| Pet Feeding Mat | MWW On Demand (8.0) | $16.88+$6.09 | $31.99 | 22.0% | 1.8 |
| Pet Bandana Collar | Printed Mint | $17.93+$5.69 | $32.99 | 22.2% | 2.1 |
| Pet Tank Top | Printed Mint | $23.15+$5.99 | $39.99 | 21.1% | 2.2 |
| Leather Pet Collar (engraving) | Fulfill Engine (8.5) | $23.03+$5.89 | $39.99 | 21.7% | 6.2 |
| Pet Food Mat 12×18 | Printed Mint | $21.56+$8.09 | $40.99 | 21.7% | 2.0 |

Borderline: Pet Bowl $52.99, Pet Bed $76.99 (ship $27.29!). Dead: Retractable
Leash (14.9-day production). UK-only (skip): Pet Hoodie, Parka, Raglan Tee.

## VERIFIED: the rest of the POD field

* **Gooten** (browser, gooten.com): real pet line — **Dog Beds in 3 sizes,
  US production confirmed on-page**, ceramic Pet Bowls (2 sizes), Pet
  Placemats, Premium Placemats, Pet Bandanas, and **Doggie Skins dog-apparel
  blanks (tank + fleece hoodie)** — the only US POD dog-apparel found anywhere.
  Prices are account-gated; the free account is the next step. Covers the two
  gaps (beds, dog apparel) Printful/Printify cannot.
* **teelaunch**: its once-famous pet line is **dead** — site search for "pet"
  returns one human necklace and a generic blanket. Verified negative.
* **Gelato**: no pet category at all in its catalogue nav. Verified negative.
* **CustomCat**: public product grid does not render without an account
  (confirmed in browser, empty DOM). Unresolved; low priority.

## VERIFIED: multiple suppliers on ONE Shopify store — YES, natively

The question that decides whether this is a migration or an addition.

1. **Shopify's fulfillment model is built for it** (shopify.dev,
   FulfillmentOrder): every order is split into one FulfillmentOrder per
   assigned location; each fulfillment app sees ONLY its own; multiple apps
   coexist and fulfill in parallel on the same order.
2. **Printful documents the mixed case explicitly** (help.printful.com,
   "What happens when an order contains both..."): the order auto-splits,
   Printful fulfills its items, "you or your other provider update the rest",
   and checkout shows separate shipping per group once **Split Shipping** is
   enabled in Settings → Shipping and delivery.
3. **Wagvive's own store is already shaped for it**: all 232 live variants are
   `fulfillment_service: manual` at Shop location, and CJ fulfils by reading
   orders and pushing tracking regardless of location (the order #1001
   precedent in CLAUDE.md). New POD products would be created BY the POD app,
   assigned to ITS location. The repo's documented trap — fulfillment service
   on existing variants cannot be reassigned — is irrelevant under this
   pattern, because nothing existing is reassigned.

Customer-facing consequences to design for: a mixed cart ships as separate
parcels with separate tracking emails, and shipping rates need Split Shipping
so each group prices itself. Kits must stay single-supplier per kit (already
required for margin anyway).

## What this settles (pending the census workflow's dropship lanes)

* POD depth ranking for dogs: **Printify (10 viable US SKUs) > Printful (4–6)
  > Gooten (unique beds + dog apparel, prices TBC) >> everyone else (no line)**.
* A Printify+Printful+Gooten stack covers: bandanas (3 forms), collars incl.
  engraved leather, tags incl. engraved, feeding mats (3 sizes), bowls,
  blankets, dog beds, dog tank/hoodie. Price band $19.99–$50.99 at 20–22%
  margins — exactly the owner's "charge more for quality" band.
* POD cannot make: grooming tools, enrichment/puzzle toys, plush, slow
  feeders, cooling mats, calming wraps. Those categories either stay dropship
  (census pending), get retired, or wait.
* CJ can remain live during any transition without technical conflict.
