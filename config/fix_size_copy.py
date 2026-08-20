#!/usr/bin/env python3
"""Bring the PROSE and the SEO fields into line with the canonical size scale.

`apply_size_scale.py` moved the option values and `apply_size_guides.py`
rewrote the guide tables, but the surrounding sales copy and the SEO metafields
still described the OLD catalogue. That is worse than untidy: the Big Dog
Costume's own description said "This runs 3XL to 8XL" directly above a size
picker offering M, L and XL, and its Google result read
"Large Dog Halloween Costume, 3XL to 8XL". The Pumpkin Hoodie led with
"Thirteen sizes" while selling five.

SEO METAFIELDS ARE A SEPARATE FIELD from body_html and feed the meta
description, og:description and twitter:description
(docs/knowledge/shopify-liquid-and-cdn-traps.md postscript). Fixing the body
alone leaves the search result wrong, which is exactly the trap that bit the
Skeleton Suit's stretch claim, so both are updated here together.

TWO NON-SIZING ERRORS the audit surfaced and this also fixes, because leaving a
known-false claim live once you have seen it is not an option:

  * Cooling Comfort Pad: the SEO said "Pressure Activated Gel Pad" and "the gel
    starts working" while the body says, correctly, "No gel, no chemicals" and
    that it is ice-silk fabric cooling by conduction. The SEO was describing a
    different product category.
  * Thanksgiving Turkey Sweater: the body called the third design "a mustard
    argyle" while the live option value, the SEO and the artwork all say Plaid.

    python config/fix_size_copy.py            # show the diff
    python config/fix_size_copy.py --apply
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

# handle -> {'body': [(old, new)], 'title_tag': str, 'description_tag': str}
# Every `body` pair is asserted to match before anything is written, so a copy
# edit elsewhere turns into a loud failure rather than a silent no-op.
FIX = {
 'wagvive-big-dog-costume': {
   'body': [('This runs 3XL to 8XL', 'This runs M to XL'),
            ('<li>Sizes 3XL to 8XL, built for large breeds</li>',
             '<li>Sizes M to XL, built for medium, large and giant breeds</li>')],
   'title_tag': 'Large Dog Halloween Costume, M to XL',
   'description_tag': 'A hooded costume built for bigger dogs, sizes M to XL. '
                      'Tiger, dinosaur or rabbit, each with ears and a tail.'},

 'wagvive-glow-skeleton-suit': {
   'body': [('Sizes S to XL here run small, so this\nsuits chihuahuas',
             'Sizes XS and S, so this suits chihuahuas'),
            ('which runs XS to 9XL, or the Big Dog Costume at 3XL to 8XL',
             'which runs XS to XL, or the Big Dog Costume at M to XL')],
   'title_tag': 'Glow in the Dark Dog Skeleton Costume, XS and S',
   'description_tag': 'A black four leg suit with a skeleton that glows after '
                      'dark. Soft brushed knit, in XS and S for small dogs.'},

 'wagvive-jack-o-lantern-sweater': {
   'body': [('<li>Four colourways, five sizes from XS to XL</li>',
             '<li>Two colourways, three sizes from XS to M</li>')],
   'title_tag': 'Jack-o-Lantern Dog Sweater, XS to M',
   'description_tag': 'Chunky orange and black knit with a glitter pumpkin on '
                      'the chest. Two colourways, three sizes from XS to M.'},

 'wagvive-pumpkin-hoodie': {
   'body': [('<p><strong>Thirteen sizes, so every dog gets one.</strong></p>',
             '<p><strong>Five sizes, so every dog gets one.</strong></p>'),
            ('the way to 9XL', 'the way to XL'),
            ('<li>Thirteen sizes, XS through 9XL</li>',
             '<li>Five sizes, XS through XL</li>')],
   'title_tag': 'Pumpkin Dog Hoodie, XS to XL, Fits Every Size',
   'description_tag': 'A fleece hoodie with a jack-o-lantern print, in five '
                      'sizes from XS to XL. Fits everything from a chihuahua '
                      'to a great dane.'},

 'wagvive-thanksgiving-turkey-coat': {
   'body': [('<li>Four sizes, small through extra large</li>',
             '<li>Two sizes, XS and S</li>'),
            ('a mustard\nargyle for every day in between',
             'a classic plaid for every day in between')],
   # title_tag as well as description_tag. The first pass fixed only the
   # description and left the TITLE reading "Turkey, Boo and Argyle", which is
   # the headline of the Google result and the og:title on every share - the
   # most visible copy on the product, and the one place the wrong design name
   # survived. The live option value is Plaid.
   'title_tag': 'Thanksgiving Dog Sweater, Turkey, Boo and Plaid',
   'description_tag': 'A chunky knit in three fall designs: a turkey for '
                      'Thanksgiving, a Boo for Halloween and a classic plaid. '
                      'Two sizes, XS and S.'},

 'wagvive-waterproof-snuggle-blanket': {
   'body': [],
   'description_tag': 'Soft on top, waterproof underneath, so muddy paws and '
                      'accidents stop at the fabric. Machine washable, two '
                      'sizes, for the sofa, the bed or the car.'},

 # Sizing AND the gel contradiction. The body has always been right.
 'wagvive-cooling-comfort-pad': {
   'body': [],
   'title_tag': 'Dog Cooling Mat, Ice Silk, No Gel or Water',
   'description_tag': 'No water, no power, no freezer. Your dog lies down and '
                      'the ice-silk fabric draws heat away. Three sizes for '
                      'crates, beds and car seats, wipe clean.'},
}


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


WORD = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
        'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
        'twelve': 12, 'thirteen': 13}


def verify(product_id):
    """Does the copy still describe the product that is actually on sale?

    NOT a blocklist of banned phrases. The first version of this check listed
    "three sizes" and "five sizes" as stale, and then flagged the Jack-o-Lantern
    and the Pumpkin Hoodie as broken immediately after correctly rewriting them
    to say exactly that - the phrases were only stale relative to the OLD
    catalogue. A blocklist cannot tell "wrong number" from "right number".

    So: parse any "<n> sizes" claim and compare it to the live option count,
    and separately look for supplier letters that no longer exist anywhere and
    for the two known factual contradictions.
    """
    p = api(f'products/{product_id}.json')['product']
    mf = api(f'products/{product_id}/metafields.json?namespace=global')['metafields']
    opt = next(o for o in p['options'] if o['name'].lower() == 'size')
    n_live = len(opt['values'])
    body = re.sub(r'<div class="wagvive-size-guide">.*?</div>', '',
                  p['body_html'], flags=re.S)
    txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body))
    txt += ' ' + ' '.join(m['value'] for m in mf)

    issues = []
    for m in re.finditer(r'\b(\w+)\s+sizes\b', txt):
        w = m.group(1).lower()
        n = WORD.get(w, int(w) if w.isdigit() else None)
        if n is not None and n != n_live:
            issues.append(f'claims {n} sizes, {n_live} live')
    old = set(re.findall(r'\b[2-9]XL\b', txt))
    if old:
        issues.append(f'retired supplier letters {sorted(old)}')
    contra = set(re.findall(r'the gel|mustard\s+argyle', txt))
    if contra:
        issues.append(f'contradiction {sorted(contra)}')
    return (not issues), '; '.join(issues)


def main():
    apply = '--apply' in sys.argv
    plan, problems = [], []

    for handle, fix in FIX.items():
        ps = api(f'products.json?handle={handle}&status=active')['products']
        if not ps:
            problems.append(f'{handle}: not found')
            continue
        p = ps[0]
        body = p['body_html']
        edits = []
        for old, new in fix.get('body', []):
            # Normalise whitespace when matching: the stored HTML wraps lines,
            # and a literal match would fail purely on where a newline landed.
            pat = re.compile(re.escape(old).replace(r'\ ', r'\s+')
                             .replace(r'\\n', r'\s+'), re.S)
            pat = re.compile(r'\s+'.join(map(re.escape, old.split())), re.S)
            if not pat.search(body):
                # Already applied is not a failure. Re-running a migration
                # should be a no-op, not an error, so only complain when the
                # NEW text is missing too - which would mean the copy was
                # edited to something else entirely and this fix no longer
                # describes reality.
                done = re.compile(r'\s+'.join(map(re.escape, new.split())), re.S)
                if done.search(body):
                    continue
                problems.append(f'{handle}: body text not found -> {old[:60]!r}')
                continue
            body = pat.sub(new, body, count=1)
            edits.append(old[:52])

        mf = api(f"products/{p['id']}/metafields.json?namespace=global")['metafields']
        seo = {m['key']: m for m in mf}
        seo_edits = []
        for key in ('title_tag', 'description_tag'):
            if key in fix and seo.get(key) and seo[key]['value'] != fix[key]:
                seo_edits.append(key)

        if body != p['body_html'] or seo_edits:
            plan.append((p, body, fix, seo, edits, seo_edits))
            print(f"{p['title'][:42]:44} body:{len(edits)}  seo:{seo_edits or '-'}")

    if problems:
        print('\nPROBLEMS, nothing written:')
        for x in problems:
            print(f'  ! {x}')
        return 1
    if not plan:
        print('Nothing to change.')
        return 0
    if not apply:
        print(f'\n{len(plan)} product(s) would change. Dry run, use --apply.')
        return 0

    for p, body, fix, seo, edits, seo_edits in plan:
        if body != p['body_html']:
            api(f"products/{p['id']}.json", 'PUT',
                {'product': {'id': p['id'], 'body_html': body}})
        for key in seo_edits:
            # Write via the PRODUCT resource, not the metafield endpoint: a
            # metafield-only write does not bump the product's updated_at, and
            # Shopify's page cache keys off that.
            api(f"products/{p['id']}.json", 'PUT',
                {'product': {'id': p['id'],
                             f'metafields_global_{key}': fix[key]}})
        print(f"  wrote {p['title']}")

    print('\n--- verify against the live product ---')
    bad = 0
    for p, _, fix, _, _, _ in plan:
        ok, why = verify(p['id'])
        print(f"  {p['title'][:42]:44} {'clean' if ok else why}")
        bad += not ok
    if bad:
        print(f'\n{bad} product(s) still carry stale size language')
        return 1
    print('\nAll copy and SEO now match the canonical scale.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
