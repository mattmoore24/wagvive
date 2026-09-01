#!/usr/bin/env python3
"""Fix the four wrong text blocks on EVERY product page (task #71).

These live in `templates/product.json`, inside the product-information section,
so they render identically on all 42 product pages. All four were written before
the catalogue changed and were found still live on 2026-08-05 during the
pre-spend audit of the Calm & Comfort Kit landing page.

  1. Trust badge          "Ships in 1-3 business days" uses an en dash, and a
                          hyphenated day range, both against house style.
  2. Shipping accordion   two more en dashes.
  3. Returns accordion    an em dash.
  4. Care & use accordion the bad one. It tells every customer to "rinse or wipe
                          clean after use and let it dry fully before storing",
                          which is wrong for the disposable wipes, wrong for the
                          plush toys, and wrong for the entire Calm & Comfort Kit
                          (a heartbeat plush, a compression wrap, a fleece
                          blanket, a cooling pad and a squeak plush; you rinse
                          none of them). It also says "grooming tools" on pages
                          with no grooming tools, and still references "older or
                          anxious dogs", which is the senior positioning retired
                          when the Senior Dog Kit went.

Because the block is global, the replacement cannot describe any one product. It
points at the description for specifics and states only rules that hold for
everything we sell.

Why a script rather than the theme editor: the same reason `fix_home_faq.py` and
`build_footer.py` are scripts. It is repeatable, it refuses to write a template
that still contains a forbidden dash, and it verifies against the admin asset
plus a real re-render instead of trusting the write.

Runs on the home PC only, because it needs config/shopify.env. The Shopify MCP
connector used by web sessions blocks writes to the live theme by policy.

    python config/fix_product_care_copy.py            # show the diff
    python config/fix_product_care_copy.py --apply    # write + verify live
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = 187585560865
TEMPLATE = 'templates/product.json'
PROBE_HANDLE = 'calm-comfort-kit'   # the page phase 1 buys traffic for

# path into templates/product.json -> new text. Paths are explicit so a theme
# edit that moves a block makes this fail loudly rather than write to the wrong
# place.
DETAILS = ['sections', 'main', 'blocks', 'product-details', 'blocks']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import delivery_promise as DP  # noqa: E402

# These strings are built from config/delivery_promise.py, NOT typed here.
# This file is wired to CI (.github/workflows/theme-copy-fix.yml) and rewrites
# these JSON paths UNCONDITIONALLY, without comparing current content. When the
# promise moved to "10 to 16 business days" on 2026-09-01 the literals below
# still said "1 to 3" and "5 to 12", so the next push to main would have
# silently restored the retired promise to every product page in the store.
EDITS = [
    {
        'name': 'trust badge, dispatch time',
        'path': DETAILS + ['wagvive_trust', 'blocks', 't3', 'blocks', 'l',
                           'settings', 'text'],
        'new': f'<p>Ships within {DP.DISPATCH_DAYS} business days</p>',
    },
    {
        'name': 'accordion, Shipping & delivery',
        'path': DETAILS + ['wagvive_details', 'blocks', 'r1', 'blocks', 'a',
                           'settings', 'text'],
        'new': (f'<p>Dispatched within {DP.DISPATCH_DAYS} business days. Typical '
                f'US delivery is {DP.WINDOW} from the day you order, with '
                'tracking emailed when your parcel is handed to the carrier. '
                'Free over $60, otherwise $5.95 flat.</p>'),
    },
    {
        'name': 'accordion, Returns',
        'path': DETAILS + ['wagvive_details', 'blocks', 'r2', 'blocks', 'a',
                           'settings', 'text'],
        'new': ('<p>30 days from delivery. Faulty, damaged, or incorrect items: '
                'we cover return shipping and replace or refund, your choice. '
                'Changed your mind is fine too. In that case return postage is '
                'on you.</p>'),
    },
    {
        'name': 'accordion, Care & use',
        'path': DETAILS + ['wagvive_details', 'blocks', 'r3', 'blocks', 'a',
                           'settings', 'text'],
        'new': ('<p>Care depends on the product, so check the description above '
                'for the specifics. As a rule: wipes and other disposables are '
                'single use, so throw each one away after use. Wash fabric items '
                'cool and skip the tumble dryer on anything with a waterproof '
                'backing. Wipe grooming tools clean and let them dry fully '
                'before storing. Introduce anything new gradually, with a few '
                'short calm sessions rather than one long one.</p>'),
    },
]

# Forbidden in store copy: literal dashes and the HTML entities the theme editor
# writes for them. The live template used &ndash; and &mdash;, not the raw chars,
# which is exactly why an eyeball check of the rendered page missed them.
BANNED = ('—', '–', '&mdash;', '&ndash;', '&#8212;', '&#8211;')

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])


def get_asset(key):
    q = urllib.parse.urlencode({'asset[key]': key})
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json?{q}',
        headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())['asset']['value']


def put_asset(key, value):
    body = json.dumps({'asset': {'key': key, 'value': value}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json',
        data=body, method='PUT',
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def dig(doc, path):
    node = doc
    for step in path[:-1]:
        node = node[step]
    return node, path[-1]


def main():
    apply = '--apply' in sys.argv
    raw = get_asset(TEMPLATE)

    # templates/*.json carry a generated-file comment block, which json.loads
    # rejects. Strip it, and keep it to put back.
    prefix = ''
    if raw.lstrip().startswith('/*'):
        end = raw.index('*/') + 2
        prefix, raw = raw[:end], raw[end:]

    doc = json.loads(raw)

    for edit in EDITS:
        try:
            parent, leaf = dig(doc, edit['path'])
            was = parent[leaf]
        except (KeyError, TypeError):
            print(f"REFUSING: block not found for {edit['name']}.")
            print(f"  path: {' > '.join(map(str, edit['path']))}")
            print('  The theme has been restructured. Re-check before writing.')
            return 1
        print(f"{edit['name']}:")
        print(f'   was: {was}')
        print(f"   now: {edit['new']}")
        if was == edit['new']:
            print('   (already correct)')
        parent[leaf] = edit['new']
        print()

    body = prefix + json.dumps(doc, ensure_ascii=False, indent=2)

    for bad in BANNED:
        if bad in body:
            print(f'REFUSING: template still contains {bad!r} somewhere.')
            occurrences = [ln.strip()[:100] for ln in body.split('\n')
                           if bad in ln]
            for o in occurrences[:6]:
                print(f'    {o}')
            return 1
    print('dash check passed: no em or en dashes, literal or entity')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    put_asset(TEMPLATE, body)

    # The admin asset is authoritative and immediate.
    fresh = get_asset(TEMPLATE)
    if fresh.lstrip().startswith('/*'):
        fresh = fresh[fresh.index('*/') + 2:]
    live = json.loads(fresh)
    ok = True
    for edit in EDITS:
        parent, leaf = dig(live, edit['path'])
        if parent[leaf] != edit['new']:
            print(f"ADMIN VERIFY FAILED: {edit['name']}")
            ok = False
    if not ok:
        return 1
    print('admin asset verified: all four blocks correct')

    # Then the rendered page, fetched IN FULL.
    #
    # Do NOT use the section rendering API here. It is the right tool for the
    # footer and homepage sections, but a product template's main section
    # returns `null` from `?sections=main` because Shopify will not render it
    # standalone without product context. An earlier version of this script
    # probed that endpoint, got null, and reported "still stale" on a write
    # that had in fact gone live instantly. A verifier that cries wolf is worse
    # than no verifier, because the next real failure gets ignored.
    #
    # Product pages also do not show the footer's cache behaviour: this change
    # was visible on the full page on the first fetch.
    url = (f'https://wagvive.com/products/{PROBE_HANDLE}'
           f'?nocache={int(time.time())}')
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            rendered = urllib.request.urlopen(req, timeout=90).read().decode(
                'utf-8', 'replace')
        except Exception as exc:
            print(f'  page fetch failed: {str(exc)[:60]}')
            time.sleep(10)
            continue
        gone = 'Rinse or wipe clean' not in rendered
        there = 'Care depends on the product' in rendered
        # Dashes only count in VISIBLE copy. The theme's own <style> blocks
        # carry em dashes in Shopify's CSS comments on every page, so scanning
        # raw HTML fails permanently and means nothing.
        visible = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', rendered,
                         flags=re.S | re.I)
        visible = re.sub(r'<[^>]+>', ' ', visible)
        clean = not any(b in visible for b in ('—', '–'))
        if gone and there and clean:
            print(f'live page verified (/products/{PROBE_HANDLE}): new care '
                  f'text present, old text gone, no dashes')
            return 0
        print(f'  attempt {attempt + 1}: not yet (new={there}, old_gone={gone}, '
              f'no_dashes={clean}), waiting')
        time.sleep(15)
    print('live page did not confirm; the ADMIN asset IS correct, so this is '
          'either CDN lag or a changed probe string. Check by hand.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
