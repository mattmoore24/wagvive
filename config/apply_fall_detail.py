#!/usr/bin/env python3
"""Add the SECOND house shot to fall products that only had one.

Purging CJ photography left six products on a single image, which is a thin
product page. These are the companion shots: the skeleton suit glowing in the
dark, treats buried in the snuffle mat, a treat tucked inside the turkey's
carrot, balls loaded in the launcher hopper, the chew toy's hollow interior, the
brush's bristle face.

They are DELIBERATELY NOT wired to any variant. `variant.image_id` is what drives
the swatch and the cart thumbnail, so pointing a variant at a detail shot would
show a close-up of three vegetables at the moment someone decides to buy. These
simply sit second in the gallery.

Files live in config/branding/fall-detail/<handle>.jpg, a separate folder from
config/branding/fall/ so `apply_fall_art.py` never picks them up and tries to
match them to an option value.

    python config/apply_fall_detail.py            # report
    python config/apply_fall_detail.py --apply
"""
import base64, io, json, os, sys, time, urllib.error, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'config', 'branding', 'fall-detail')
sys.path.insert(0, os.path.join(ROOT, 'config'))
from apply_fall_art import api, by_handle          # noqa: E402


def main():
    apply = '--apply' in sys.argv
    if not os.path.isdir(ART):
        print('no detail art directory'); return 1
    files = sorted(f for f in os.listdir(ART) if f.lower().endswith('.jpg'))
    if not files:
        print('no detail art'); return 1

    problems = []
    for fn in files:
        handle = os.path.splitext(fn)[0]
        p = by_handle(handle)
        if not p:
            print(f'{handle}: product not found'); problems.append(handle); continue
        fname = f'{handle}--detail.jpg'
        already = any(fname in im['src'].split('/')[-1] for im in p['images'])
        print(f"{p['title']:44} {len(p['images'])} image(s)  "
              f"{'detail already present' if already else 'add detail'}")
        if already or not apply:
            continue
        im = Image.open(os.path.join(ART, fn)).convert('RGB')
        im = im.resize((1600, 1600), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=92, optimize=True)
        api('POST', f"products/{p['id']}/images.json", {'image': {
            'attachment': base64.b64encode(buf.getvalue()).decode(),
            'filename': fname, 'position': 2,
            'alt': f"{p['title']} detail"}})
        print('      uploaded at position 2')

    if not apply:
        print('\nDry run. Use --apply.'); return 0

    print('\n--- verify ---')
    for fn in files:
        handle = os.path.splitext(fn)[0]
        p = by_handle(handle)
        if not p: continue
        names = [im['src'].split('/')[-1].split('?')[0] for im in p['images']]
        unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
        ok = any('--detail' in n for n in names) and not unwired
        print(f"  {p['title']:44} {len(names)} images  "
              f"{'ok' if ok else 'CHECK'}  lead={names[0][:40]}")
        if not ok: problems.append(handle)
    if problems:
        print(f'\n{len(set(problems))} need attention'); return 1
    print('\nEvery one-image product now has a second house shot.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
