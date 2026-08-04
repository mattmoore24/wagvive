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

- (Web session, 2026-08-04) Confirmed live Shopify access works from
  claude.ai/code via the Shopify connector; capabilities section below
  rewritten to match. Added `config/fetch_cj_refs.py` + the `cj-image-refs`
  dispatch workflow so credential-less sessions can pull CJ reference images.
  Ran that workflow for the Wagvive Dematting Comb (SPU CJYD2754094; note the
  CJ query endpoint wants the SPU, not the variant SKU): our
  `master-dematting.png` matches CJ's photos feature for feature (handle,
  collar, thumb shield, tooth count and serration). No Runway re-run needed.
  Only nit: the axle's hex nut is subtler in our shot than in CJ's. References
  live in `docs/qa/dematting/`; owner has the side-by-side for final say.
- The comb's LIFESTYLE image (`ls-dematting.png`, second on the product page)
  FAILED QA: the owner spotted it, and a 4-pass review (one adversarial)
  unanimously confirmed the tool head was invented — a closed oval loop with
  internal wires and ball caps instead of the real open rake. RESOLVED same
  day with owner approval: regenerated in Runway (nano-banana-pro; master as
  product reference + old lifestyle as scene reference, then a targeted
  retouch pass to fix the axle hinge/hex-nut area), verified by two
  adversarial review passes, uploaded via Admin GraphQL as
  `ls-dematting-v2.png` (media 47616876806433, alt "Wagvive Dematting Comb in
  use"), old media deleted, storefront re-fetch confirmed master first +
  new image second. Approved copy: `docs/qa/dematting/lifestyle-approved.png`.
  LESSONS: prompting alone doesn't stop head hallucination — a full re-shoot
  reproduced the wrong head when the bad image was the scene reference, and
  one candidate of each batch failed; generate 2, pick, retouch, re-verify.
  The other 40 products' lifestyle images have NOT been audited (owner
  deferred; likely more of these lurking).
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
| 59 | GA4 + Meta pixel | NEXT UP. Store has zero analytics; needed before any ad spend. Requires owner's Google/Meta accounts. |
| 63 | Post-purchase reviews | Biggest untouched conversion lever. Judge.me free tier or similar; needs app install (owner clicks, Claude configures). |
| 57 | NY sales tax registration | OWNER ACTION: file DTF-17 at NY Business Express (needs SSN/EIN). Then Claude adds the Certificate of Authority number in Shopify tax settings. |
| 64 | DDP/DDU confirmation with CJ | Owner raises a CJ ticket (order-gated; order #1001 exists now). Margin model assumes duties included — DDU would mean surprise customer charges. |
| 60 | TikTok Shop | Blocked on repricing pass: TikTok commission (~6-8%) is a fee layer the 50% floor model does not yet include. |
| 61 | Short-form video for social-first products | Runway videos for screaming chicken, talk button, paw washing cup, LED clippers. |
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
