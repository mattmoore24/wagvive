#!/usr/bin/env python3
"""Build the Instagram profile picture from the existing Wagvive icon mark.

Not generated art. Instagram sits next to the site, the emails and the pins, so
the avatar has to be the SAME mark, rebuilt for the constraints of a circular
avatar. Those constraints are what make `icon-1024.png` unusable as-is:

  * Instagram CROPS TO A CIRCLE. In icon.svg the toe pads run to the top edge of
    the 512 viewBox, so a circular crop clips the outer two toes and flattens
    the top of the middle two. The mark needs to sit inside the inscribed circle
    with real margin.
  * It is displayed TINY: about 32px in comments, 56px in the feed, 110px on the
    profile. Anything with fine detail or text turns to mush. The paw plus pulse
    is the right element precisely because it survives that.
  * The feed is WHITE. A cream avatar dissolves into it, which is why the
    green-ground variant is the default.

Geometry is redrawn from icon.svg rather than recoloring the flattened PNG,
because the pulse line has to change color independently of the paw and in the
PNG they share one alpha channel.

    python config/branding/make_avatar.py
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'config', 'branding')

SAGE = (107, 143, 113)      # #6B8F71 brand green, from icon.svg
CREAM_CARD = (247, 242, 233)  # #F7F2E9
CREAM_PAGE = (239, 231, 218)  # #EFE7DA
INK = (58, 48, 38)            # #3A3026

SIZE = 1024                 # export size; Instagram wants >=320, upload bigger
SS = 4                      # supersample factor for clean curved edges

# icon.svg geometry, in its native 512 viewBox
TOES = [  # cx, cy, rx, ry, rotation
    (120, 140, 46, 60, -25),
    (205, 80, 42, 56, -8),
    (307, 80, 42, 56, 8),
    (392, 140, 46, 60, 25),
]
PAD = (90, 228, 422, 440)   # x0, y0, x1, y1
PAD_RADIUS = 100
PULSE = [(128, 335), (188, 335), (218, 263), (250, 388),
         (282, 298), (312, 335), (402, 335)]
PULSE_W = 15

# The mark occupies this fraction of the canvas width. 0.62 keeps every toe
# inside the inscribed circle with margin to spare; the mark's own bounding box
# is wider than it is tall, so the binding constraint is horizontal.
MARK_SCALE = 0.62


def rotated_ellipse(canvas, cx, cy, rx, ry, deg, fill, k):
    """PIL cannot draw a rotated ellipse, so draw it upright and rotate."""
    pad = int(max(rx, ry) * 2 * k) + 8
    layer = Image.new('RGBA', (pad, pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    mid = pad / 2
    d.ellipse([mid - rx * k, mid - ry * k, mid + rx * k, mid + ry * k], fill=fill)
    layer = layer.rotate(deg, resample=Image.BICUBIC, center=(mid, mid))
    canvas.alpha_composite(layer, (int(cx * k - mid), int(cy * k - mid)))


def draw_mark(size, paw, pulse):
    """The paw mark on a transparent square of `size`, drawn at `size`/512."""
    k = size / 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for cx, cy, rx, ry, deg in TOES:
        rotated_ellipse(img, cx, cy, rx, ry, deg, paw, k)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD[0] * k, PAD[1] * k, PAD[2] * k, PAD[3] * k],
                        radius=PAD_RADIUS * k, fill=paw)
    d.line([(x * k, y * k) for x, y in PULSE], fill=pulse,
           width=max(int(PULSE_W * k), 1), joint='curve')
    # round the pulse line's end caps, which ImageDraw.line does not do
    r = max(int(PULSE_W * k), 1) / 2
    for x, y in (PULSE[0], PULSE[-1]):
        d.ellipse([x * k - r, y * k - r, x * k + r, y * k + r], fill=pulse)
    return img


def bbox_trim(img):
    return img.crop(img.getbbox())


def build(bg, paw, pulse, name):
    """Compose one avatar: mark centered on `bg`, sized to clear a circle crop."""
    big = SIZE * SS
    canvas = Image.new('RGBA', (big, big), bg + (255,))
    mark = bbox_trim(draw_mark(big, paw, pulse))

    target_w = int(big * MARK_SCALE)
    scale = target_w / mark.width
    mark = mark.resize((target_w, max(int(mark.height * scale), 1)),
                       Image.LANCZOS)
    canvas.alpha_composite(mark, ((big - mark.width) // 2,
                                  (big - mark.height) // 2))

    out = canvas.resize((SIZE, SIZE), Image.LANCZOS).convert('RGB')
    path = os.path.join(OUT, name)
    out.save(path, quality=95)
    return path, out


def circle_preview(img, px):
    """What Instagram actually shows: a circular crop at display size."""
    small = img.resize((px, px), Image.LANCZOS).convert('RGBA')
    mask = Image.new('L', (px * 4, px * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, px * 4, px * 4], fill=255)
    small.putalpha(mask.resize((px, px), Image.LANCZOS))
    return small


def main():
    variants = [
        # bg,          paw,        pulse,      filename
        (SAGE,       CREAM_CARD, SAGE,       'avatar-green.png'),
        (CREAM_PAGE, SAGE,       CREAM_CARD, 'avatar-cream.png'),
        (INK,        CREAM_CARD, INK,        'avatar-ink.png'),
    ]
    built = []
    for bg, paw, pulse, name in variants:
        path, img = build(bg, paw, pulse, name)
        built.append((name, img))
        print(f'  {name:20} {os.path.relpath(path, ROOT)}')

    # contact sheet: each variant at real Instagram display sizes
    sizes = [110, 56, 32]
    pad, gap, label_h = 40, 34, 26
    row_h = max(sizes) + label_h + gap
    sheet_w = pad * 2 + sum(sizes) + gap * (len(sizes) - 1) + 220
    sheet = Image.new('RGB', (sheet_w, pad * 2 + row_h * len(built)),
                      (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for r, (name, img) in enumerate(built):
        y = pad + r * row_h
        d.text((pad, y + max(sizes) // 2), name.replace('avatar-', '')
               .replace('.png', '').upper(), fill=(40, 40, 40))
        x = pad + 200
        for s in sizes:
            circ = circle_preview(img, s)
            sheet.paste(circ, (x, y + (max(sizes) - s) // 2), circ)
            d.text((x, y + max(sizes) + 6), f'{s}px', fill=(120, 120, 120))
            x += s + gap
    sp = os.path.join(OUT, 'avatar-contact-sheet.png')
    sheet.save(sp)
    print(f'\n  contact sheet -> {os.path.relpath(sp, ROOT)}')
    print('  (110px = profile page, 56px = feed, 32px = comments)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
