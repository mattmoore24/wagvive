#!/usr/bin/env python3
"""Put a real, per-size measurement table on every product that asks for a size.

WHY. Fifteen active products make the shopper pick a size. Six carried a table
already and nine carried nothing at all, including every single costume and
jumper, which are exactly the products where getting it wrong means a return.
The Skeleton Suit came closest with "cut for small dogs", which is a vibe, not a
measurement: an owner with a 14 inch dachshund and an owner with a 14 pound pug
both read that as "yes".

AND ONE OF THE SIX WAS WRONG. The Quick-Dry Bath Robe told customers XS fits a
9 to 16 lb dog and named the Chihuahua and the Pomeranian. The manufacturer's
chart says XS is for 8 to 15 KILOGRAMS, which is 18 to 33 lb. Someone read the
maker's unlabelled weight column as pounds and converted it a second time, so
every row was out by roughly 2x and the breed examples followed the bad number
down. The chest column settles it: XS is graded for a 45 to 55 cm chest and M
for 70 to 80 cm. A Chihuahua measures about 35 cm and a 70 to 80 cm chest is a
Labrador, not the Border Collie the M row used to name. Anyone who bought by
that table got a robe two sizes too big.

WHERE THE NUMBERS COME FROM. CJ does not expose size data anywhere in the API.
`/product/query` has no size field, and `variantLength/Width/Height` are the
POSTAGE CARTON, not the garment: the Pumpkin Hoodie reports 300x200x30mm for XS
and for 9XL alike. The charts are images, and they are not in `productImageSet`
either. They are embedded as <img> tags inside the `description` HTML, which
every earlier script stripped to plain text before looking at it. That is why
this looked like missing data for so long, and it is very likely how the robe
came to be filled in from guesswork.

Centimetres and kilograms are the transcribed source values. Inches and pounds
are COMPUTED here, because hand-converting thirteen rows is how a decimal point
goes missing. Spot-checked against the inches the Skeleton Suit chart prints
itself: 27cm/10.6in, 34cm/13.4in, 42cm/16.5in all agree.

THREE HONEST CAVEATS, all visible in the copy rather than smoothed over:

  1. The Jack-o-Lantern Sweater's chart is labelled S to 2XL while CJ sells it
     as XS to XL. Five graded sizes either way, in the same order, and we order
     by variantSku so grade 1 is grade 1 whatever letter is printed on the
     chart. The measurements map by POSITION, which is what the copy says. Do
     not "correct" the letters to match the chart.

  2. The Skeleton Suit's chart states in bold that the fabric is NOT
     stretchable. CJ's own marketing bullet for the same product says "STRETCHY
     AND BREATHABLE". They cannot both be true, and a fit claim is the one place
     where guessing wrong costs a return, so the bullet no longer promises
     stretch and the copy leans on "size up if between", which is what the chart
     says.

  3. The Sofa & Furniture Cover is sized to the FURNITURE. No dog measurement
     picks it, and inventing one would be worse than saying so.

For the blankets and pads the manufacturer publishes dimensions only. The dog
guidance there is our own fitting rule, labelled as ours: a dog lying stretched
takes roughly its back length, so a pad is matched on its LONG edge, while a
blanket has to cover a curled dog and is matched on its SHORT edge.

    python config/apply_size_guides.py             # show the plan
    python config/apply_size_guides.py --apply
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')

MARK = 'wagvive-size-guide'      # our wrapper, so a re-run replaces cleanly
HEAD = 'Choosing a size'         # the heading the six existing guides use

# Lifted verbatim from the guides already on the store so the new tables are
# visually identical to the ones that were there before.
STYLE = ('<style>.wv-size{width:100%;border-collapse:collapse;margin:0 0 1em;'
         'font-size:.95em}.wv-size th,.wv-size td{border:1px solid #DCD2C1;'
         'padding:.5em .6em;text-align:left;vertical-align:top}'
         '.wv-size th{background:#F7F2E9;font-weight:600}</style>')


# ---------------------------------------------------------------- conversions
def inch(cm):
    v = cm / 2.54
    return f'{v:.0f}' if abs(v - round(v)) < 0.05 else f'{v:.1f}'


def lb(kg):
    v = kg * 2.2046
    return f'{v:.0f}' if v >= 10 else f'{v:.1f}'


def L(cm):
    """A single length, inches first: this is a US storefront."""
    return f'{inch(cm)} in ({cm:g} cm)'


def LR(a, b):
    return f'{inch(a)} to {inch(b)} in ({a:g} to {b:g} cm)'


def WR(a, b):
    return f'{lb(a)} to {lb(b)} lb ({a:g} to {b:g} kg)'


def DIM(w, h):
    return f'{inch(w)} x {inch(h)} in ({w:g} x {h:g} cm)'


# --------------------------------------------------------------------- charts
# Every row is transcribed from the manufacturer's own chart image, found by
# pulling the <img> tags out of the CJ `description` HTML.

HOODIE = [  # size, dog weight kg lo/hi, chest cm, back length cm
    ('XS', 0.6, 1.2, 27, 16), ('S', 1.2, 2.0, 32, 20), ('M', 2.0, 3.0, 37, 25),
    ('L', 3.0, 4.3, 42, 30), ('XL', 4.3, 6.0, 47, 35), ('2XL', 6.0, 8.0, 52, 38),
    ('3XL', 8.0, 10, 59, 40), ('4XL', 10, 14, 64, 50), ('5XL', 14, 18, 69, 55),
    ('6XL', 18, 22.5, 74, 60), ('7XL', 22.5, 27.5, 79, 65),
    ('8XL', 27.5, 31.5, 83, 70), ('9XL', 31.5, 36, 87, 75),
]
BIGDOG = [('3XL', 68, 48), ('4XL', 73, 53), ('5XL', 78, 58),
          ('6XL', 83, 63), ('7XL', 88, 66), ('8XL', 93, 66)]
ROBE = [  # size, chest lo/hi, back, neck lo/hi, weight kg lo/hi
    ('XS', 45, 55, 33, 35, 40, 8, 15),
    ('S', 57, 67, 40, 45, 50, 15, 25),
    ('M', 70, 80, 50, 53, 58, 25, 50),
]
ROBE_BREEDS = {
    'XS': 'Shih Tzu, Miniature Schnauzer, West Highland Terrier',
    'S': 'Border Collie, Cocker Spaniel, Staffordshire Bull Terrier',
    'M': 'Labrador, Golden Retriever, German Shepherd, Boxer',
}
SKELETON = [('S', 27, 34, 22), ('M', 29, 38, 25),
            ('L', 35, 42, 28), ('XL', 40, 46, 32)]
JACK = [('XS', 19, 30), ('S', 20, 35), ('M', 23, 40),
        ('L', 25, 48), ('XL', 30, 56)]        # by grade order, see caveat 1
TURKEY = [('S', 36), ('M', 38), ('L', 44), ('XL', 46)]
PAWCUP = [('S', 11), ('M', 13.5), ('L', 15)]  # height; opening is 7cm on all
FLEECE = [('S', 52, 76), ('M', 76, 104)]
SNUGGLE = [('XS', 50, 70), ('S', 71, 100)]
COOLPAD = [('Medium 24" x 20"', 60, 50), ('Large 28" x 22"', 70, 55),
           ('X-Large 39" x 28"', 100, 70), ('XX-Large 59" x 39"', 150, 100)]
SOFA = [('Small 20" x 28"', 50, 70), ('Medium 28" x 39"', 71, 100),
        ('Large 39" x 57"', 100, 145)]

HOW_TO = ('Chest is the widest part of the ribcage, just behind the front legs. '
          'Back length runs from the base of the neck to the base of the tail. '
          'Keep the tape flat rather than tight.')
SIZE_UP = 'If your dog falls between two sizes, choose the larger one.'


def table(cols, rows):
    th = ''.join(f'<th>{c}</th>' for c in cols)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
                   for r in rows)
    return (f'{STYLE}<table class="wv-size"><thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


def block(intro, cols, rows, notes):
    n = ''.join(f'<p>{x}</p>' for x in notes)
    return (f'<div class="{MARK}"><h3>{HEAD}</h3><p>{intro}</p>'
            f'{table(cols, rows)}{n}</div>')


# ----------------------------------------------------------------- per product
def guides():
    g = {}

    g['wagvive-pumpkin-hoodie'] = block(
        'The maker grades this one by weight as well as by chest and back, so '
        'it is the easiest of our costumes to get right. ' + HOW_TO,
        ['Size', 'Dog weight', 'Chest girth', 'Back length'],
        [(s, WR(a, b), L(c), L(d)) for s, a, b, c, d in HOODIE],
        [SIZE_UP,
         'Thirteen sizes runs from a puppy of a pound or two up to a 79 lb '
         'labrador, so nearly every dog has a size here.'])

    g['wagvive-big-dog-costume'] = block(
        'These are the measurements of the costume itself, not of your dog. '
        'Measure your dog, then pick the size that clears both figures so the '
        'fleece is not pulled tight. ' + HOW_TO,
        ['Size', 'Costume chest', 'Costume back length'],
        [(s, L(b), L(l)) for s, b, l in BIGDOG],
        ['Built for big dogs only. The smallest size here takes a chest of '
         'about 27 in, so for anything under that see the Pumpkin Hoodie, '
         'which starts at XS.',
         '7XL and 8XL share a back length and differ in the chest. That is the '
         'maker grading for barrel chested dogs, not a typo.'])

    g['wagvive-quick-dry-bath-robe'] = block(
        'The robe wraps the whole body, so chest girth is what matters most. '
        'Weight is a useful check, not the deciding number. ' + HOW_TO,
        ['Size', 'Chest girth', 'Back length', 'Neck girth', 'Dog weight',
         'Roughly'],
        [(s, LR(c1, c2), L(b), LR(n1, n2), WR(w1, w2), ROBE_BREEDS[s])
         for s, c1, c2, b, n1, n2, w1, w2 in ROBE],
        [SIZE_UP,
         'XS here starts at about 18 lb. This robe is cut for medium and large '
         'dogs, so it is not the right thing for a toy breed.'])

    g['wagvive-glow-skeleton-suit'] = block(
        'A four leg suit, and the maker is clear that the fabric does not '
        'stretch, so measuring matters more here than on a knit jumper. '
        + HOW_TO,
        ['Size', 'Back length', 'Chest girth', 'Neck girth'],
        [(s, L(b), L(c), L(n)) for s, b, c, n in SKELETON],
        [SIZE_UP + ' The maker is emphatic about this one because the fabric '
         'has no give at all.',
         'Cut for small dogs and medium breed puppies. The largest size takes '
         'an 18 in chest, so for a bigger dog see the Pumpkin Hoodie, which '
         'runs to 9XL, or the Big Dog Costume.'])

    g['wagvive-jack-o-lantern-sweater'] = block(
        'A knit jumper, so the neck and the chest are the two to measure. '
        + HOW_TO,
        ['Size', 'Neck girth', 'Chest girth'],
        [(s, L(n), L(b)) for s, n, b in JACK],
        [SIZE_UP,
         'The maker prints its chart one letter larger than the sizes on the '
         'dropdown. There are five graded sizes either way and these are the '
         'measurements of the one you actually receive, so choose by the '
         'numbers rather than by the letter.'])

    g['wagvive-thanksgiving-turkey-coat'] = block(
        'The maker publishes chest only for this jumper. Measure the widest '
        'part of the ribcage, just behind the front legs, and pick the size '
        'that clears it.',
        ['Size', 'Chest girth'],
        [(s, L(b)) for s, b in TURKEY],
        [SIZE_UP,
         'Acrylic knit with some give, so a snug measurement still goes on '
         'comfortably. There is no published back length for this one, which '
         'is why we are not quoting a figure we cannot stand behind.'])

    g['wagvive-paw-washing-cup'] = block(
        'All three sizes share the same 2.8 in (7 cm) opening, so the choice '
        'is about how deep the cup is, not how wide. Measure your dog across '
        'the paw pads: anything wider than 2.8 in will not go into any size.',
        ['Size', 'Cup height', 'Opening', 'Suits'],
        [(s, L(h), L(7),
          {'S': 'Toy and small breeds up to about 15 lb, such as a Chihuahua '
                'or Yorkshire Terrier',
           'M': 'Medium breeds roughly 15 to 45 lb, such as a Beagle or '
                'Cocker Spaniel',
           'L': 'Large breeds 45 lb and up, such as a Labrador or German '
                'Shepherd'}[s]) for s, h in PAWCUP],
        ['A taller cup suits a longer leg, which is the only thing that '
         'changes between the three. A cup too narrow will not turn around '
         'the paw, so measure the width before the height.'])

    g['wagvive-paw-print-fleece-blanket'] = block(
        'A blanket is sized to cover a curled dog, so compare your dog against '
        'the SHORT edge below. Back length runs from the base of the neck to '
        'the base of the tail.',
        ['Size', 'Blanket size', 'Suits a back length up to', 'Best for'],
        [(s, DIM(w, h), L(w), t) for (s, w, h), t in zip(
            FLEECE, ['Crates, carriers and car seats',
                     'Sofa corners and larger beds'])],
        ['The dimensions are the maker figures. The back length column is our '
         'own fitting rule rather than a published number: a dog curls to '
         'roughly its back length, so a blanket whose short edge clears that '
         'will cover it.'])

    g['wagvive-waterproof-snuggle-blanket'] = block(
        'Sized to cover a curled dog, or to protect a patch of sofa or car '
        'seat. Compare your dog against the SHORT edge.',
        ['Size', 'Blanket size', 'Suits a back length up to', 'Covers'],
        [(s, DIM(w, h), L(w), t) for (s, w, h), t in zip(
            SNUGGLE, ['A crate floor or a car seat',
                      'One sofa cushion or an armchair seat'])],
        ['Dimensions are the maker figures. The back length column is our own '
         'fitting rule, not a published number.'])

    g['wagvive-cooling-comfort-pad'] = block(
        'A cooling pad only works where the dog is touching it, so it wants to '
        'be long enough to lie out on. Compare your dog against the LONG edge '
        'below. Back length runs from the base of the neck to the base of the '
        'tail.',
        ['Size', 'Pad size', 'Suits a back length up to', 'Typical dog'],
        [(s, DIM(w, h), L(w), t) for (s, w, h), t in zip(
            COOLPAD, ['Small dogs up to about 25 lb, such as a Pug or '
                      'Miniature Schnauzer',
                      'Medium dogs roughly 25 to 55 lb, such as a Beagle or '
                      'Border Collie',
                      'Large dogs roughly 55 to 90 lb, such as a Labrador or '
                      'Boxer',
                      'Giant breeds over 90 lb, or a dog who likes to '
                      'sprawl'])],
        ['Dimensions are the maker figures. The back length column is our own '
         'fitting rule: a dog lying stretched takes roughly its back length, '
         'so the long edge should clear it.'])

    g['wagvive-waterproof-sofa-furniture-cover'] = block(
        'This one is sized to your FURNITURE, not to your dog. Measure the '
        'seat you want to protect, across the front and from the back cushion '
        'to the front edge, then pick the size that covers it.',
        ['Size', 'Cover size', 'Covers'],
        [(s, DIM(w, h), t) for (s, w, h), t in zip(
            SOFA, ['A car seat, a crate floor, or one armchair seat cushion',
                   'A generous armchair, or a large dog bed',
                   'The seat area of a two seat sofa, or one end of a '
                   'larger sofa'])],
        ['No dog measurement picks this one, so we are not inventing one. '
         'Any size works for any dog. What matters is the furniture '
         'underneath.'])

    return g


# ------------------------------------------------------------------------ kits
# A kit's Size drives several components at once through SIZE_MAP in
# kit_colorways.py, so the guidance has to be derived from the components that
# actually vary. The binding one is whichever is WORN: a blanket slightly small
# is a minor disappointment, a robe that does not do up is a return. Grooming
# and Travel both carry the robe, so the robe's chart governs them. New Puppy
# and Calm & Comfort carry nothing worn, so theirs is about footprint and says
# so rather than implying a fit that is not being promised.
def kit_guides():
    sys.path.insert(0, os.path.join(ROOT, 'config'))
    from kit_colorways import KITS, SIZE_MAP

    robe = {r[0]: r for r in ROBE}
    fleece = {s: (w, h) for s, w, h in FLEECE}
    pad = {s: (w, h) for s, w, h in COOLPAD}
    out = {}

    worn_intro = ('One size choice sets every sized item in the kit at once, '
                  'so pick it from the robe, which is the only thing your dog '
                  'wears. ' + HOW_TO)
    soft_intro = ('Nothing in this kit is worn, so the size choice is about '
                  'how much ground the bedding covers rather than about fit. '
                  'Compare your dog against the figures below. Back length '
                  'runs from the base of the neck to the base of the tail.')

    for handle, kit in (('grooming-essentials-kit', 'Grooming Essentials Kit'),
                        ('travel-kit', 'Travel Kit')):
        rows = []
        for size in KITS[kit]['sizes']:
            rs = SIZE_MAP[size]['Quick-Dry Bath Robe']
            _, c1, c2, b, n1, n2, w1, w2 = robe[rs]
            rows.append((size, LR(c1, c2), L(b), WR(w1, w2),
                         ROBE_BREEDS[rs],
                         f'Robe {rs}, paw cup '
                         f'{SIZE_MAP[size]["Paw Washing Cup"]}'))
        out[handle] = block(
            worn_intro,
            ['Kit size', 'Chest girth', 'Back length', 'Dog weight', 'Roughly',
             'You receive'],
            rows,
            [SIZE_UP,
             'Small starts at about 18 lb because that is where the robe '
             'starts. For a smaller dog every tool in this kit still suits '
             'any size, but the robe will be loose.'])

    rows = []
    for size in KITS['New Puppy Kit']['sizes']:
        w, h = fleece[SIZE_MAP[size]['Paw Print Fleece Blanket']]
        rows.append((size, DIM(w, h), L(w)))
    out['new-puppy-kit'] = block(
        soft_intro + ' The blanket is the only thing that changes.',
        ['Kit size', 'Blanket size', 'Suits a back length up to'], rows,
        ['Everything else in this kit is one size and suits any puppy.'])

    rows = []
    for size in KITS['Calm & Comfort Kit']['sizes']:
        fw, fh = fleece[SIZE_MAP[size]['Paw Print Fleece Blanket']]
        pw, ph = pad[SIZE_MAP[size]['Cooling Comfort Pad']]
        rows.append((size, DIM(fw, fh), DIM(pw, ph), L(pw)))
    out['calm-comfort-kit'] = block(
        soft_intro + ' The blanket and the cooling pad both change.',
        ['Kit size', 'Blanket', 'Cooling pad', 'Suits a back length up to'],
        rows,
        ['Medium and Large share the same blanket, which is the largest the '
         'maker offers. The cooling pad is what grows between them.'])
    return out


# ------------------------------------------------- corrections to other copy
# The Skeleton Suit's chart states the fabric does not stretch. Keeping a bullet
# that promises stretch next to a table that tells you to size up would be
# telling the customer two different things about the same garment.
COPY_FIX = {
    'wagvive-glow-skeleton-suit': [
        ('<li>Soft stretch knit, pulls on over the head</li>',
         '<li>Soft brushed knit, pulls on over the head</li>'),
    ],
}


# ----------------------------------------------------------------------- apply
def api(path, method='GET', payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def strip_old(html):
    """Remove any guide already present, ours or the earlier hand written one.

    Both end where the delivery promise begins, which closes every description
    in the store. Matching on that rather than on the table tags is what lets
    the trailing notes go too: the robe's old "Dogs over 55 lb are larger than
    this robe is made for" belongs to the wrong table and must not survive it.
    """
    html = re.sub(rf'<div class="{MARK}">.*?</div>', '', html, flags=re.S)
    html = re.sub(rf'<h3[^>]*>\s*{HEAD}\s*</h3>.*?(?=<p><strong>Arrives in)',
                  '', html, flags=re.S)
    return html.strip()


def insert(html, blk):
    html = strip_old(html)
    m = re.search(r'<p><strong>Arrives in [^<]*</strong></p>', html)
    return (html[:m.start()] + blk + html[m.start():]) if m else html + blk


def main():
    apply = '--apply' in sys.argv
    want = dict(guides())
    want.update(kit_guides())

    prods = api('products.json?limit=250&status=active')['products']
    by_handle = {p['handle']: p for p in prods}
    sized = [p['handle'] for p in prods
             if any(o['name'].lower() == 'size' for o in p['options'])]

    missing = [h for h in sized if h not in want]
    extra = [h for h in want if h not in by_handle]
    for h in missing:
        print(f'  ! no guide written for {h}')
    for h in extra:
        print(f'  ! guide for a handle that is not live: {h}')
    if missing or extra:
        return 1

    print(f'{len(sized)} active products take a size, and all {len(sized)} '
          f'have a guide.\n')
    changed = []
    for h in sorted(sized):
        p = by_handle[h]
        new = insert(p['body_html'], want[h])
        for old, rep in COPY_FIX.get(h, []):
            new = new.replace(old, rep)
        if new.strip() == (p['body_html'] or '').strip():
            print(f'  {p["title"]:44} already current')
            continue
        had = '<table' in (p['body_html'] or '')
        rows = want[h].count('<tr>') - 1
        print(f'  {p["title"]:44} {"REPLACE" if had else "add    "} '
              f'{rows:2d} row table')
        changed.append((p, new))

    if not changed:
        print('\nNothing to do.')
        return 0
    if not apply:
        print(f'\n{len(changed)} product(s) would change. Dry run, use --apply.')
        return 0

    for p, new in changed:
        api(f'products/{p["id"]}.json', 'PUT',
            {'product': {'id': p['id'], 'body_html': new}})
        print(f'  wrote {p["title"]}')

    # Verify on the STOREFRONT, never on the write's return value. Shopify's CDN
    # serves stale renders for minutes after a write, so this asks for the
    # rendered page with a cache buster and checks the marker class, which is
    # ours alone. The words "Choosing a size" would not prove anything: the old
    # guides used them too.
    print('\n--- storefront verification ---')
    bad = 0
    for p, _ in changed:
        url = (f'https://{SHOP}/products/{p["handle"]}'
               f'?nocache={int(time.time() * 1000)}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                page = r.read().decode('utf-8', 'replace')
        except Exception as e:
            print(f'  {p["title"]:44} FETCH FAILED {e}')
            bad += 1
            continue
        ok = MARK in page
        print(f'  {p["title"]:44} {"live" if ok else "NOT VISIBLE"}')
        bad += not ok
        time.sleep(0.3)

    if bad:
        print(f'\n{bad} product(s) did not show the guide. The CDN serves '
              f'stale renders for a few minutes, so re-run before assuming '
              f'a real failure.')
        return 1
    print('\nEvery size product shows its measurement table on the storefront.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
