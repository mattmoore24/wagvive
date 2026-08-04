---
name: wagvive-sourcing-rules
description: Wagvive sourcing policy — pick best quality and margin regardless of CJ supplier; freight weight is the binding constraint
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-07-30T00:50:27.415Z
---

**Supplier consolidation is no longer required** (decided 2026-07-29). The earlier rule
"use one supplier (CJ in-house / PREMIUMGOODS) for all SKUs" is **superseded**: choose the
best-quality, best-margin product regardless of which CJ supplier it comes from. US-warehouse
stock is only available via third-party suppliers, so consolidation and fast delivery are
mutually exclusive.

**Consequence:** site copy claiming "one vetted supplier" / "every product ships from a single
audited partner" is no longer true and must be reworded. It appears on the homepage value
props and the About page.

**Freight is the binding constraint, not product cost.** Measured against CJ's freight
calculator (CN -> US), 2026-07-29:

- Under ~700g, freight sits near a **~$3 floor** and barely varies with weight.
- ~2kg costs **~$46**. ~3.75kg costs **~$108**. Over ~5.5kg **no carrier will accept it at all**.
- Freight depends on product *category* as much as weight — liquids, powders and electronics
  are restricted to expensive lines. A 35g glove quoted $4.94 while a 705g 4-item parcel quoted $3.00.
- **Consolidated multi-item parcels are far cheaper than the sum of their parts** — the
  Grooming kit's 4 items ship for $3.00 vs ~$28 shipped individually. Bundles are the margin play.
- Cheapest carriers often run 10-30 days, which conflicts with the site's 5-11 day promise.
  Promise-compliant carriers cost more.

**Rule of thumb: reject anything over ~1kg shipped from China.** This killed the original
Cooling Comfort Mat (2,020g) and Orthopedic Comfort Bed (3,750g); both were archived.

Watch for **implausible CJ weights** — a 40x22x20cm steel double bowl listed at 135g returned
$0.00 freight, which is a data error, not free shipping. Verify suspicious weights before
pricing on them. See [[cj-shopify-connection-procedure]].

---

**Round-2 sourcing outcomes (2026-08-02), all eyeball-verified before commitment:**

- **The 50% floor caps "cheap toys" at ~$14-17 retail from China.** Even a $0.35 toy needs
  ~$14 once freight ($4-6 minimum) and the fee stack land. Achieved entry tier: Bouncy Egg
  $16.99, Talk Button $18. The 3-for-15% toy discount is what makes them read cheap.
- **listedNum ranks candidates but NEVER commits them.** The top water bottle (listed 2014)
  was a 285ml novelty ball printed "Love With Style"; the top cheap toy was a Halloween
  pumpkin; the only treat pouch was cartoon-printed merch. All rejected on sight. The
  runner-up bottle (CJDT2874873, listed 325) won because its PLAIN variants have no print.
- **No viable hair-remover roller exists on CJ** (zero candidates in Pet Hair Removers &
  Combs, 4 pages). The mitt (listedNum 4818, $0.95) stays, repositioned furniture-first
  ("Pet Hair Remover Mitt") with a seedance demo video on the PDP.
- **Kit lineup is now five:** Grooming, New Puppy, Toy, Dog Enrichment (slow feeder +
  anti-spill bowl + lick bowl + talk button, 57.6%), Travel (bottle + LED dispenser +
  cooling pad + frisbee, 63.0%). Senior Dog Kit retired; its components redistributed.
- **CJ /product/list has no keyword search** — category scan + name regex + list-price
  prefilter, then economics() only on finalists. The category tree comes from
  /product/getCategory once.
- **CJ "Alex" onboarding popup** on the connection page eats synthetic clicks
  (cross-origin overlay); pairing new products needs one human dismissal first.

**Round 4 (2026-08-02, +14 products):** social-video lens added to the standing rules -
motion/interaction/before-after beats static commodities. Winners: sneaker chew toy,
jingle ball, companion teddy, corduroy squeak pals (listed 241), screaming chicken,
bathrobe towel (listed 2999), LED nail clippers (real clipper variants are $3.78/220g -
the $0.36 row is a brush accessory; always price the variant you sell), dematting comb,
paw trimmer, paw washing cup, waterproof blanket (M size dropped: 770g -> $49 need,
off-market), thunder wrap, heartbeat sloth, budget fleece (S/M only). Market reality at
CJ: NO viable water fountain (real units 920g -> $86+ need), no snuffle mat, no steam
brush, lick mats over-market. CJ variant NAMES lie (sneaker "Yellow" ships royal blue -
its variantImage is ground truth; rename Shopify option values to match the image).
Build artifacts: config/round4_manifest.json (floor-verified prices/carriers),
config/round4_product_ids.json, scratchpad round4/ (all renders + task maps).
