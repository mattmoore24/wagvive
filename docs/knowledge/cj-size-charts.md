# Where CJ keeps its size charts, and the 2x error that came from guessing

**Learned 2026-08-18.** Applies to every product with a Size option.

## The chart is not where you would look for it

CJ exposes no size data through the API at all. Specifically:

* `/product/query` has **no size, spec or attribute field**. The full key list
  is product/packing/material names, images, weight, price and `variants`.
* `variant.variantLength / variantWidth / variantHeight` are the **postage
  carton**, not the garment. The Pumpkin Hoodie reports `300x200x30mm` for XS
  and for 9XL alike, so anything derived from them is fiction.
* `productImageSet` does **not** contain the chart. For the Pumpkin Hoodie all
  seven entries are colourway product shots.
* `variantKey` sometimes carries a dimension for non apparel, and when it does
  it is reliable: `Coffee color-M 60x50cm`, `Black-S 71cm*100cm`. This is the
  cheapest source for pads, blankets and covers, and it agreed exactly with our
  storefront option labels.

The apparel charts live **inside the `description` HTML, as `<img>` tags**.

```python
urls = re.findall(r'<img[^>]+src="([^"]+)"', product['description'])
```

Every earlier script in this repo ran the description through
`re.sub(r'<[^>]+>', ' ', ...)` before looking at it, which threw the `<img>`
tags away and left the visible text reading `Size:` followed by nothing. That
is why size data looked absent for months. The description also carries **more
images than `productImageSet`** (the robe: 16 vs 27, different sets), so it is
worth pulling both.

Finding the chart among them: charts are flat graphics, so they have far fewer
unique colours than a photograph and are rarely square. Ranking by
`len(set(im.resize((160,160)).getdata()))` puts the chart first almost every
time. Some CJ text descriptions also carry the dimensions in prose under
`Specifications:` (`XXS:20 * 20CM,XS:40*60CM,S:52*76CM,...`), which is the
easiest source of all when it exists.

## The error this caused

The Quick-Dry Bath Robe shipped a size table saying **XS fits 9 to 16 lb**,
naming the Chihuahua and the Pomeranian. The manufacturer's chart says XS is
**8 to 15 kilograms**, which is 18 to 33 lb. The maker's weight column is
unlabelled, someone read it as pounds and then converted it *again*, so every
row landed at roughly half the true weight and the breed examples were written
to match the wrong number.

**The chest column is what settles it, and it is why a weight-only table is
dangerous.** XS is graded for a 45 to 55 cm chest and M for 70 to 80 cm. A
Chihuahua measures about 35 cm. A 70 to 80 cm chest is a Labrador, not the
Border Collie the M row used to name. A weight figure cannot be checked against
anything; a girth can be checked against the garment. `audit_size_guides.py`
therefore **rejects any guide whose only number is a weight range**.

When a chart's units are unlabelled, resolve them against the girth, not
against what looks plausible.

## Charts that disagree with themselves

* **Skeleton Suit (CJGD2143164).** The chart says in bold *the fabric is not
  stretchable*; CJ's own marketing bullet for the same SPU says *STRETCHY AND
  BREATHABLE*. A fit claim is where guessing wrong costs a return, so the copy
  drops the stretch promise and leans on "size up if between", which is what
  the chart says.
* **Jack-o-Lantern Sweater (CJGD1809813).** The chart is labelled **S to 2XL**
  while CJ sells the product as **XS to XL**. Five graded garments either way,
  in the same order, and we order by `variantSku`, so grade 1 is grade 1
  whatever letter is printed. The measurements are mapped **by position** and
  the copy tells the shopper to choose by the numbers rather than the letter.
  Do not "fix" the letters to match the chart.
* **Turkey Sweater (CJGD1841040).** Chest only, no back length published. We
  quote chest and say plainly that there is no published back length, rather
  than inventing one.

## Products with no dog measurement at all

The blankets, pads and covers publish dimensions only. Our fitting rules,
labelled in the copy as ours rather than as the maker's:

* a **pad** is matched on its **long** edge, because a dog lying stretched out
  takes roughly its back length
* a **blanket** is matched on its **short** edge, because it has to cover a dog
  that is curled

Two products have no honest dog measurement and are exempt in the audit rather
than fudged: the **Sofa & Furniture Cover** is sized to the furniture, and the
**Paw Washing Cup** is sized to the paw. The cup is worth a note: all three
sizes share the same **7 cm opening** and differ only in height, so the size
choice is leg length, and a paw wider than 7 cm fits none of them.

## Supplier quality signal, noticed in passing

`CJGY1926497` (Waterproof Snuggle Blanket) is listed by a general merchandise
seller whose description images are mostly adult body pillows, and whose
`Black set-L` variants bundle them. We sell only the plain blanket variants
(Black XS and S) so nothing improper reaches the storefront, and the imagery is
all house art now. Worth remembering if that SPU is ever re-imaged from source.

## Scripts

* `config/apply_size_guides.py` holds every transcribed chart and writes the
  tables. Source values are cm and kg; inches and pounds are computed, never
  transcribed.
* `config/audit_size_guides.py` is the gate. Run it after any product or option
  change.
