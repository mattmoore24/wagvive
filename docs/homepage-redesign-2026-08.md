# Homepage redesign, kits-first — research, decisions, and what shipped (2026-08-08)

Applied by `config/homepage_kits_first.py --apply` and verified live. Rollback is
`config/theme-backup/templates__index__2026-08-08-pre-kit-redesign.json` (PUT it
back to `templates/index.json`).

## 1. The problem, in our own numbers

The homepage led with eight SINGLE products ("The favorites") and put the kit
grid seventh and eighth, several screens down. Our unit economics say that is
backwards:

| Offer | Contribution | Note |
|---|---|---|
| Average single | $4.71 | needs a 19% conversion rate to break even on a $0.90 click |
| Kits | $16.76 to $43.06 | Calm & Comfort highest at $43.06 |

The marketing plan's one-line conclusion is "never advertise a single product,
kits only" — and the homepage is our biggest free ad. It also carried stale
facts: "Five kits" (there are six), "bundles four essentials" (kits are 4 or 5),
a bundle blurb that omitted Calm & Comfort entirely, and two British spellings
("ageing", "grey muzzles").

## 2. What the top performers actually do (checked live, not from memory)

**Gymshark** (gymshark.com, read 2026-08-08): leads with BESTSELLERS as product
cards carrying real prices and review scores, two shelves deep, before any
brand story. Then guide content ("Leggings Guide", "Sports Bra Guide") that
routes undecided shoppers, then a large SEO footer. Merchandising first,
story later.

**Skims** (skims.com, read 2026-08-08): remarkably lean. One campaign hero with
a single Shop Now, then three or four full-width category tiles, each with ONE
benefit line and ONE CTA ("Everyone is switching to SKIMS bras. You're next").
No testimonial walls, no clutter; social proof is embedded in the copy itself.

Common pattern: state the offer immediately, show purchasable product with
prices early, one job and one CTA per section, and keep reviews close to the
product rather than as homepage decoration.

## 3. The data points the design leans on

- Baymard: a homepage must communicate what the store sells above the fold, and
  a hero that pushes category access below the fold is "a navigation failure
  dressed up as a marketing win"; CTAs need action-oriented language and 44px
  targets; low trust drives about 17% of abandonment; research-backed fixes are
  worth about 35% conversion improvement on the average store
  ([Baymard via convertcart](https://www.convertcart.com/blog/above-the-fold-content),
  [ai-cmo summary](https://ai-cmo.net/tools/baymard)).
- Bundling: bundles lift AOV 20 to 30%, bundle buyers show about 2.7x lifetime
  value, and 73% of bundles fail when they are arbitrary rather than job-based
  ([Swell](https://www.swell.is/content/physical-product-bundling-statistics),
  [Envive](https://www.envive.ai/post/average-order-value-aov-boost-statistics)).
  Ours are job-based with real savings, which is the failure mode avoided.
- Video: a short silent hero video lifts add-to-cart 12 to 18% and product
  video lifts conversion broadly
  ([Rewarx](https://www.rewarx.com/blogs/should-my-homepage-hero-section-be-an-image-or-video),
  [Levitate](https://levitatemedia.com/learn/video-conversion-statistics)) —
  so the looping dog video STAYS.
- Category tiles: three or four clickable tiles help visitors self-select
  ([FoxEcom](https://foxecom.com/blogs/all/homepage-design),
  [Scrippt](https://www.scrippt.dev/blog/ecommerce-homepage-design-best-practices-that-convert)).

## 4. What shipped, section by section

| # | Section | Change | Why |
|---|---|---|---|
| 1 | Hero (video kept) | H1 "The whole routine, in one box."; sub names all six jobs; primary CTA **Shop the kits** to the bundles collection, secondary outline "Browse everything" | Offer clarity above the fold; specific CTA; the old "Shop the range" sent traffic to /collections/all, the weakest economics on the site |
| 2 | Marquee | Six facts, all now true: shipping, returns, SIX kits, "Kits save up to $26.95 vs separates", 3-toys offer, tracking | Trust bar; the savings figure is computed from live compare_at at apply time |
| 3 | **Kit grid, now first content** | "Start with a kit", all six kits, 3x2, each card showing sale price AND struck-through compare_at | Gymshark pattern: purchasable product with price anchoring before anything else. The savings range $11.95 to $26.95 is stated and real |
| 4 | Trust row | Kept, directly under the grid; "grey"→"gray" | Baymard's 17% trust abandonment, answered before secondary browsing |
| 5 | Flagship band | Repurposed the old duplicate kit band into a Calm & Comfort spotlight: "Storm season, handled.", the five components, "$109.00 together, $26.95 less than apart", CTA to the product page, new Runway lifestyle banner built from the kit's actual component photos | 80/20 merchandising: highest-contribution kit ($43.06) and the phase 1 paid landing page gets the feature slot |
| 6 | Categories | "Prefer to build your own?" + the four tiles | Self-selection for singles shoppers, demoted below kits |
| 7 | Favorites | Kept but demoted; sub-copy now cross-sells: "All of them live inside a kit too." | Singles support the 3-toys offer and SEO; they no longer lead |
| 8 | Story, FAQ, newsletter | FAQ savings answer now states the real range; newsletter "ageing"→"senior dogs" | Objection handling with numbers instead of "yes" |

## 5. What was deliberately NOT done

- **No invented social proof.** We have one real order. No fake review walls,
  no fabricated "as seen in". The Skims lesson is copy that carries conviction,
  not manufactured testimonials. When Judge.me lands and real reviews exist,
  star ratings on the kit cards are the next addition (Gymshark pattern).
- **No WELCOME10 on the page.** The welcome email automation (#76a) is not
  built yet, so "sign up for 10% off" would promise an email nobody sends; and
  printing the code itself on the homepage would convert a first-order
  incentive into a permanent site-wide price cut (the plan's incrementality
  warning). Wire the incentive copy into the newsletter block when flow 2 goes
  live.
- **No urgency theatre.** No countdowns, no fake stock warnings.

## 6. Guardrails built into the script

- Every dollar figure in the copy is computed from the LIVE storefront at apply
  time; the script refuses to write if any kit's compare_at is not above its
  price (so a repricing cannot silently strand a false claim).
- The standing copy rules (no em/en dashes, no hyphenated day ranges, no
  British spellings) are enforced before the PUT.
- The flagship band refuses to point at the banner until the image is READY in
  Files.
- Re-running is idempotent; re-run after any kit repricing to refresh the
  numbers.

## 7. How we will know it worked

No GA4 yet (task #75), so today the only measure is the phase 0 gate. Once the
measurement stack lands, watch: homepage click-through to /collections/
bundles-kits vs the old /collections/all path, kit share of orders, AOV, and
homepage bounce. The bundling benchmarks above (AOV +20 to 30%) are the
reference band for whether kits-first is doing its job.
