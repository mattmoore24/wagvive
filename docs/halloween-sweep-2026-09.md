# Second Halloween sweep, 2026-09-14

**Status: recommendations only. Nothing has been created, paired or bought.**
The owner decides which to add.

## Timing

Halloween is Saturday 31 October. Under the 10 to 16 business day promise the
safe last order date is **Wednesday 7 October** (16 business days back from
Friday 30 October, skipping Columbus Day). Orders up to about 16 October arrive
only at the fast end. Anything added now sells as a Halloween item for about
three weeks, so each addition has to be worth its art, size guide and pairing.

## Method

1. **Sweep** (`config/scout_halloween.py`). CJ's `/product/listV2`, 46 keyword
   searches and 22 pet categories, 3 pages of 100 per keyword, sorted by
   `listedNum` (the number of other stores listing the product). 4,971 unique
   products; about 8,950 CJ points.
2. **Filter.** Halloween by name, for a dog, not human wear or house decor, not
   Christmas only, not an SPU the catalogue already uses (any status): 421
   candidates.
3. **Cost** (`config/cost_halloween.py`) the top 62: every variant's CJ cost and
   weight, a live freight quote on the dearest and heaviest variant, the 20%
   break-even price per variant. One rejected on weight (a 1.6 kg cat bed).
4. **Vet** 61 with one agent each: CJ photos and size charts opened by eye, a
   US market price check, which variants to keep, margin on each.
5. **Verify** every "recommend" or "maybe" with two independent refuters, one
   on product truth (photos, sizing, quality) and one on economics (own market
   search, margin recomputed).
6. **Rank**, merging listings where several CJ suppliers sell the same design.
7. **Live quotes** for every variant of the six finalists (below).

Result: 12 survived both checks, 11 contested, 5 killed by a refuter, 33
rejected at vetting.

## Shortlist (every kept variant clears 20% on a LIVE carrier quote)

| # | Product | SPU | Price | Worst / best margin | Sizes | Carrier |
|---|---|---|---|---|---|---|
| 1 | Deadly Doll Dog Costume | CJJJCWGD00380 | $21.99 | 29.4% / 33.0% | S to XL, chest 37 to 69 cm | LuWei Ordinary US |
| 2 | Hot Dog Costume | CJJJCWGD00035 | $19.99 / $21.99 / $25.99 by size | 22.1% / 27.4% | chest 40 to 102 cm (Bichon to Lab) | LuWei Ordinary US, CJPacket Super Pure Electricity |
| 3 | Dog Bat Wings | CJGD2134159 | $9.99 | 30.3% / 36.3% | S to L, chest 35 to 65 cm | CJPacket Super Pure Electricity |
| 4 | Halloween Dog Collar | CJJJCWGY02793 | $12.99 | 31.2% / 40.4% | S to XL, strap 40 to 70 cm | CJPacket Super Pure Electricity, LuWei Ordinary US |
| 5 | Reversible Halloween Bandana | CJGD1226829 | $10.99 | 32.5% / 35.8% | S, M | CJPacket Super Pure Electricity |
| 6 | Skull Tutu Dress | CJGD1809711 | $12.99 | 35.8% / 39.8% | S to XL, chest 38 to 55 cm | CJPacket Super Pure Electricity |

All carriers quote 5 to 11 days. **The carrier chosen at CJ pairing must be the
one each variant was priced on** (CLAUDE.md, money model).

### Variants to keep

1. **Deadly Doll:** "Photo Color" S, M, L, XL only. Drop "Horseman" (cat only,
   one photo is another brand's advert), "No hat" (never photographed),
   "Photo Colorset" M and XL (477 to 650 g, need $39.15 to $45.80). Confirm on
   CJ's variant image that "Photo Color" is the doll look.
2. **Hot Dog:** CJ sizes 8 and 10 at $19.99, 12, 14 and 16 at $21.99, 18 at
   $25.99 (its cost jumps to $9.56, so a flat $21.99 would be about 8.5%).
   Drop Size6, which is not on the chart. Size 10 at $19.99 is the thinnest
   kept variant at 22.5%.
3. **Bat Wings:** "Black Wings" S, M, L. Drop the three "Red brown bell"
   variants, which at 30 g in every size are the bell alone.
4. **Collar:** Halloween (black), Bat, Ghost and Cat monster prints in S to XL.
   Drop "Pumpkin hat" and "Yellow" (names do not say which print they are) and
   "Spider" (the most cartoonish). Confirm print names against CJ's images.
5. **Bandana:** Witch or pumpkin, Spider web pumpkin, Bat or spider web, S and
   M. Drop "Spider or ghost" (a cartoon cat resembling a known character).
6. **Skull Dress:** Skull S to XL. The "Colorful" variants are a different print.

### Why these, and the risks carried in

* **Deadly Doll** has by far the strongest demand signal in the sweep (10,559
  other stores list it) and reads as Halloween instantly on a real dog. It
  covers the small and medium dogs the Big Dog Costume does not. **It copies a
  licensed horror character**: title and copy must say Deadly Doll and never
  name the character. No large-dog size; map CJ's letters onto the store's
  chest-based scale, never CJ's letters.
* **Hot Dog** is the only candidate with real large-dog sizes, on genuine
  Golden Retriever photos, which is what recent orders bought (large Big Dog
  Costumes). It is a price stretch against big-box hot dog costumes ($17 to
  $19.99) and relies on buyers paying Big Dog Costume prices. No photo shows
  the belly strap.
* **Bat Wings** fills the impulse accessory gap at $9.99, under Target's $12.
  Thin felt with raw edges (standard for the category). Weak references: most
  photos are cats and carry burnt-in sales text, so the house shot must be
  built from the flat lay and checked closely. Do not promise the bell in copy
  until CJ confirms it ships with Black Wings.
* **Collar** is the only Halloween add-on that fits big dogs, under PetSmart's
  $14.99. No dog appears in any photo and there is no neck chart, only strap
  lengths, so the size guide must be derived.
* **Bandana** is the classic cheap add-on and the lineup has none. Genuine
  photos of a real Samoyed. No size chart and CJ's side lengths contradict
  themselves; write fit from the long edge (S about 13 to 14 in neck, M about
  19 to 20 in). Works as an add-on, not a standalone.
* **Skull Dress** is the cleanest money (35.8% worst) but small dogs only and
  shares the skull theme with the Glow Skeleton Suit. First cut if the list
  must shrink.

## Merged (same design, several CJ suppliers)

* CJGY1338841 front-walking killer doll into the Deadly Doll (smaller sizes,
  seven looks, 587 listings against 10,559).
* CJGD1305697 small plush hot dog into the padded Hot Dog (its dog photos are
  another brand's costume; stops at a 20.5 in chest).
* Bandanas CJJJCWGY02683, CJJJCWGD00661, CJGY1546391 into CJGD1226829 (theirs
  have pasted-in or wrong-item dog photos).
* Dresses CJGD1809790, CJGD1809650 into the Skull Dress (same factory template,
  shown only on a plush dog or a dress form).

## Notable rejections

* **Pumpkin vest set CJYD1861730 came back again.** It is August's cat hood:
  set minus vest is exactly 158 g and $1.10 at every size, so every set ships
  the same one-size "Cat Hat".
* **Four listings show a DIFFERENT product on their dog photos:** plush pumpkin
  hood CJGD1239295, spider legs CJHD1244332, satin vampire cape CJYD2090717,
  small hot dog CJGD1305697. The August lesson, repeated: titles and hero shots
  lie, and only opening every photo catches it.
* Cowboy and reaper rider CJJT1311139: the "dog" is a plush display dog.
* Headless horseman rider CJGD1825417: no size chart, needs $15.16 against a
  $12 market.
* Novelty wig CJGY1583543, jester hoodie CJJJCWGD00578, pumpkin hide and seek
  plush CJJT1582711: the market will not pay the 20% price.
* Bloody prop vest CJGY1292971: thin raw felt, every dog photo a composite.
* Spider web cape CJGD1266208: good photos, runner-up to the bat wings if their
  reshoot fails.

## Better later (fall, winter or Christmas)

Cow fleece onesie CJJJCWGD00036 (33.1% at $13.99, live quote), front-walking
Santa delivery costume (Red look of CJGY1338841), sherpa collar winter vest
CJJJCWGD00166, padded harness puffer vest CJJJCWGY02108.

## Before listing any of these

1. Confirm variant name to look or print on CJ's own variant images.
2. Duplicate check on `sku[:11]` against the catalogue (all six are new today).
3. Size guide from the chart, mapped onto `config/size_scale.py` by chest.
4. House art on cream #F7F2E9 from the genuine dog photos, eyeballed against
   the CJ reference.
5. Pair in CJ on the carrier each variant was priced on, then run the standing
   audits.

## Lessons for the next sweep

* `/product/listV2` is the sourcing endpoint. `/product/list` has no working
  keyword search or sort, which is why this repo once believed CJ's API could
  not source.
* REST `products.json?status=any` returns zero products. Omit `status`.
* A theme regex must not match words that are only sometimes Halloween
  ("luminous", "shark", "dinosaur", "hot dog"), and the candidate test must
  require a dog or pet signal. The first pass kept night lights, slippers and
  handbags and began costing them.
* Price the variant set, not the product: the Deadly Doll's own CJ listing
  needs $12.15 or $45.80 for 20% depending on which variants are kept.
