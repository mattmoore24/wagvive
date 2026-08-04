# Skims / Gymshark design audit — basis for the 2026-08 Wagvive refresh

Measured from live DOM, 2026-08-01, desktop 1265px viewport.

## Skims (skims.com)

**Homepage structure** (top to bottom):
1. Announcement bar (rewards hook), then slim header — 48px tall
2. Full-bleed hero band, 1265x552 (~2.3:1), image or video, headline + one CTA -> collection
3. Category tile row: 4 portrait tiles, 302x382 (~4:5), label only
4. Full-bleed VIDEO band ("Best Sellers"), 1265x593, autoplay muted loop playsinline,
   heading + one sentence + "Shop Now"
5. Second 4-tile category row
6. Full-bleed image band (Mens)
7. Brand statement: a single mission sentence, text only, generous whitespace

**Type**: display = Tstar Pro Headline 36px w400, letterspacing 0.9px; body/UI = Inter 16px;
buttons tiny (12px). No uppercase shouting — restraint is the look.
**Palette**: near-black `#2D2A26` on white/neutral. Color comes from photography only.
**Copy voice**: heading + max one sentence + one CTA per band. Nothing longer anywhere.

## Gymshark (gymshark.com)

**Homepage structure**:
1. Full-bleed video hero, 1265x474, muted loop; UPPERCASE headline + one CTA
2. Product carousel — 20 cards + View All
3. Full-bleed image band (NEW IN) + CTA
4. Second product carousel (20 cards)
5. "FAVORITES" category tile row
6. "POPULAR RIGHT NOW" collection tiles
7. More tiles ("WAIT THERE'S MORE...")
8. SEO text block at the very bottom

**Type**: headings Montserrat 700 UPPERCASE 24-25px; body Roboto 16.
**Pattern**: louder and denser than Skims; motion up top, then relentless product carousels.

## Shared spine (what we mirror)

- Motion at the top: full-bleed autoplay muted looping video hero, ~2.3:1, headline + ONE cta
- Alternation: full-bleed emotional band -> functional row (tiles or carousel) -> repeat
- Portrait 4:5 category tiles, 4-across, photo-led, label-only
- One thought per band; copy never exceeds heading + sentence + CTA
- Slim header, mega-menu on hover, announcement bar on top
- Product carousels 8+ items deep (vs our current 2-product featured collection)
- Brand statement band near the footer: one sentence, no image

## Wagvive translation

- Keep cream `#F5F1E8` + green `#2F7A4D`: Skims proves neutral-plus-photography wins;
  our color IS the warmth, dogs ARE the photography
- Skims softness for tone (premium pet care), Gymshark density for the product row
- Homepage: video hero (puppies, loopable) -> 4 category tiles (Toys / Grooming /
  Comfort / Kits, real dog photos) -> featured carousel (8-12 bestsellers) -> kit value
  band (full-bleed, one kit hero shot or clip) -> toy-deal band (3-for-15% mechanic) ->
  brand statement sentence -> newsletter
- Type target: letterspaced display for headings (Skims restraint, not Gymshark shout),
  humanist sans body from Shopify's font library
