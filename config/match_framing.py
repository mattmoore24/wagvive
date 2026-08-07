#!/usr/bin/env python3
"""Reframe a regenerated product photo to match the shot it replaces.

The house style is every product on the same cream ground with consistent
framing, so a replacement shot has to sit in the frame exactly where the old one
did. Runway does not preserve framing across an edit: asked to retouch one small
surface it re-renders the scene, and the subject drifts and changes scale.

Rather than judging that by eye, this measures the subject's bounding box in
both images and crops the new one so its subject lands at the same relative
position and the same relative size as the old one. Deterministic, and it makes
the replacement drop straight into a catalogue of 141 other shots without
looking off.

    python config/match_framing.py OLD.png NEW.png OUT.jpg [--size 1024]
"""
import os, sys

from PIL import Image, ImageChops

BG_TOL = 14


def content_box(im):
    """Bounding box of the subject, and the background colour behind it.

    Measured against the mean of the four corner patches rather than a fixed
    colour, because the backdrop carries a soft vignette.
    """
    w, h = im.size
    s = max(w // 40, 8)
    patches = [im.crop(b) for b in ((0, 0, s, s), (w - s, 0, w, s),
                                    (0, h - s, s, h), (w - s, h - s, w, h))]
    px = [p.resize((1, 1), Image.LANCZOS).getpixel((0, 0)) for p in patches]
    bg = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
    diff = ImageChops.difference(im, Image.new('RGB', im.size, bg))
    mask = diff.convert('L').point(lambda v: 255 if v > BG_TOL else 0)
    return mask.getbbox(), bg


def match(old, new, out_px=1024):
    ob, _ = content_box(old)
    nb, bg = content_box(new)
    if not ob or not nb:
        raise SystemExit('could not find the subject in one of the images')

    ow, oh = old.size
    nw, nh = new.size
    # where the OLD subject sits, as fractions of its frame
    o_cx, o_cy = (ob[0] + ob[2]) / 2 / ow, (ob[1] + ob[3]) / 2 / oh
    o_w = (ob[2] - ob[0]) / ow
    n_cx, n_cy = (nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2
    n_w = nb[2] - nb[0]

    side = n_w / o_w                      # crop wide enough to match scale
    left = n_cx - o_cx * side
    top = n_cy - o_cy * side

    # Pad rather than clamp: clamping would move the subject back off-position,
    # which is the whole thing being corrected.
    canvas = Image.new('RGB', (int(round(side)), int(round(side))), bg)
    canvas.paste(new, (int(round(-left)), int(round(-top))))
    result = canvas.resize((out_px, out_px), Image.LANCZOS)

    rb, _ = content_box(result)
    r_cx, r_cy = (rb[0] + rb[2]) / 2 / out_px, (rb[1] + rb[3]) / 2 / out_px
    r_w = (rb[2] - rb[0]) / out_px
    print(f'  old subject: centre ({o_cx:.3f}, {o_cy:.3f}) width {o_w:.3f}')
    print(f'  new subject: centre ({r_cx:.3f}, {r_cy:.3f}) width {r_w:.3f}')
    print(f'  residual   : centre off by ({abs(r_cx-o_cx)*100:.1f}%, '
          f'{abs(r_cy-o_cy)*100:.1f}%), width off by {abs(r_w-o_w)*100:.1f}%')
    return result


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 3:
        print(__doc__)
        return 2
    size = 1024
    if '--size' in sys.argv:
        size = int(sys.argv[sys.argv.index('--size') + 1])
    old = Image.open(args[0]).convert('RGB')
    new = Image.open(args[1]).convert('RGB')
    print(f'{os.path.basename(args[0])} -> {os.path.basename(args[1])}')
    out = match(old, new, size)
    out.save(args[2], 'JPEG' if args[2].lower().endswith(('.jpg', '.jpeg'))
             else 'PNG', quality=95, optimize=True, subsampling=0)
    print(f'  wrote {args[2]} ({os.path.getsize(args[2])//1024} KB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
