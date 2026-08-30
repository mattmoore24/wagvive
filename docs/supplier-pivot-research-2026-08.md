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

---

# FINAL SYNTHESIS (census workflow complete, 2026-08-30)

The 7-agent census (51 dropship partners + 26 POD providers + reliability
evidence + architecture) converged with the direct verification above.
Corrections and completions to the interim findings:

## Corrections to the interim read

* **Gooten is DISQUALIFIED on reliability despite its unique catalogue.**
  Trustpilot 3.1/226 with 22% one-star; Shopify 3.4/139. Acquired by Taylor
  Corp Oct 2025; post-acquisition reviews: "almost every single order placed
  has been wrong" (Jul 2026). It has CJ's disease in POD form. The safe route
  to the same Taylor production capacity is **Printify's Taylor provider**
  (9.1/10 provider score, verified).
* **Printed Mint DIRECT (Phoenix AZ) beats its own Printify listings by
  $3-8/SKU** - public pricelist verified: bandana $11.50 (vs $14.53 via
  Printify), tag $7.00 (vs $11.49), bowl $17.50 (vs $25.21), tank $16.50 (vs
  $23.15), small-breed hoodie $14.00, lap blanket $13.50. Ship $5.79 first +
  **$0.99 each additional item** - the ONLY cheap multi-item/kit play in all
  of POD. Own Shopify app. SLA 2-4 days production + 2-5 ship.
* **Dreamship** has the cheapest US ceramic pet bowl: $12.49 + $6.99 ship,
  clears at $29.99 (29%) where Printful/Printify bowls need $45-53.
* **TopDawg partially rehabilitated by the reliability lane**: zero one-star
  reviews anywhere (though only ~25 reviews total). Pricing structure is
  still spread-based; earns a small paid PILOT with per-SKU margin math, not
  trust.
* **PetDropShipper is $399/mo** (live Shopify app listing; the $19 blog
  figure circulating is wrong). Dead at 3 orders/month.

## The reliability tiers (evidence-based, cited in the census output)

* **TIER 1 build on**: Printful (Shopify 4.8/3,804; 97% ship <=5 days;
  US-region SKUs ONLY - its collar/leash/sweater are China-fulfilled), and
  Printify as hedge (4.7/4,435; quality varies BY PROVIDER - pin US
  providers, sample every SKU).
* **TIER 2 pilot**: TopDawg (clean but thin record), Printed Mint direct.
* **TIER 3 - CJ's disease, named and evidenced**: Spocket ("most of the stuff
  you sell will never ship"), Syncee ("60% of orders don't get fulfilled"),
  Doba (44% one-star), Zendrop (documented fictitious stock), USAdrop
  (rating suppressed), Sellvia (Trustpilot removed rating for fake reviews),
  AutoDS (orders unfulfilled a year later), EPROLO (40% of orders 2+ weeks
  late), Dropshipman, Gooten. **Every general aggregator fails on exactly the
  phantom-inventory/never-ships axis that motivated the exit.**

## Category coverage - the honest limit of POD

| Wagvive category | POD coverage |
|---|---|
| Apparel (5) | **5/5, better than CJ** (4 bandana forms, tank, small-breed hoodie + collar/leash/tag upgrades) |
| Comfort & Health (12) | ~half (beds, blankets, mats, bowls; NOT slow feeders, dental, calming, molded goods) |
| Toys & Play (19) | **0/19 - no POD provider prints a plush, squeaker, rope or chew** |
| Grooming (10) | **0/10 - POD cannot make a nail grinder or brush** |
| Kits (6) | derivative - survive only if every component does |

Toys and grooming therefore stay dropship (CJ, or a phone-verified US
specialist: Mirage #1 candidate, Pet Life $5/order own-brand, Essential Pet
zero-fee) or retire. There is no third option under the no-inventory
constraint.

## Artwork: the real migration cost

Nothing existing transfers as PRINT files - the Runway photos depict CJ's
physical goods. POD needs (1) print-ready surface art: the unit of design is
the PATTERN, not the SKU - one strong repeat deploys across bandana + mat +
blanket + tank; a 16-SKU line needs ~6-8 original patterns; and (2) product
mockups restyled through the existing Runway pipeline (~1 hr/SKU, proven
workflow). Engraved SKUs (tags, leather collar) need only a vector template
each - the personalization engine does per-order work free.

## The viable POD shelf (verified numbers, both pricing models)

16 SKUs, all US-made, all clearing 20%; charging shipping separately softens
entry prices dramatically:

| SKU | Source | Free-ship price | Ship-charged price |
|---|---|---|---|
| Small-breed bandana | Printed Mint | $22.99 (24.8%) | $15.99 + $5.79 (28.4%) |
| Pet bandana | Printed Mint | $24.99 (24.4%) | $17.99 + $5.79 (27.4%) |
| Personalized tag | Printed Mint | $19.99 (29.5%) | $12.99 + $5.79 (36.4%) |
| Engraved alu tag | Printify/Taylor | $21.99 (28.0%) | $14.99 + $5.69 (32.7%) |
| Collar bandana | Printed Mint | $25.99 (23.3%) | $18.99 + $5.79 (25.7%) |
| Small-breed hoodie | Printed Mint | $28.99 (25.5%) | $20.99 + $5.79 (25.1%) |
| Lap blanket | Printed Mint | $28.99 (27.3%) | $20.99 + $5.79 (27.5%) |
| Ceramic bowl | Dreamship | $29.99 (29.0%) | ~$21.99 + $6.99 |
| Pet tank top | Printed Mint | $31.99 (24.2%) | $23.99 + $5.79 (23.3%) |
| Feeding mats (bone/rect) | Printed Mint | $34.99 (24.8-26.3%) | $22.99-23.99 + $8.19 |
| Engraved leather collar | Printify/Fulfill Engine | $39.99 (21.7%) | - |
| AOP bandana / throw blankets / bowl 18oz | Printful US-3 | $20.99-50.99 | - |

Plus 2 recomposed kits (apparel + accessory + mat) once patterns exist.
Printed Mint's $0.99 additional-item rate makes IT the kit supplier for POD
kits.

## Multi-supplier architecture - completions from the census

Beyond the interim findings (order auto-split per location, Printful's
documented mixed-store support, Split Shipping):

* **Printful can LINK to existing Shopify products** ("Import existing
  products" + per-variant linking; Ecommerce Platform Sync API does it
  programmatically). Titles, descriptions, SEO, handles and reviews survive;
  only imagery needs replacing per the artwork section. Printify's
  equivalent exists but only unpublished Printify products can connect to an
  existing listing - clunkier.
* **Shipping-rate trap**: Shopify SUMS matching rates across shipping
  profiles ONLY when rate names are identical; differently-named rates
  collapse to a generic "Shipping". Name Printful-profile rates identically
  to the general profile - or run free-shipping in both and bake freight in.
* **Zero SKU overlap is the one hard rule** - every documented multi-app
  fight is two apps managing the same SKU. Extend the sku[:11] duplicate
  audit to cover POD SKUs.
* **FOUR REPO SCRIPTS MUST BE SCOPED TO CJ SKUS FIRST** (verified by reading
  the code): fix_locations.py would stamp available=0 onto every Printful
  variant 3-hourly; sync_inventory.py burns CJ API points quota on foreign
  SKUs; guard_unshippable.py would page on every POD variant (no CJ carrier
  quote exists); the margin/catalog audits assume CJ SKU shape. One scoping
  PR is the prerequisite for installing ANY second supplier app.
* **Kits stay single-supplier** pending one live test: native Bundles route
  components by location and nothing forbids mixed-service components, but
  mixed-supplier native kits are UNPROVEN anywhere. Printful's documented
  bundle path is the Simple Bundles & Kits app.

## The recommended shape (three lanes + bridge)

1. **POD core (install now)**: Printed Mint direct + Printify (pinned US
   providers: Taylor, Printed Mint, MWW, Fulfill Engine) + Printful (its 3
   US-region SKUs only). Covers Apparel outright and half of Comfort at
   $19.99-$50.99, 20-29% margins, 1.7-4 day US production.
2. **US specialists (phone-verify, owner)**: Mirage Pet Products (best find:
   US manufacturer, no fees, min retail ~$14 - but site broken, confirm it
   trades), Pet Life ($5/order, own-brand $25-90 goods), Essential Pet
   (zero-fee, $26+ retail). These are the only dropship path for
   toys/grooming above $20.
3. **Shopify Collective (apply, browse)**: the only route to real premium
   brands; viable only where a supplier grants ~50% margin above $35 retail.
   Zero app-conflict surface (Shopify-native).
4. **CJ stays as bridge**, product by product, until each is replaced or
   retired. Its sub-$20 toys either stay on CJ knowingly (with honest
   delivery copy) or retire - no US supplier can carry them at any price.

## Still unverified (the short list)

* Mirage Pet Products: is it trading? (site 403/404s; owner phone call)
* Printed Mint direct-app reliability at order volume (its 8.6/10 Printify
  provider score is the best proxy)
* One live mixed CJ+POD order end-to-end (place a small test order)
* A native bundle with mixed-supplier components (draft product test)
* TopDawg real shipped-vs-quoted freight (the $6.75-to-$13 blowout reports)
