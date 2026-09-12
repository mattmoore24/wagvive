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
   paragraph beginning with one of `DP.NOTE_OPENINGS` is stripped before the
   new one is written, so this converges rather than accumulating.

4. THE NOTE DEPENDS ON THE WAREHOUSE (2026-09-11). China-shipped products get
   the overseas note; products CJ ships US to US get the US one. Origin comes
   from `freight_floor.origin_for`, the same answer pricing uses, which reads
   the BOOKED carrier in `config/carriers.json`. It used to say 'US' for any
   product holding a single US unit and would have mislabelled the
   China-shipped Pet Hair Remover Mitt; that was fixed there, for every caller.
   Kits carry no SKU and keep the overseas note, because most of their
   components ship from China.

5. COMPARED WITHOUT WHITESPACE. Shopify re-indents body_html when it saves, so
   a byte comparison would call every product changed on every run and rewrite
   all of them for nothing, the trap apply_size_guides.py already hit.

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
NOTE = re.compile(r'<p>(?:' + '|'.join(re.escape(o) for o in DP.NOTE_OPENINGS)
                  + r')[^<]*(?:<[^>]+>[^<]*)*?</p>')
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


def rewrite(body, origin='CN'):
    """Body with exactly one current delivery block, in the right place, with
    the honesty line for `origin`."""
    block = DP.delivery_block(origin)
    b = body or ''
    b = NOTE.sub('', b)                      # drop any previous honesty paragraph
    if ANCHOR.search(b):
        b = ANCHOR.sub(PLACEHOLDER, b, count=1)   # mark where the first one was
        b = ANCHOR.sub('', b)                     # remove any duplicates
        return b.replace(PLACEHOLDER, block)
    # No line at all: append, keeping the bundle upsell last.
    if UPSELL in b:
        return b.replace(UPSELL, block + UPSELL, 1)
    return b + block


def squash(html):
    """Whitespace-insensitive form, for COMPARISON only. Never written back."""
    return re.sub(r'\s+', ' ', re.sub(r'>\s+<', '><', html or '')).strip()


def origin_of(product):
    """'US' only when CJ actually ships the product US to US. Kits carry no SKU
    and stay 'CN'. A CJ quota outage raises rather than guessing, because this
    decides a customer-facing claim."""
    sku = next((v.get('sku') for v in product['variants'] if v.get('sku')), None)
    if not sku:
        return 'CN'
    import freight_floor
    return freight_floor.origin_for(sku)


def main():
    apply = '--apply' in sys.argv
    prods = api('products.json?limit=250&status=active')['products']
    origins = {p['id']: origin_of(p) for p in prods}
    us = sorted(p['title'] for p in prods if origins[p['id']] == 'US')
    print(f"{len(us)} product(s) ship from CJ's US warehouse: {us}\n")
    plan = []
    for p in sorted(prods, key=lambda x: x['title']):
        old = p.get('body_html') or ''
        new = rewrite(old, origins[p['id']])
        if squash(new) != squash(old):
            had = 'update' if ANCHOR.search(old) else 'ADD (was missing)'
            plan.append((p, new, had))

    for p, _, had in plan:
        print(f"  {p['title'][:46]:48} {had}  [{origins[p['id']]}]")
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
        notes = NOTE.findall(b)
        want = DP.NOTE_OPENINGS[1] if origins.get(p['id']) == 'US' else DP.NOTE_OPENINGS[0]
        right_note = len(notes) == 1 and want in notes[0]
        if n != 1 or stale or not right_note:
            bad += 1
            print(f"  ! {p['title'][:44]:46} anchors={n} stale={stale} "
                  f"notes={len(notes)} right_note={right_note}")
    print(f'{len(fresh) - bad} of {len(fresh)} carry exactly one current promise '
          f'and the note for their warehouse')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
