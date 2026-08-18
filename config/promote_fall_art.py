"""Promote the house art to position 1 on each fall product.

Uploading is not enough. A new image lands LAST, so the CJ photo stays at
position 1 and remains the COLLECTION CARD and the product hero. The variant
swatches were correct while every product card still showed the old photo.
"""
import os, sys
sys.path.insert(0, 'config')
from apply_fall_art import api, by_handle, art_files

files = art_files()
bad = []
for handle, looks in sorted(files.items()):
    p = by_handle(handle)
    if not p:
        continue
    lead = sorted(looks)[0]
    fname = f"{handle}__{lead}.jpg" if lead != '_' else f"{handle}.jpg"
    img = next((im for im in p['images'] if fname in im['src'].split('/')[-1]), None)
    if not img:
        print(f'  {handle}: {fname} not found on product'); bad.append(handle); continue
    if img['position'] == 1:
        print(f"  {p['title']:44} already leading"); continue
    api('PUT', f"products/{p['id']}/images/{img['id']}.json",
        {'image': {'id': img['id'], 'position': 1}})
    print(f"  {p['title']:44} {fname} -> position 1")

print('\n--- verify on the live product ---')
for handle, looks in sorted(files.items()):
    p = by_handle(handle)
    if not p: continue
    first = p['images'][0]['src'].split('/')[-1].split('?')[0]
    ok = first.startswith(handle)
    print(f"  {p['title']:44} {first[:46]:48} {'ok' if ok else 'STILL CJ'}")
    if not ok: bad.append(handle)
sys.exit(1 if bad else 0)
