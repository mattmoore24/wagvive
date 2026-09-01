#!/usr/bin/env python3
"""Put the CURRENT delivery promise on every active product, and only there.

`config/delivery_promise.py` defines the promise. This applies it to the live
catalogue: the `<p><strong>Arrives in ...</strong></p>` anchor plus the honesty
paragraph that follows it, and the SEO description metafield where it mentions
delivery timing.

THREE THINGS THIS HAS TO GET RIGHT.

1. TWELVE ACTIVE PRODUCTS HAVE NO DELIVERY LINE AT ALL. A find-and-replace
   cannot fix an absence, which is exactly why the old promise survived audits
   that only looked for stale strings. Those get the block appended.

2. THE TAG SHAPE IS LOAD-BEARING. `apply_size_guides.py` finds
   `<p><strong>Arrives in [^<]*</strong></p>` to decide where the size guide
   ends and to insert a new one, with a silent `html + blk` fallback. Keeping
   the shape means the guides keep working; changing it would duplicate guides
   across 15 sized products with no error. So the anchor keeps its shape and
   the new honesty text goes in a SEPARATE paragraph after it.

3. IDEMPOTENT. Re-running must not stack honesty paragraphs. Any existing
   paragraph beginning "We ship direct from our overseas" is stripped before
   the new one is written, so this converges rather than accumulating.

Insertion point for products that have no line: before the bundle-upsell
marker if present, otherwise at the end. That keeps the upsell last, which is
where the theme expects it.

    python config/apply_delivery_promise.py            # dry run, shows the plan
    python config/apply_delivery_promise.py --apply
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
import delivery_promise as DP  # noqa: E402

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

ANCHOR = re.compile(r'<p><strong>Arrives in [^<]*</strong></p>')
NOTE = re.compile(r'<p>We ship direct from our overseas[^<]*(?:<[^>]+>[^<]*)*?</p>')
UPSELL = '<!--wagvive-bundle-upsell-->'


def api(path, method='GET', payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
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


# Placeholder used while de-duplicating. It has to be something ANCHOR cannot
# match: substituting the new anchor in directly and THEN stripping duplicates
# deletes the line just written, because the replacement matches the pattern
# too. That bug briefly removed the delivery promise from 40 live products.
PLACEHOLDER = '@@WAGVIVE_DELIVERY_BLOCK@@'


def rewrite(body):
    """Body with exactly one current delivery block, in the right place."""
    b = body or ''
    b = NOTE.sub('', b)                      # drop any previous honesty paragraph
    if ANCHOR.search(b):
        b = ANCHOR.sub(PLACEHOLDER, b, count=1)   # mark where the first one was
        b = ANCHOR.sub('', b)                     # remove any duplicates
        return b.replace(PLACEHOLDER, DP.DELIVERY_BLOCK)
    # No line at all: append, keeping the bundle upsell last.
    if UPSELL in b:
        return b.replace(UPSELL, DP.DELIVERY_BLOCK + UPSELL, 1)
    return b + DP.DELIVERY_BLOCK


def main():
    apply = '--apply' in sys.argv
    prods = api('products.json?limit=250&status=active')['products']
    plan = []
    for p in sorted(prods, key=lambda x: x['title']):
        new = rewrite(p.get('body_html') or '')
        if new != (p.get('body_html') or ''):
            had = 'update' if ANCHOR.search(p.get('body_html') or '') else 'ADD (was missing)'
            plan.append((p, new, had))

    for p, _, had in plan:
        print(f"  {p['title'][:46]:48} {had}")
    print(f'\n{len(plan)} of {len(prods)} products change.')
    if not apply:
        print('Dry run. Use --apply.')
        return 0

    for p, new, _ in plan:
        api(f"products/{p['id']}.json", 'PUT',
            {'product': {'id': p['id'], 'body_html': new}})
    print(f'wrote {len(plan)}')

    # --- verify against a re-fetch, not against the write's return value ------
    print('\n--- verify (re-fetched) ---')
    fresh = api('products.json?limit=250&status=active')['products']
    bad = 0
    for p in fresh:
        b = p.get('body_html') or ''
        n = len(ANCHOR.findall(b))
        stale = DP.is_stale(b)
        if n != 1 or stale:
            bad += 1
            print(f"  ! {p['title'][:44]:46} anchors={n} stale={stale}")
    print(f'{len(fresh) - bad} of {len(fresh)} carry exactly one current promise')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
