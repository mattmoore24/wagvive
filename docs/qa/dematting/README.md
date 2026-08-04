# Dematting comb imagery QA (CJ SPU CJYD2754094)

State as of 2026-08-04: the product page carries **only the studio master**.
The lifestyle image was removed; a replacement is deferred.

## What is here

| File | What it is |
|---|---|
| `cj-01..14` | CJ's own product photos, the ground truth. `cj-01` is the supplier's in-use shot, `cj-04` shows both sides of the blade row. |
| `product.json` | CJ's full product record |
| `shopify-current.png` | The studio master, live on the product page. Verified accurate. |
| `shopify-lifestyle.png` | The ORIGINAL lifestyle image, removed. Its head was an invented closed hoop. |
| `lifestyle-head-crop.png` | Enlargement showing that failure |
| `rejected-v2-lifestyle.png` | A regenerated version that briefly shipped, then was pulled: the axle bar did not line up with the handle. |
| `best-attempt-v6.png` | Furthest the regeneration got. Handle/axle collinearity is correct here; the hinge and blade rendering still are not. Best starting point for another attempt. |

## The tool, for prompting

Beech teardrop handle, stainless collar ring, rounded D-shaped thumb shield
over the blade roots, and ONE OPEN ROW of 9 to 10 long straight serrated
blades whose rolled scroll hinges wrap a thin axle. **The axle is the metal
continuation of the handle: handle, collar and axle are a single straight
line, like a screwdriver shaft.** A hex nut and domed cap sit at the exposed
axle end, just past the last blade. Nothing connects the blade tips.

## What went wrong, so it is not repeated

1. **Generation reproduces the wrong head when a bad image is the scene
   reference.** The first re-shoot re-created the invented hoop because the
   old lifestyle image was passed as the scene anchor.
2. **Fixing one region breaks another.** Six rounds across nano-banana-pro,
   nano-banana-2 and seedream-5 each fixed the named flaw and introduced a
   new one somewhere else on the head: perforated straps, lollipop blade
   tops, a sword-guard shield, an axle sitting below the blades.
3. **Collinearity is the hardest constraint** and the one the owner notices
   first. Only the v4/v6 line of edits achieved it.

Anything new must be checked against `cj-02`, `cj-04`, `cj-05` and the master
at pixel zoom before upload, not just at full-frame.
