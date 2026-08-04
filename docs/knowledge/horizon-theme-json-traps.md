---
name: horizon-theme-json-traps
description: "Horizon JSON template traps — placeholder cards that look real, handles not gids, static block keys, and the checks that catch them"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-02T17:05:51.353Z
---

Traps hit while editing Horizon theme JSON via the Assets API (all found 2026-08-01,
during the homepage refresh):

**Product rows can silently render PLACEHOLDER cards that pass a casual look.** If a
`product-list` section's `collection` setting fails to resolve, the theme renders
`max_products` fake cards reading "Product title / $19.99" with grey boxes. In a
screenshot thumbnail they pass for real products. The homepage favorites and kit rows
had been placeholders for an unknown time. **Check: fetch the section with
`/?sections=<section-id>` and grep the HTML for "Product title" (placeholder) and for
real product names.**

**Resource settings in JSON templates take HANDLES, not gids.** `"collection":
"frontpage"` works; `"gid://shopify/collection/…"` and even correctly-cased
`"gid://shopify/Collection/…"` silently resolve to blank (no error on PUT).
Same for `collection_list` arrays. Image pickers use `shopify://shop_images/<file>`,
videos use `shopify://files/videos/<filename>` (these DO work).

**Static block keys must match the `id:` in the section's `content_for 'block'`.**
`sections/product-list.liquid` calls `content_for 'block', type: '_product-card',
id: 'static-product-card'`. The JSON entry must be keyed `"static-product-card"`.
Keyed anything else ("card"), the block renders with defaults and — because the
gallery/title/price live as CHILDREN of the mis-keyed entry — the card body renders
empty (a 0-height anchor). The working reference is templates/product.json, which
uses the correct key.

**Template JSON needs its own dash sweep.** dedash.py covers products, pages,
collections, policies and my snippets, NOT templates/*.json. Blind entity replacement
there is dangerous: `1&ndash;3` became "1, 3 business days" and an em-dash clause
became a comma splice. Number ranges must become "1 to 3", not "1, 3".

**Section padding caps at 100** (`padding-block-*`); the PUT 422s above that. Use
`section_height` for tall bands.

**Background-tab video ≠ broken video.** Chrome never paints video frames in
non-selected tabs, so screenshots show the section background color where the video
belongs, and `readyState` stays 0. Verify by checking `currentTime` advances in a
foreground context (the in-app pane counts), not by screenshot.

**The one-supplier claim keeps resurfacing.** After the story band was fixed, the
same claim was found AGAIN in the homepage values section ("ships from a single
partner we audited"). When rewording a claim, grep the whole template for it, not
just the section that surfaced it. See [[wagvive-sourcing-rules]].

Storefront password gate: REMOVED 2026-08-02 (user flipped the toggle after the
full address saved — Shopify hard-gates removal until street + city + state + zip
are ALL present in Settings > Store details; province+zip alone keeps the gate up).
The site is public; the old password was "eavite".

**Homepage SEO is managed in CODE, not Online Store preferences** (2026-08-02): the
preferences fields sit in a cross-origin iframe (online-store-web.shopifyapps.com)
that can't be scripted, isn't in the extension's a11y tree, and has no public API.
Instead `snippets/meta-tags.liquid` carries a Wagvive override block: on
`request.page_type == 'index'` it assigns seo_title (54 chars, "Wagvive | Premium
Dog Toys, Grooming & Enrichment Kits"), seo_description (149 chars), and emits
og:image from theme asset `assets/og-share.png` (1200x630, built from
config/branding/logo-horizontal.png + kit covers; generator inline in session,
source image at config/branding/og-share-1200x630.png). Product/collection pages
keep default behavior. If anyone later fills the preferences fields, the code
override still wins on the homepage — edit the snippet, not the admin form.
Verifying live tags: Shopify CDN serves MIXED stale/fresh renders for minutes after
an asset PUT — check title AND description in the SAME fetched document with a
unique ?nocache= param before concluding anything is missing.
