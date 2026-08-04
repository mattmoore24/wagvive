#!/usr/bin/env python3
"""
Sizing copy for every product where size or capacity is a real choice.

Source of truth is CJ's own size charts, captured in docs/qa/cj-variants.json.
Written here rather than typed into the admin so the copy is reviewable and
re-appliable. Apply with a Shopify `productUpdate` on `descriptionHtml`.

House style: plain language, no em or en dashes, ranges written with "to",
"5 to 12 business days" as the delivery promise. Dimensions are given in
inches first (US store) with centimetres alongside, because CJ publishes
centimetres and the two must not drift apart.

Dog weights are guidance for choosing a size, not a fit guarantee: coat and
build vary, so every guide says what to do when a dog falls between sizes.
"""

DELIVERY = '<p><strong>Arrives in 5 to 12 business days.</strong></p>'

SIZING_CSS = (
    '<style>.wv-size{width:100%;border-collapse:collapse;margin:0 0 1em;'
    'font-size:.95em}.wv-size th,.wv-size td{border:1px solid #DCD2C1;'
    'padding:.5em .6em;text-align:left;vertical-align:top}'
    '.wv-size th{background:#F7F2E9;font-weight:600}</style>'
)


def table(headers, rows):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'{SIZING_CSS}<table class="wv-size"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


# handle -> full replacement descriptionHtml
COPY = {}

# ---------------------------------------------------------------- bath robe
# CJ: XS 4 to 7.5kg, S 7.5 to 12.5kg, M 12.5 to 25kg. Those three are CJ's
# entire range, so the store is complete here; only the guidance was vague.
COPY['wagvive-quick-dry-bath-robe'] = (
    '<p><strong>From soaked to snug in one wrap.</strong></p>'
    '<p>A hooded microfibre robe that drinks the bathwater off your dog before it '
    'ends up on your walls. Wrap, fasten, and let them do the post-bath zoomies '
    'already dry.</p>'
    '<ul>'
    '<li><strong>Ultra-absorbent microfibre</strong> cuts drying time</li>'
    '<li><strong>Hooded wrap design</strong> stays on wiggly dogs</li>'
    '<li><strong>Machine washable</strong>, dries fast itself</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>This robe is sized by your dog\'s weight. Weigh them first, then pick from '
    'the table. If your dog is between two sizes, or has a thick double coat, '
    'choose the larger one.</p>'
    + table(
        ['Size', 'Your dog\'s weight', 'Typical breeds'],
        [
            ['XS', '9 to 16 lb (4 to 7.5 kg)',
             'Chihuahua, Yorkshire Terrier, Pomeranian, small Dachshund'],
            ['S', '16 to 27 lb (7.5 to 12.5 kg)',
             'Shih Tzu, Miniature Schnauzer, Cocker Spaniel, French Bulldog'],
            ['M', '27 to 55 lb (12.5 to 25 kg)',
             'Border Collie, Beagle, Springer Spaniel, Staffordshire Bull Terrier'],
        ])
    + '<p>Dogs over 55 lb are larger than this robe is made for.</p>'
    + DELIVERY
)

# ------------------------------------------------------------ paw wash cup
# CJ: small 11 x 8.5 x 7cm, medium 13.5 x 8.5 x 7cm, large 15 x 8.5 x 7cm.
# Only the depth changes between sizes, so fit is about paw size, not height.
COPY['wagvive-paw-washing-cup'] = (
    '<p><strong>Muddy walk in, clean paws out.</strong></p>'
    '<p>Add a little water, insert one muddy paw, twist gently. Soft silicone '
    'bristles inside the cup lift off the dirt before it reaches your floors.</p>'
    '<ul>'
    '<li><strong>Soft silicone bristles</strong> clean without scrubbing</li>'
    '<li><strong>Contained water</strong> means no bathroom wrestling match</li>'
    '<li><strong>Rinses clean</strong> in seconds</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>Pick by the width of your dog\'s paw. The cup needs to be wider than the '
    'paw so it can twist freely. All three sizes are the same height, so only the '
    'opening changes.</p>'
    + table(
        ['Size', 'Cup size', 'Suits'],
        [
            ['S', '4.3 x 3.3 x 2.8 in (11 x 8.5 x 7 cm)',
             'Toy and small breeds up to about 15 lb, such as a Chihuahua or Yorkshire Terrier'],
            ['M', '5.3 x 3.3 x 2.8 in (13.5 x 8.5 x 7 cm)',
             'Medium breeds roughly 15 to 45 lb, such as a Beagle or Cocker Spaniel'],
            ['L', '5.9 x 3.3 x 2.8 in (15 x 8.5 x 7 cm)',
             'Large breeds 45 lb and up, such as a Labrador or German Shepherd'],
        ])
    + '<p>If your dog is between sizes, choose the larger one. A cup that is too '
      'narrow will not turn around the paw.</p>'
    + DELIVERY
)

# ------------------------------------------------------- snuggle blanket
# CJ: XS 50 x 70cm, S 71 x 100cm. CJ also makes M, L and XL, which the store
# does not carry yet.
COPY['wagvive-waterproof-snuggle-blanket'] = (
    '<p><strong>The blanket that guards the couch.</strong></p>'
    '<p>Plush flannel on top, a waterproof layer through the middle. Drool, wet fur '
    'and accidents stay on the blanket, not in your cushions.</p>'
    '<ul>'
    '<li><strong>Waterproof membrane</strong> protects whatever is underneath</li>'
    '<li><strong>Plush flannel face</strong> dogs actually choose to lie on</li>'
    '<li><strong>Machine washable</strong>, holds up wash after wash</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>Measure the space you want to protect, not the dog. The blanket should be '
    'a little larger than the area so the edges tuck in.</p>'
    + table(
        ['Size', 'Blanket size', 'Covers'],
        [
            ['XS', '20 x 28 in (50 x 70 cm)',
             'A crate floor, a car seat, or a bed for a dog up to about 25 lb'],
            ['S', '28 x 39 in (71 x 100 cm)',
             'One sofa cushion, an armchair seat, or a bed for a dog up to about 60 lb'],
        ])
    + DELIVERY
)

# --------------------------------------------------------- fleece blanket
# CJ: S 52 x 76cm, M 76 x 104cm. The previous copy listed M as 100 x 75cm,
# which was wrong in both numbers and order.
COPY['wagvive-paw-print-fleece-blanket'] = (
    '<p><strong>The everywhere blanket.</strong></p>'
    '<p>A soft coral fleece throw for crates, car seats, sofa corners and anywhere '
    'else your dog decides is a bed. Light enough to pack, soft enough that they '
    'will not argue.</p>'
    '<ul>'
    '<li><strong>Double-sided coral fleece</strong> with stitched trim</li>'
    '<li><strong>Light and packable</strong> for travel and crates</li>'
    '<li><strong>Machine washable</strong>, quick to dry</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>Pick by where it will live. Both sizes suit any breed, so this is about the '
    'space rather than the dog.</p>'
    + table(
        ['Size', 'Blanket size', 'Best for'],
        [
            ['S', '20 x 30 in (52 x 76 cm)',
             'Crates, carriers, car seats, and dogs up to about 30 lb curling up'],
            ['M', '30 x 41 in (76 x 104 cm)',
             'Sofa corners, larger beds, and dogs up to about 70 lb stretching out'],
        ])
    + DELIVERY
)

# ----------------------------------------------------------- cooling pad
# Size names already carry inches. CJ also makes XS 40 x 30cm and S 50 x 40cm,
# which the store does not carry yet.
COPY['wagvive-cooling-comfort-pad'] = (
    '<p><strong>Cools the moment they lie down.</strong></p>'
    '<p>Ice-silk fabric moves body heat away by conduction rather than trapping it, '
    'so the surface stays cool without gels, water or power. No leaking, nothing to '
    'freeze, and nothing that stops working after twenty minutes. Roll it out on the '
    'floor, a sofa, a crate base or the back seat.</p>'
    '<ul>'
    '<li>Contact cooling that works as soon as your dog settles on it</li>'
    '<li>No gel, no chemicals, no charging</li>'
    '<li>Breathable and anti-slip on the underside</li>'
    '<li>Folds flat and weighs almost nothing, so it is easy to take along</li>'
    '<li>Machine washable at 30 to 40°C</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>Your dog should be able to lie on their side with all four legs on the pad. '
    'Measure them from nose to base of tail while they are lying down, then add a '
    'few inches. When in doubt, size up.</p>'
    + table(
        ['Size', 'Pad size', 'Suits'],
        [
            ['Medium', '24 x 20 in (61 x 51 cm)',
             'Small dogs up to about 25 lb, such as a Pug or Miniature Schnauzer'],
            ['Large', '28 x 22 in (71 x 56 cm)',
             'Medium dogs roughly 25 to 55 lb, such as a Beagle or Border Collie'],
            ['X-Large', '39 x 28 in (99 x 71 cm)',
             'Large dogs roughly 55 to 90 lb, such as a Labrador or Boxer'],
            ['XX-Large', '59 x 39 in (150 x 99 cm)',
             'Giant breeds over 90 lb, or two dogs sharing'],
        ])
    + DELIVERY
)

# ------------------------------------------------------------- sofa cover
# CJ: XS 50 x 70cm, S 71 x 100cm, M 100 x 145cm are the three the store sells,
# listed as Small, Medium and Large. CJ also makes L, XL, 2XL and 3XL up to
# 216 x 216cm, which the store does not carry. The old copy claimed the range
# reached "a full three-seater", which the largest stocked size does not.
COPY['wagvive-waterproof-sofa-furniture-cover'] = (
    '<p><strong>Let them on the sofa without losing the sofa.</strong></p>'
    '<p>A waterproof layer stops muddy paws, wet fur and accidents reaching the '
    'cushions. The top is short plush, the border is sherpa, so it reads as '
    'something you chose for the room rather than a mat you tolerate.</p>'
    '<ul>'
    '<li>Waterproof backing blocks moisture before it reaches upholstery</li>'
    '<li>Short plush face with a sherpa border, soft on both sides</li>'
    '<li>Machine washable, holds its colour</li>'
    '<li>Also works on a bed, a crate floor or the back seat of a car</li>'
    '</ul>'
    '<h3>Choosing a size</h3>'
    '<p>Measure the seat area you want to cover, then pick the size that matches or '
    'slightly overhangs it. These cover a seating area rather than wrapping a whole '
    'sofa, so for a long sofa most people use one per seat.</p>'
    + table(
        ['Size', 'Cover size', 'Covers'],
        [
            ['Small', '20 x 28 in (50 x 70 cm)',
             'A car seat, a crate floor, or one armchair seat cushion'],
            ['Medium', '28 x 39 in (71 x 100 cm)',
             'A generous armchair, or a large dog bed'],
            ['Large', '39 x 57 in (99 x 145 cm)',
             'The seat area of a two-seat sofa, or one end of a larger sofa'],
        ])
    + DELIVERY
)

# ------------------------------------------------------- anti-spill bowl
COPY['wagvive-anti-spill-floating-water-bowl'] = (
    '<p><strong>Water they will actually want to drink, without the mess.</strong></p>'
    '<p>A dual-layer floating design that slows water intake and prevents overflow, '
    'so eager drinkers stay hydrated without soaking the floor. The splash-proof '
    'frame and non-slip base keep it steady at home, in the car, or on the go. '
    'Ideal for senior dogs who need to stay ahead on hydration.</p>'
    '<ul>'
    '<li>Anti-overflow floating plate design</li>'
    '<li>Slows fast drinking to reduce gulping and mess</li>'
    '<li>Splash-proof, non-slip base</li>'
    '<li>Easy to disassemble and clean</li>'
    '</ul>'
    '<h3>Choosing a capacity</h3>'
    '<p>A rough guide is that dogs drink about one ounce of water per pound of body '
    'weight per day. Pick the size that holds a full day for your dog so you are not '
    'refilling constantly.</p>'
    + table(
        ['Capacity', 'Holds', 'Suits'],
        [
            ['1.5L', '50 fl oz', 'One dog up to about 50 lb'],
            ['2L', '68 fl oz', 'Larger dogs, or two dogs sharing one bowl'],
        ])
    + '<!--wagvive-bundle-upsell--><hr>'
)


# --------------------------------------------------------- dental/ear wipes
# Not a sizing product, but the same problem: the page sold two different
# products under one listing and the copy only described one of them. The
# variant images point at the matching tub and the gallery is ordered
# dental tub, dental in use, ear tub, ear in use, so selecting a variant lands
# on the right pair. Shopify only supports one featured image per variant, so
# the gallery cannot be filtered per variant without a theme change.
COPY['wagvive-ear-teeth-cleaning-wipes'] = (
    '<p><strong>A wipe is the version of dental and ear care that actually '
    'happens.</strong></p>'
    '<p>Two separate tubs of finger wipes, one for teeth and one for ears. You pull a '
    'wipe over a finger, clean, and throw it away. No paste to spit out, no bottle of '
    'solution, no brushing standoff. For most dogs it is the difference between a '
    'routine you keep and one you abandon in week two.</p>'
    '<h3>Which one do you need?</h3>'
    '<p>These are two different products, so choose the tub that matches the job. They '
    'are not interchangeable: the ear wipe is not made for the mouth, and the dental '
    'wipe is not made for the ear canal.</p>'
    + table(
        ['Choose', 'What it does', 'How often'],
        [
            ['<strong>Dental wipes (50)</strong>',
             'A textured wipe that scrubs along the gum line to lift plaque and freshen '
             'breath before it hardens into tartar.',
             'A few times a week. Little and often beats a perfect daily plan you give '
             'up on.'],
            ['<strong>Ear wipes (50)</strong>',
             'A softer, smoother wipe for the outer ear and the folds you can see, '
             'clearing wax and grime that would otherwise build up.',
             'About once a week. Floppy eared breeds and swimmers usually need it more '
             'often.'],
        ])
    + '<ul>'
      '<li>50 wipes per tub</li>'
      '<li>Fits over a finger, so you can feel what you are doing</li>'
      '<li>Single use, so nothing is carried between sessions or between ears</li>'
      '<li>No rinsing, no water, nothing to wipe off afterwards</li>'
      '</ul>'
      '<p><strong>How to use them.</strong> Slide one wipe over your index finger. For '
      'teeth, lift the lip and work along the outer surfaces where plaque collects, back '
      'to front. For ears, lift the ear flap and clean only the part you can see. Never '
      'push into the ear canal.</p>'
      '<p>Wipes clean what is already there. If you see persistent redness, discharge, '
      'swelling or a strong odour, that is a vet visit rather than a wipe.</p>'
    + DELIVERY
)
