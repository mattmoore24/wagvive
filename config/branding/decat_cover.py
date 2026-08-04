#!/usr/bin/env python3
"""Remove the composited cat from the waterproof cover photography.

The supplier drops the same cat, in the same place, onto every colourway. Wagvive
is dog-only, so it has to go. The quilt is a regular repeating texture that is
evenly lit across the bed, which means a patch lifted from the same height a few
hundred pixels to the right blends in without any visible seam - no inpainting
needed. The patch is feathered at the edges so the join is not a hard rectangle.

    python config/branding/decat_cover.py            # writes *_clean.jpg
    python config/branding/decat_cover.py --preview  # side-by-side check
"""
import os, sys

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'cj-raw', 'cover4', 'var')

# Cat bounding box in the 1920x1920 originals, measured off a coordinate grid.
# It must clear the cat by more than FEATHER on every side: inside the feathered
# band the original still shows through, so a box that merely touches the cat
# leaves a ghost of it bleeding around the edges.
BOX = (830, 440, 1290, 860)
# Donor origin. The only region large enough and free of the quilt edge, the
# floor and the white sheet is the lower-left of the quilt.
DONOR = (160, 760)
FEATHER = 30
# That region sits in shadow while the cat sits in the bright centre, so the
# patch is scaled to the mean colour of a ring just outside the box before it is
# pasted - otherwise it lands as an obvious dark blotch.
RING = 40


def declaw(path, out):
    im = Image.open(path).convert('RGB')
    x0, y0, x1, y1 = BOX
    w, h = x1 - x0, y1 - y0

    dx, dy = DONOR
    donor = im.crop((dx, dy, dx + w, dy + h))

    # Colour-match the donor to the ring of quilt immediately around the target.
    ring = im.crop((x0 - RING, y0 - RING, x1 + RING, y1 + RING))
    inner = Image.new('L', ring.size, 255)
    inner.paste(0, (RING, RING, RING + w, RING + h))
    ring_px = [p for p, m in zip(ring.getdata(), inner.getdata()) if m]
    if ring_px:
        n = len(ring_px)
        want = [sum(p[c] for p in ring_px) / n for c in range(3)]
        have = [sum(p[c] for p in donor.getdata()) / (w * h) for c in range(3)]
        scale = [(want[c] / have[c]) if have[c] else 1.0 for c in range(3)]
        donor = donor.point(lambda v, s=scale: v)  # placeholder replaced below
        bands = list(donor.split())
        bands = [b.point(lambda v, k=scale[i]: min(255, int(v * k)))
                 for i, b in enumerate(bands)]
        donor = Image.merge('RGB', bands)

    # Feathered alpha so the patch fades into the surrounding quilt.
    mask = Image.new('L', (w, h), 0)
    inner = Image.new('L', (w - 2 * FEATHER, h - 2 * FEATHER), 255)
    mask.paste(inner, (FEATHER, FEATHER))
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER / 2))

    im.paste(donor, (x0, y0), mask)
    im.save(out, quality=92)
    return out


def main():
    files = [f for f in sorted(os.listdir(SRC))
             if f.lower().endswith('.jpg') and '_clean' not in f]
    done = []
    for f in files:
        src = os.path.join(SRC, f)
        out = os.path.join(SRC, f.replace('.jpg', '_clean.jpg'))
        declaw(src, out)
        done.append((f, out))
        print(f'  {f:20} -> {os.path.basename(out)}')

    if '--preview' in sys.argv and done:
        before = Image.open(os.path.join(SRC, done[0][0])).convert('RGB')
        after = Image.open(done[0][1]).convert('RGB')
        for im in (before, after):
            im.thumbnail((640, 640))
        sheet = Image.new('RGB', (before.width + after.width + 12, before.height), 'white')
        sheet.paste(before, (0, 0))
        sheet.paste(after, (before.width + 12, 0))
        p = os.path.join(SRC, '_decat_preview.png')
        sheet.save(p)
        print(f'preview -> {p}')


if __name__ == '__main__':
    main()
