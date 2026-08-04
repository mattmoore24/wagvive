---
name: wagvive-placeholder-product-art
description: All 8 Wagvive product SKUs now use real CJ supplier photos; only the 2 bundle-kit images are still illustrations
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-01T21:12:31.765Z
---

**Photography is a valid reason to reject a product outright.** The Dental & Ear Wipes were
dropped from both kits on 2026-08-01 purely on imagery: every CJ frame is a branded plastic can
with a cat on the label. A full catalogue sweep for a replacement found nothing better — the
best-scoring alternative loses the dental and ear functions entirely, and the runner-up carries
another manufacturer's retail packaging in every full-size frame. The fix was to change the
*slot*, not the product: both kits now use the existing Finger Toothbrush, which is
brand-neutral, cheaper, and lighter. The wipes stay on the site as a standalone. When no
sourceable product photographs well, reach for something already in the catalogue before
accepting bad imagery.

Wagvive product imagery as of 2026-07-28:

- **All 8 product SKUs use real CJ supplier photos.** The last two holdouts were fixed:
  the nail grinder (gallery found on `oss-cf.cjdropshipping.com/product/...`) and the bed
  (replaced entirely — see below).
- **Only the 2 bundle-kit images are still illustrations** from
  `config/branding/generate_product_art.js`.

**How to pull CJ images:** their pages are client-rendered and `curl` hits a bot wall, but
`fetch()` from inside a logged-in CJ browser tab returns full SSR HTML. Galleries live on
several hosts — `cf.cjdropshipping.com`, `oss-cf.cjdropshipping.com/product/...`,
`oss.cjdropshipping.com/product/...`, and `cc-west-usa.oss-accelerate.aliyuncs.com`. URLs are
JSON-escaped as `\/`, so unescape before matching. The CDN itself needs no auth. See
`config/branding/upload_real_photos.py` and `config/swap_bed.py`.

**CJ catalogue search works too** — list pages embed `window.PRODUCTSRES` (a JS literal, not
strict JSON: replace `:undefined` with `:null` and bracket-match to extract it). Names are
blank there, but each row has an `id`, and `/product/x-p-<id>.html` resolves to the detail
page regardless of slug, where `<title>` and `"supplierId"` are readable.

**De-branding:** `config/branding/debrand.js` removes third-party logos with a gradient-aware
fill. Used on the water bowl's "els pet" moulded logo. Re-check any newly added photo.

---

**2026-08-02: the entire catalogue was re-shot with Runway (nano-banana-2; pro for label-bearing
tubs).** All 19 standalone products now use AI studio photography on the brand cream (#F7F2E9):
master + pose-locked colour recolors + one lifestyle shot each, plus locally composed (PIL, real
type) size-guide cards for the cooling pad and sofa cover. Kit covers were recomposed from the new
masters. Every one of the 81 variants has an image association, so swatches swap photos.
`config/reshoot_state.json` maps every shot to its Runway task id; `config/apply_reshoot.py`
uploads manifests and wires variants.

**Pipeline rules that survived contact with reality:**
- Master first, then recolor THE APPROVED MASTER for other colourways: only way to pose-lock.
- Describe the product from LOOKING at the reference, never from its name. Two near-misses:
  the "waterproof cover" is a plush sherpa throw (model invented a quilted strapped cover),
  and the "shedding gloves" are a fingerless oval mitt (model drew a five-finger glove).
- The model invents props: display stands, embossed logos, fake-branded treat pouches in
  backgrounds. Every prompt carries a no-props/no-text/no-packaging clause AND every output
  still gets eyeballed against its CJ reference before upload.
- Character/animal variants must come from CJ per-variant images (`/product/query` ->
  variants[].variantImage); the Shopify gallery only shows a few of them.
- Labeled packaging needs nano-banana-pro and a "preserve the label EXACTLY" clause; it kept
  the wipes tub text legible where -2 would garble it.
- Reference URLs: copy verbatim from tool output. Two generations were wasted on guessed URLs.
