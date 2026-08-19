#!/usr/bin/env python3
"""Write the size guide for every sized product, on the ONE canonical scale.

Replaces the earlier per-product guides, which were correct about measurements
but expressed in each supplier's own letters - so the beagle owner read "XS" on
the robe and "4XL" on the hoodie and had no way to know those were the same dog.
`config/size_scale.py` is the scale; this file renders it.

ORDER OF INFORMATION IS THE WHOLE POINT. Weight first, breeds second,
measurements last. Nobody knows their dog's chest girth. Everybody knows what
it weighs and roughly what breed it is. The old guides led with girth, which is
the number that decides fit but the one a customer cannot answer, so it read as
homework. Girth is still there, last, for anyone who wants to measure.

Every product shows THE SAME weight and breed text for a given letter, because
that is the promise: one dog, one letter, whole store.

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
sys.path.insert(0, os.path.join(ROOT, 'config'))
from size_scale import SCALE, BY_SIZE, ORDER, weight_text, FURNITURE  # noqa: E402

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

MARK = 'wagvive-size-guide'
HEAD = 'Choosing a size'
STYLE = ('<style>.wv-size{width:100%;border-collapse:collapse;margin:0 0 1em;'
         'font-size:.95em}.wv-size th,.wv-size td{border:1px solid #DCD2C1;'
         'padding:.5em .6em;text-align:left;vertical-align:top}'
         '.wv-size th{background:#F7F2E9;font-weight:600}</style>')


def inch(cm):
    v = cm / 2.54
    return f'{v:.0f}' if abs(v - round(v)) < 0.05 else f'{v:.1f}'


def L(cm):
    return f'{inch(cm)} in ({cm:g} cm)'


def LR(a, b):
    return f'{inch(a)} to {inch(b)} in ({a:g} to {b:g} cm)'


# canonical size -> the garment measurement of the variant we actually ship.
# Transcribed from the maker charts; see size_scale.MAP for which supplier size
# each one is.
FIT = {
 'wagvive-pumpkin-hoodie': ('Chest', {
    'XS': L(32), 'S': L(47), 'M': L(64), 'L': L(79), 'XL': L(87)}),
 'wagvive-big-dog-costume': ('Costume chest', {
    'M': L(68), 'L': L(78), 'XL': L(93)}),
 'wagvive-glow-skeleton-suit': ('Chest', {'XS': L(34), 'S': L(42)}),
 'wagvive-jack-o-lantern-sweater': ('Chest', {
    'XS': L(30), 'S': L(48), 'M': L(56)}),
 'wagvive-thanksgiving-turkey-coat': ('Chest', {'XS': L(36), 'S': L(46)}),
 'wagvive-quick-dry-bath-robe': ('Chest', {
    'S': LR(45, 55), 'M': LR(57, 67), 'L': LR(70, 80)}),
 'wagvive-paw-washing-cup': ('Cup depth', {
    'S': L(11), 'M': L(13.5), 'L': L(15)}),
 'wagvive-paw-print-fleece-blanket': ('Blanket size', {
    'S': '20 x 30 in (52 x 76 cm)', 'L': '30 x 41 in (76 x 104 cm)'}),
 'wagvive-waterproof-snuggle-blanket': ('Blanket size', {
    'S': '20 x 28 in (50 x 70 cm)', 'L': '28 x 39 in (71 x 100 cm)'}),
 'wagvive-cooling-comfort-pad': ('Pad size', {
    'M': '24 x 20 in (60 x 50 cm)', 'L': '28 x 22 in (70 x 55 cm)',
    'XL': '39 x 28 in (100 x 70 cm)'}),
}

KIT_HANDLES = ['calm-comfort-kit', 'grooming-essentials-kit', 'new-puppy-kit',
               'travel-kit']

NOTE = {
 'wagvive-glow-skeleton-suit':
    'A small-dog suit: the maker states it does not fit large breeds, and the '
    'fabric does not stretch, so measure rather than guess. It sells in XS and '
    'S only. For a bigger dog see the Pumpkin Hoodie, which runs the full XS '
    'to XL.',
 'wagvive-big-dog-costume':
    'Built for bigger dogs, so it starts at M. For anything smaller see the '
    'Pumpkin Hoodie or the Jack-o-Lantern Sweater.',
 'wagvive-pumpkin-hoodie':
    'The only costume that covers the whole scale, XS to XL.',
 'wagvive-paw-washing-cup':
    'All three share the same 2.8 in (7 cm) opening, so the size changes how '
    'DEEP the cup is, not how wide. A paw wider than 2.8 in will not fit any '
    'size.',
 'wagvive-paw-print-fleece-blanket':
    'Two sizes, so they cover the small and large ends. A blanket wants to '
    'cover a curled dog, so err large if you are between.',
 'wagvive-waterproof-snuggle-blanket':
    'Two sizes, covering the small and large ends. Err large if you are '
    'between.',
 'wagvive-cooling-comfort-pad':
    'A cooling pad only works where the dog is touching it, so it should be '
    'long enough to lie out on.',
}
SIZE_UP = ('If your dog is between two sizes, choose the larger. Every size on '
           'this page means the same dog it means everywhere else on Wagvive.')


def table(cols, rows):
    th = ''.join(f'<th>{c}</th>' for c in cols)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
                   for r in rows)
    return (f'{STYLE}<table class="wv-size"><thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


def block(intro, cols, rows, notes):
    n = ''.join(f'<p>{x}</p>' for x in notes if x)
    return (f'<div class="{MARK}"><h3>{HEAD}</h3><p>{intro}</p>'
            f'{table(cols, rows)}{n}</div>')


def guide_for(handle, sizes_offered):
    """Weight -> breeds -> measurement, for the sizes this product sells."""
    if handle in FURNITURE:
        # Real dimensions, in the same "in (cm)" form as every other guide.
        # The old option labels wrote inches as 20" x 28", which reads fine to
        # a human but is not a unit any checker can parse.
        dims = {'Armchair or car seat': '20 x 28 in (50 x 70 cm)',
                'Two seat sofa': '28 x 39 in (71 x 100 cm)',
                'Three seat sofa': '39 x 57 in (100 x 145 cm)'}
        rows = [(f'<strong>{v}</strong>', dims[v]) for v in FURNITURE[handle].values()]
        return block(
            'This one is sized to your FURNITURE, not to your dog, so it is '
            'deliberately not on the XS to XL dog scale used everywhere else '
            'on Wagvive. Measure the seat you want to protect.',
            ['Fits', 'Cover size'], rows,
            ['Any size suits any dog. What matters is the furniture '
             'underneath.'])

    label, fits = FIT[handle]
    rows = []
    for s in ORDER:
        if s not in sizes_offered:
            continue
        b = BY_SIZE[s]
        rows.append((f'<strong>{s}</strong>', weight_text(s), b['breeds'],
                     fits.get(s, '-')))
    return block(
        'Pick by your dog’s weight. Breed examples are there as a sanity '
        'check, and the measurement is for anyone who wants to be exact.',
        ['Size', 'Dog weight', 'Typical breeds', label], rows,
        [SIZE_UP, NOTE.get(handle)])


def kit_guide(sizes_offered):
    """A kit sizes several items at once, so the honest measurement to publish
    is the DOG's chest band for that letter, not any one component's garment
    spec - the components differ per kit but the dog does not."""
    rows = []
    for s in ORDER:
        if s not in sizes_offered:
            continue
        b = BY_SIZE[s]
        rows.append((f'<strong>{s}</strong>', weight_text(s), b['breeds'],
                     LR(*b['chest_cm'])))
    return block(
        'One pick sizes every item in the kit at once. Choose by your dog’s '
        'weight, exactly as you would for any single product on Wagvive.',
        ['Size', 'Dog weight', 'Typical breeds', 'Chest girth'], rows,
        [SIZE_UP,
         'Items in the kit that have no size, like the toys, are the same in '
         'every kit size.'])


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
    prods = api('products.json?limit=250&status=active')['products']
    changed = []
    for p in sorted(prods, key=lambda x: x['title']):
        opt = next((o for o in p['options'] if o['name'].lower() == 'size'), None)
        if not opt:
            continue
        h = p['handle']
        offered = set(opt['values'])
        if h in KIT_HANDLES:
            blk = kit_guide(offered)
        elif h in FURNITURE or h in FIT:
            blk = guide_for(h, offered)
        else:
            print(f'  ! no guide defined for {h}')
            return 1
        new = insert(p['body_html'], blk)
        if new.strip() != (p['body_html'] or '').strip():
            changed.append((p, new))
        print(f"  {p['title'][:44]:46} {sorted(offered, key=lambda s: ORDER.index(s) if s in ORDER else 99)}")

    if not changed:
        print('\nAll guides already current.')
        return 0
    if not apply:
        print(f'\n{len(changed)} guide(s) would change. Dry run, use --apply.')
        return 0
    for p, new in changed:
        api(f"products/{p['id']}.json", 'PUT',
            {'product': {'id': p['id'], 'body_html': new}})
        print(f"  wrote {p['title']}")

    print('\n--- storefront verification ---')
    bad = 0
    for p, _ in changed:
        url = f"https://{SHOP}/products/{p['handle']}?nocache={int(time.time()*1000)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            page = urllib.request.urlopen(req, timeout=90).read().decode('utf-8', 'replace')
            ok = MARK in page
        except Exception as e:
            ok = False
            print(f'   fetch failed {e}')
        print(f"  {p['title'][:44]:46} {'live' if ok else 'NOT VISIBLE'}")
        bad += not ok
        time.sleep(0.3)
    if bad:
        print(f'\n{bad} not visible yet (CDN lag). Re-run to confirm.')
        return 1
    print('\nEvery sized product shows the canonical guide.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
