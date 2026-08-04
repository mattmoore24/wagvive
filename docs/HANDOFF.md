# Session handoff — read this first on any device

> Protocol: every Claude session starts by reading this file, and updates it
> (plus commits and pushes) before the user switches devices or ends a work
> session. This file IS the conversation continuity between devices.

**Last updated:** 2026-08-04, from a claude.ai/code web session

## Where the business stands

wagvive.com is LIVE and fully operational: 41 active products (36 singles + 5
variant-selectable bundle kits), all CJ-paired, all margin-verified above the
50% floor. First real order (#1001) completed the full loop: checkout → CJ →
paid → shipped → tracking back → branded emails from hello@wagvive.com.
Storefront password is off, SEO/social cards are set, all 18 notification
emails are branded.

Operations run themselves: GitHub Actions (`scheduled-ops.yml`) syncs CJ stock
into Shopify, repairs inventory locations, and checks margins **every 6 hours**.
A failed run emails the owner — silence means healthy.

## What just happened (most recent work)

- **CATALOGUE AUDIT (2026-08-04, web session).** Full pass over all 41 products
  against CJ source data (`docs/qa/cj-variants.json`, regenerate via the
  `cj-variant-audit` workflow by editing `config/audit_spus.json`).
  1. **Five missing lifestyle images added** and verified live: Barnyard
     Squeaker, Woodland Rope-Limb Plush, Crinkle Plush Buddy, Big Squeak
     Plush, Dental Wipes. Each generated from its own studio master and
     eyeballed against it before upload. Owner is checking accuracy
     themselves. The Pet Hair Remover Mitt and Dematting Comb stay
     master-only by owner decision.
  2. **Sizing guides written for all seven size or capacity products** from
     CJ's own charts: bath robe (by dog weight), paw washing cup, snuggle
     blanket, fleece blanket, cooling pad, sofa cover, water bowl. Copy lives
     in `config/sizing_copy.py`, applied via Admin GraphQL.
  3. **Two real copy errors fixed.** The fleece blanket's M size was listed as
     100 x 75cm when CJ says 76 x 104cm, and the sofa cover claimed its range
     reached "a full three-seater" when the largest stocked size is 39 x 57in.
  4. **Dimensions added** to the dental duck, squirrel plush, cuddle teddy,
     LED nail clippers and travel bottle. Deliberately NOT added elsewhere:
     CJ's per-variant numbers are package dimensions, and for soft goods those
     are not product dimensions. Do not treat them as such.
  5. **Variant gaps found, nothing added.** See
     `docs/qa/variant-audit-2026-08.md`. Four products are missing real sizes
     (sofa cover, snuggle blanket, fleece blanket, cooling pad) and the sofa
     cover's Small/Medium/Large are actually CJ's XS/S/M of seven. Adding any
     of them needs CJ pairing in the browser plus a margin-floor check, so it
     is owner-gated. Tracked as #67.
- (Web session, 2026-08-04) Confirmed live Shopify access works from
  claude.ai/code via the Shopify connector; capabilities section below
  rewritten to match. Added `config/fetch_cj_refs.py` + the `cj-image-refs`
  dispatch workflow so credential-less sessions can pull CJ reference images.
  Ran that workflow for the Wagvive Dematting Comb (SPU CJYD2754094; note the
  CJ query endpoint wants the SPU, not the variant SKU): our
  `master-dematting.png` matches CJ's photos feature for feature (handle,
  collar, thumb shield, tooth count and serration) — the master is ACCURATE and
  stays. Only nit: the axle's hex nut is subtler in our shot than in CJ's.
  References live in `docs/qa/dematting/`.
- The comb's LIFESTYLE image FAILED QA (owner spotted it; a 4-pass review, one
  adversarial, confirmed the tool head was invented — a closed hoop instead of
  the real open rake). Six Runway regeneration rounds across nano-banana-pro,
  nano-banana-2 and seedream-5 each fixed the named flaw and broke something
  else on the head; the version that briefly shipped was pulled because the
  axle bar did not line up with the handle. **OUTCOME: the lifestyle image is
  REMOVED. The product page now carries only the studio master** (media
  47588547887393, still featured; verified in Admin and on the live
  storefront). Owner will revisit creating one another time — everything
  needed is in `docs/qa/dematting/` with a README: CJ ground truth, the two
  failed images, the best attempt (`best-attempt-v6.png`, correct
  collinearity), and the prompt description of the real tool. Tracked as #65.
  The other 40 products' lifestyle images have NOT been audited — tracked as
  #66, and the more important of the two, since this one was live since launch.
- CJ's stock-writing disabled store-wide via the authorization page's Sync
  Settings → "Not Sync" (see docs/knowledge/cj-inventory-sync-model.md, "kill
  switch"). `sync_inventory.py` is now the ONLY inventory writer. Verified: 144
  variants, zero double-counts, zero out-of-stock, CJ↔Shopify parity exact.
- Archived duplicate product "Wagvive Sneaker Squeaky Toy" (same CJ SPU as
  Sneaker Chew Buddy, and its colour names were wrong). New audit rule: check
  for duplicate source SKUs (`sku[:11]`), not just titles.

## Open tasks, in priority order

| # | Task | Status / notes |
|---|---|---|
| 59 | GA4 + Meta pixel | NEXT UP, but owner-gated: needs a GA4 measurement ID (G-XXXX) and a Meta pixel ID from the owner's own accounts. Once those exist Claude installs both. Store has zero analytics; blocks #62 and any ad spend. |
| 71 | **Fix four dashes and the wrong care text on every product page** | NEW 2026-08-04, OWNER ACTION, quick. `templates/product.json` carries two en dashes in the shipping copy, one in a trust badge, one em dash in returns, and a "Care & use" block telling customers to rinse and dry the product before storing, which is wrong for disposable wipes and plush toys and still mentions "older or anxious dogs". Claude CANNOT fix this: live theme writes are refused by policy. Exact find and replace text is in `docs/qa/theme-copy-fixes.md`, about five minutes in the theme editor. Every other theme file was scanned and is clean. |
| 67 | **Add the 41 missing size variants (HOME PC)** | NEW 2026-08-04. Four products are missing sizes CJ actually sells. **Exact SKU list with CJ costs is in the appendix of `docs/qa/variant-audit-2026-08.md`** so pairing is mechanical: sofa cover 12, snuggle blanket 9, fleece blanket 12, cooling pad 8. Sequence: (1) owner pairs each SKU in the CJ browser app, one product at a time, verifying `matchitem.shopType === 'Shopify'` before confirming; (2) Claude resolves freight via `freight_floor.py` and prices each size to clear the 50% floor, levelling colours as usual; (3) Claude creates the Shopify variants and wires variant images. Freight, not product cost, will decide whether the biggest sizes are viable, so expect some to fail the floor and be dropped. |
| 67a | Rename the sofa cover's size labels | Depends on #67. Our Small/Medium/Large are CJ's XS/S/M of seven sizes, so the labels stop making sense the moment bigger sizes are added. Rename to the true range at the same time. Renaming option values rewrites variant titles, so do it in one pass with the additions, not before. |
| 68 | Decide on lifestyle images for the five kits | NEW 2026-08-04. All five kits (New Puppy, Toy, Grooming Essentials, Enrichment, Travel) have a cover plus component shots and no in-use photo. That looked deliberate so nothing was changed. If you want them, the components are already shot and a kit scene is straightforward. |
| 69 | Real product dimensions for the remaining products | NEW 2026-08-04. Dimensions were added only where CJ states them explicitly. For most toys CJ publishes package dimensions only, which for soft goods are not product dimensions, so nothing was stated. To finish this properly, either measure samples on arrival or ask CJ for product dimensions per SKU. Do NOT infer from `variantLength/Width/Height`. |
| 70 | Consider larger wipe counts | NEW 2026-08-04, low priority. The Dental & Ear Wipes sells 50-count tubs; CJ also offers 100, 150 and 200 count. Merchandising opportunity, same pairing mechanics as #67. |
| 66 | Audit ALL lifestyle images against CJ references | PARTLY DONE 2026-08-04: every product now HAS a lifestyle image except the two the owner excluded, and all descriptions were checked for sizing accuracy. Still outstanding: confirming each existing lifestyle image actually depicts the right product, which the owner is doing themselves. Fully unblocked — no owner action, tooling already built (`cj-image-refs` workflow + `config/fetch_cj_refs.py`). The dematting comb's "in use" photo depicted a tool that does not exist and had been live since launch; the rest of the catalogue has never been checked the same way. Misleading imagery drives returns and chargebacks, so do this BEFORE paying for traffic. Method and failure patterns: `docs/qa/dematting/README.md`. |
| 63 | Post-purchase reviews | Biggest untouched conversion lever. Judge.me free tier or similar; needs app install (owner clicks, Claude configures). |
| 57 | NY sales tax registration | OWNER ACTION: file DTF-17 at NY Business Express (needs SSN/EIN). Then Claude adds the Certificate of Authority number in Shopify tax settings. |
| 64 | DDP/DDU confirmation with CJ | Owner raises a CJ ticket (order-gated; order #1001 exists now). Margin model assumes duties included — DDU would mean surprise customer charges. |
| 60 | TikTok Shop | Blocked on repricing pass: TikTok commission (~6-8%) is a fee layer the 50% floor model does not yet include. |
| 61 | Short-form video for social-first products | Runway videos for screaming chicken, talk button, paw washing cup, LED clippers. |
| 65 | Recreate the dematting comb lifestyle image | Deferred by owner 2026-08-04 after six failed regeneration rounds. Product page currently ships master-only, which is accurate, so this is cosmetic not urgent. Start from `docs/qa/dematting/best-attempt-v6.png` (handle/axle collinearity already correct). Prompting alone has not worked — consider compositing the master's tool into a scene, or a photographed sample, before burning more Runway credits. |
| 62 | Ad-spend guardrails | Blocked on #59. |

## Device capabilities — what works where

**Any device (claude.ai/code on the repo):** planning, research, copy, code,
email templates, audits of committed state, editing the Actions workflow.
**Live Shopify edits work from web sessions too** when the Shopify MCP
connector is attached (verified 2026-08-04): products, collections, inventory,
orders, discounts, plus arbitrary Admin GraphQL reads/writes. A Runway
connector is typically attached as well. What web sessions still CANNOT do:
run the repo's Python scripts live (`config/*.env` are gitignored and exist
only on the PC; the sandbox's network policy also blocks direct calls to
Shopify/CJ domains — only the connectors get through), and anything CJ-side.
For CJ API reads without credentials, dispatch the `cj-image-refs` workflow
(fetches a product's record + images and commits them to the branch), or
route work through the Actions job. Pricing changes should still be computed
against `config/pricing.py` logic before any write.

**Queued for the next home PC session:** #67 and #67a (pair 41 new size
variants, then price and create them), plus anything in #70 if wanted. #57
(NY tax filing) and #64 (CJ DDP ticket) are also owner actions waiting.

**Home PC only:** CJ UI work (pairing, sync settings — no API exists),
Shopify admin settings screens (do not render in background tabs), visual
storefront QA in the user's logged-in Chrome, and anything needing
`config/shopify.env` / `config/cj.env` which live only there.

## Standing rules (full set in CLAUDE.md — binding)

50% margin floor after all costs · never enter the owner's credentials ·
confirm before spending money or irreversible actions · hello@wagvive.com is
the only customer-facing email · no em-dashes or hyphenated ranges in store
copy · verify against the live system, never trust a write's return value.

## How to hand off

Before ending a session or switching devices:
1. Update this file (state, open tasks, what changed, anything in flight).
2. Commit and push everything.
3. Tell the user the handoff is committed.

On this session's device (home PC) the prior chat history also survives
locally — but treat THIS FILE as the source of truth for state, because other
devices may have moved things since.
