---
name: shopify-liquid-and-cdn-traps
description: "Liquid will not index an array with a variable (fails silently); theme assets GET and storefront HTML are both eventually consistent, so verify by polling"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-07T17:46:38.988Z
---

Three Shopify behaviours that make a working change look broken, or a broken
change look fine. All three cost real time on 2026-08-07 building the kit
callout.

**1. Shopify Liquid will not index an array with a VARIABLE.** `arr[0]` works;
`{% assign i = 0 %}{{ arr[i] }}` evaluates to nil. Nothing raises, nothing logs,
the surrounding markup just disappears. Proven live with an HTML-comment probe:
`{% assign zz = 0 %}{{ kl[zz].title }}` rendered empty while the same list
iterated correctly in a `for` loop on the same page.
**How to apply:** never "find the best index then look it up". Capture the object
inside the loop with `assign winner = item`, and compare later items by a stable
field like `.handle`. Assign is global in Liquid, so it survives the loop.

**2. The theme assets endpoint is eventually consistent.** A GET issued right
after a PUT can hand back the pre-write body. Reading once and failing on it
reports a successful upload as broken.
**How to apply:** poll a few times with backoff before believing a verification
miss. `config/deploy_snippet.py` does this.

**3. Storefront HTML serves mixed stale and fresh renders for MINUTES, and
`?nocache=` does not reliably defeat it.** Across two consecutive verifier runs
the same product pages passed and failed alternately, in different combinations.
A single fetch proves nothing either way.
**How to apply:** retry per page before reporting a failure. Only a failure that
survives several spaced fetches is real. See `config/verify_kit_callout.py`.

**4. The ADMIN API's product-list endpoint can serve stale embedded variants for
MINUTES after a successful write - this is not a storefront/CDN issue, it is the
Admin REST API itself.** Found 2026-08-18 repricing the fall lineup: six variant
PUTs all returned 200 immediately (`X-Shopify-Shop-Api-Call-Limit: 1/40`, proof
each request landed). A `products.json?handle=X` re-fetch straight after showed
some variants on the OLD price and some on the NEW one - looked exactly like a
partial write. It was not: fetching the SAME variant IDs directly via
`variants/{id}.json` showed every single one already correct, with an
`updated_at` timestamp from the moment of the original write. The embedded
`variants` array on the product LIST/SHOW endpoint was the only thing lagging;
the variant resource itself was never wrong. Confirmed the other direction too:
re-issuing "corrective" PUTs based on the stale list read were harmless no-ops.
**How to apply:** never trust `products.json?handle=X` (or the equivalent
GraphQL product query) to verify a variant-level write you just made. Re-fetch
the SPECIFIC variant(s) by ID with `variants/{id}.json`, or wait and retry the
list endpoint several times before concluding a write failed. This is exactly
the same shape as traps 2 and 3 above (read the fastest/most convenient endpoint
first, believe a single miss) applied to the Admin API instead of the storefront
or theme assets endpoint - the fix is the same discipline: retry before
believing, and know which endpoint is actually the source of truth.

The general lesson, and the reason CLAUDE.md insists on live verification: when a
Shopify write "did nothing", suspect the READ before rewriting the logic. Probe
the actual values with a temporary HTML comment (storefront) or the specific
resource ID (Admin API) rather than reasoning about what ought to be true, and
rather than trusting the first convenient endpoint you already had open.

Related: [[horizon-theme-json-traps]], [[shopify-admin-ui-automation-limits]]
