# Theme copy fixes, product page (owner action)

Found 2026-08-04 while checking the wipes product. All four items live in
`templates/product.json` in the Horizon theme, and every one of them appears on
**every product page**, not just the wipes.

**Claude cannot apply these.** Writes to the live theme are refused by policy:
"This mutation targets the live (published) theme." The options are to edit in
the theme editor (fastest, these are all text blocks) or to duplicate the theme,
edit the draft and publish. I scanned every other theme file that carries
Wagvive copy (`index.json`, `page.json`, `collection.json`, `settings_data.json`,
`kit-callout`, `toy-deal`, `kit-contents`) and they are all clean, so this file
is the only one that needs touching.

Where to find them: Theme editor, Products template, in the right hand column
under the Add to cart button. Item 1 is a trust badge, items 2 to 4 are rows of
the accordion.

## 1. Trust badge, stopwatch icon

Contains an en dash, which the house style forbids for ranges.

Replace:

    Ships in 1–3 business days

With:

    Ships in 1 to 3 business days

## 2. Accordion row, "Shipping & delivery"

Two en dashes.

Replace:

    Dispatched in 1–3 business days. Typical US delivery is 5–12 business days after dispatch, with tracking emailed as soon as it ships. Free over $60, otherwise $5.95 flat.

With:

    Dispatched in 1 to 3 business days. Typical US delivery is 5 to 12 business days after dispatch, with tracking emailed as soon as it ships. Free over $60, otherwise $5.95 flat.

## 3. Accordion row, "Returns"

One em dash.

Replace:

    30 days from delivery. Faulty, damaged, or incorrect items: we cover return shipping and replace or refund, your choice. Changed your mind is fine too — return postage is on you in that case.

With:

    30 days from delivery. Faulty, damaged, or incorrect items: we cover return shipping and replace or refund, your choice. Changed your mind is fine too. In that case return postage is on you.

## 4. Accordion row, "Care & use"

Three problems in one block. It carries an em dash; it tells customers to
"rinse or wipe clean after use and let it dry fully before storing", which is
wrong for the disposable wipes and for the plush toys; and it still refers to
"older or anxious dogs", which is the senior positioning we dropped.

Because this block is global, the replacement has to be true for every product
in the catalogue, so it points at the product description for specifics and
only states rules that hold everywhere.

Replace:

    Rinse or wipe clean after use and let it dry fully before storing. Introduce new grooming tools gradually — a few short, calm sessions beat one long one, especially with older or anxious dogs.

With:

    Care depends on the product, so check the description above for the specifics. As a rule: wipes and other disposables are single use, so throw each one away after use. Wash fabric items cool and skip the tumble dryer on anything with a waterproof backing. Wipe grooming tools clean and let them dry fully before storing. Introduce any new grooming tool gradually, with a few short calm sessions rather than one long one.

## Note on the wipes

CJ lists this product as "Disposable Pet Cleaning Products", material
non-woven fabric, packed as "Wet wipes * 1 box/50pcs". They are single use wet
wipes, so the old care text was wrong. The product description was rewritten on
2026-08-04 and already says so in three places.
