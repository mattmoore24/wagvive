---
name: wagvive-pricing-architecture
description: "How Wagvive prices are set: demand-model pipeline, competitive ceiling, kit live-quote re-rank, and the traps (sensitive-line carriers, multipack vids, CJ search useless for sourcing)"
metadata:
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-05T00:24:05.194Z
---

Since 2026-08-04 every price is set per product by a demand model, not a margin target.
Pipeline (all in `config/`): `market_bands.py` (observed low/mid/high per product; the
band must be the VOLUME seller's price, not the premium brand's — Casfuy $20/88k reviews
is the competitor, not Dremel $50) → `demand_model.py` (logistic share-of-consideration
in log price; constant elasticity was rejected because it never decays and recommends
pricing above market) → `optimise_prices.py` (maximise contribution x share, hard-capped
at mid x1.15 for outcome goods / mid for everything else) → `build_price_book.py` →
`apply_price_book.py --apply`. Floors then calibrated by `calibrate_floors.py` (see
[[wagvive-cost-model]]).

**Kits: the fitted freight curve finds candidates; only LIVE combined CJ basket quotes
may pick winners.** Carrier-eligibility rules are invisible to any weight curve: a basket
containing the Talk Button (electronics) gets forced onto sensitive/oversize lines,
nearly +$25 on a 5-item kit; the 2026-08-04 Enrichment winner-by-curve was actually -2%
live. `optimise_kits.py` enumerates, then the top ~8 per theme are re-ranked on live
`/logistic/freightCalculate` baskets before `apply_kits.py --apply` writes anything.

**When quoting baskets, the vid for each component must come from a SKU we actually
sell.** Picking a SPU's heaviest variant grabs CJ multipacks/oversizes we don't list and
inflates the quote 2-3x — the same multipack trap as the voided pricing study, wearing a
freight disguise ([[cj-shopify-connection-procedure]] has the SKU-side version).

**CJ's API cannot find products worth adding.** `/product/list` keyword search returns
newest-first listings with listedNum ~0; there is no demand-sorted search. Sourcing
means the CJ trending/hot-products UI in a browser session, never an API scan.

Kit policy: price = charm00(0.80 x sum of NEW single prices), compare_at = that singles
sum (colour never changes price; sizes pinned at the costed dearest variant, except
level-priced fit sizes like the Paw Cup, which open). Kit floor 30% (`kit_margins.py`).
