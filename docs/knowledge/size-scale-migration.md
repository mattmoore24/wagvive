# One size scale for the whole store, and the two traps in getting there

**2026-08-19.** Owner brief: standardise every sized product onto XS to XL, so
a given dog picks the same letter everywhere, with weight and breed examples
because "nobody knows their dog's measurements".

`config/size_scale.py` is the source of truth. `config/apply_size_scale.py`
migrates the catalogue onto it. `config/apply_size_guides.py` renders the
customer-facing guides from it.

## The problem, in one line

A beagle owner needed the robe in **XS**, the hoodie in **4XL** and the costume
in **3XL** - three different letters for one dog - because each product wore
whatever its CJ supplier happened to print. After: **M, M, M**.

## How the mapping was decided

Matched on **chest girth**, because girth is what decides whether a garment
does up. Displayed as **weight then breeds then measurements**, because that is
the order a customer can actually answer. Supplier sizes were placed into the
canonical girth bands; where several landed in one band, the one nearest the
band midpoint was kept and the rest retired, so "S" is one obvious choice
rather than three near-identical ones. 153 variants became 88.

Products that genuinely cannot serve the whole range offer a SUBSET rather than
pretending: the Skeleton Suit is a small-dog suit and sells XS and S only; the
Big Dog Costume sells M, L and XL. The letters still mean the same dog.

The Sofa & Furniture Cover was deliberately taken OFF the dog scale entirely
and given furniture names (Armchair or car seat / Two seat sofa / Three seat
sofa). Dog letters on a furniture-sized product is exactly the confusion this
work removed.

## TRAP 1: a one-pass rename deadlocks on any mapping that SHIFTS

The Quick-Dry Bath Robe maps XS to S, S to M, M to L. Renaming XS to S while a
real S still exists returns:

```
422 {"errors":{"base":["The variant 'Blue / S' already exists. ..."]}}
```

and the run dies half finished - which it did, leaving five products migrated
and five not. Sizes that merely get NEW names (the cooling pad's dimensional
labels) are fine; anything that shifts along its own scale is not.

**Fix, now in `apply_size_scale.rename()`:** two passes through a temporary
name. Set every changing variant to `__TMP_<new>`, then to `<new>`. Nothing can
collide with a temp name, so the operation is order-independent, and passes are
per product so a product never ends a failed run holding temp names.

## TRAP 2: deleting a component variant SILENTLY DRAFTS every kit using it

Retiring the Cooling Comfort Pad's XX-Large set Shopify to knock all four sized
kits (Calm & Comfort, Grooming Essentials, New Puppy, Travel) from `active` to
`draft`. No error, no warning - they simply left the storefront. The catalogue
went 52 active products to 48 and the four kits stopped being findable by
handle with `status=active`, which is how it was noticed.

Critically, **the bundle composition survived intact**: components are
referenced by variant ID, so the renames propagated correctly (the robe inside
the kit correctly read `Green / S` afterwards) and every kit still had its five
components. Only `status` changed. The XX-Large pad was NOT itself a kit
component - deleting a sibling variant on a component PRODUCT was enough.

**What to do:** after deleting any variant on a product that is a kit
component, re-check every kit's `status`, set it back to `active`, AND
re-publish it to the sales channels - per CLAUDE.md, active alone does not put
a product back on the Online Store. `apply_size_scale.py` does not yet automate
this; verify it manually or the kits stay invisible.

## What did NOT break, verified

* **CJ pairing.** Keyed on variant SKU, and a rename never touches the SKU, so
  survivors kept their pairing. `audit_cj_connections.py` after the migration:
  every SKU resolves, 46/46 products buyable, all six kits intact.
* **variant.image_id.** Zero variants lost their art across all 15 products.
* **Kit bundle contents.** Confirmed by `productVariantComponents` before and
  after.

## Follow-up left open

`config/price_book.json` had to be pruned of the 65 retired SKUs (plus a dead
Dental & Ear Wipes entry) so `apply_price_book.py` could not write prices to
variants that no longer exist. Any future variant retirement needs the same
prune - the book does not self-clean.
