# Pre-spend audit: the Calm & Comfort Kit page

Phase 1 of the marketing plan puts $150 of Pinterest traffic onto exactly one
page, `/products/calm-comfort-kit`. This is that page checked before the money
is committed, because the plan's own decision rule says a conversion problem is
fixed on the site rather than in the ads.

Audited 2026-08-05 against the live Admin API and the live Horizon theme.

**A note on method.** The sandbox this session runs in cannot reach wagvive.com;
curl returns `000` and WebFetch returns 403, both blocked at the proxy. So this
is not a rendered-page review. It is the product record and the theme source
that produces the page, which catches content and configuration faults but not
layout or visual ones. **Somebody still needs to look at the page on a phone.**

---

## The finding that matters: a broken block on every product page

The theme's "Care & use" accordion currently reads:

> Rinse or wipe clean after use and let it dry fully before storing. Introduce
> new grooming tools gradually, a few short, calm sessions beat one long one,
> especially with older or anxious dogs.

On the Calm & Comfort Kit that is wrong three separate ways:

1. **"Rinse or wipe clean and let it dry fully."** The kit is a heartbeat plush
   sloth, a compression wrap, a fleece blanket, a cooling pad and a big squeak
   plush. Not one of them is rinsed. A buyer who follows this instruction ruins
   the plush.
2. **"Grooming tools."** There are none in this kit.
3. **"Older or anxious dogs."** Senior positioning was retired when the Senior
   Dog Kit went. The homepage FAQ was fixed for precisely this reason. This block
   was missed.

It is a global block, so it says the same wrong thing on all 42 product pages,
including the disposable wipes.

**This is task #71, and it was never applied.** The exact find-and-replace text
has been sitting in `docs/qa/theme-copy-fixes.md` since 2026-08-04. The task has
also quietly fallen out of the current handoff: the task-number warning covers
the #73 to #82 range, and #71 simply vanished in the rewrite rather than being
closed.

The same four edits also fix four live style violations:

| Where | Live text | Problem |
|---|---|---|
| Trust badge | `Ships in 1&ndash;3 business days` | en dash, and a hyphenated day range |
| Accordion, Shipping | `1&ndash;3` and `5&ndash;12 business days` | two en dashes |
| Accordion, Returns | `Changed your mind is fine too &mdash; return postage...` | em dash |
| Accordion, Care & use | `gradually &mdash; a few short...` | em dash, plus the three content faults above |

All four contradict the standing rule in `CLAUDE.md`: no em or en dashes
anywhere on the site, no hyphenated day ranges, write "5 to 12 business days".

**Fix this before spending anything.** It is about five minutes in the theme
editor and the replacement text is already written.

---

## What is right, and should not be touched

Worth stating so the fixes above do not turn into a rebuild of a page that is
mostly working.

| Check | State |
|---|---|
| Price and compare-at | $109.00 against $135.95. The $135.95 is **exactly** the sum of the five components at their current single prices. Verified against the price book. Honest, and legally safe. |
| Description | Accurate. Names all five components and matches the live bundle composition exactly. |
| Stock | 5,104 per variant, all available for sale |
| Sticky add to cart | On |
| Accelerated checkout | On, so Shop Pay and friends appear |
| Trust badges | Free shipping over $60, 30 day returns, dispatch time. All three present above the fold area. |
| Kit contents section | Renders, and cross-links each component |
| Media | 6 images: the kit cover plus one shot of each component, all on the cream background |
| Recommendations | "You may also like", 4 related products |

---

## Three things to decide before the campaign

### 1. No SEO title or description

Both are `null` on this product, so Shopify falls back to the product title and
a truncated description.

That is survivable for paid clicks, which land on the page directly. It is not
survivable for the two free channels the plan depends on: **Pinterest rich pins
read the meta description**, and Google free listings use it. Since the same
page is meant to carry both, it should be written.

Suggested, and I can apply these on your word since they change no price or
product:

- **Title:** `Dog Anxiety Kit: Heartbeat Toy, Calming Wrap and Cooling Mat`
- **Description:** `Five pieces that work on the same problem from different
  sides. A heartbeat plush, a compression wrap, a cooling mat, a fleece blanket
  and a squeak plush, for storms, fireworks and being left alone. Free US
  shipping over $60.`

Note this is the same principle as the feed titles in `feed_health.py`: describe
the product the way a shopper types it, never lead with the brand, and never
change the on-site title.

### 2. Thirty six variants, and three choices before checkout

The kit has three option dimensions: Thunder Wrap colour (3), Blanket colour (3),
Cooling Pad colour (4). That is 36 variants.

Shopify preselects the first available combination, so **Add to cart works
without touching anything** and this is not a blocker. But a stranger arriving
from Pinterest on a $109 first purchase now sees three rows of colour buttons
before the buy button. Every one is a small invitation to think harder.

I am not recommending a change, because the colours are genuine and removing
choice on a gift-shaped product may cost more than it saves. I am flagging it as
**the first thing to test** if the campaign gets clicks and no orders. The plan's
kill rule already says change the creative, not the budget; this would be the
page-side equivalent.

### 3. $109 is the most expensive thing in the store

The plan picks this kit for phase 1 on contribution ($43.06) and breakeven
conversion (0.8%), and that arithmetic is right. The unstated assumption is that
conversion rate does not move with price. It does, and a $109 first purchase
from a brand with **no reviews at all** is the hardest ask in the catalogue.

I would still start here, because the headroom is real and the emotional trigger
is the strongest we have. But the fallback should be decided now rather than
argued about in week 4:

| If phase 1 shows | Then |
|---|---|
| Clicks arriving, 0 orders after $75 | Test the New Puppy Kit at $54. Contribution $30.61, breakeven 1.1%, and a far easier first purchase. |
| Clicks arriving, orders at 0.8%+ | Working as designed. Continue. |
| No clicks | Creative problem, not a page problem. Do not touch this page. |

---

## Recommended order

1. **Apply the four theme fixes** from `docs/qa/theme-copy-fixes.md`. Owner, in
   the theme editor, about five minutes. Blocks nothing else but should not ship
   traffic without it.
2. **Add the SEO title and description.** Claude, on your word.
3. **Verify with the section rendering API, not the cached page.** The cached
   homepage served stale renders for over seven minutes after a footer write, and
   `?nocache=` does not help because it is not part of the cache key.
4. Then, and only then, phase 1.

Nothing above has been applied.
