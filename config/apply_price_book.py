#!/usr/bin/env python3
"""Write config/price_book.json to the live store, then prove it landed.

The book is built by build_price_book.py from the demand-model optimiser and
is the source of truth for every single-product variant price. This script is
deliberately dumb: it makes the store match the book, nothing else. Bundles
are priced by apply_kits.py, not here.

Rules honoured:
  * 2 calls/sec REST limit: 0.55s between writes, exponential backoff on 429.
  * Never trust a write's return value: a full re-fetch at the end compares
    every variant against the book and the run FAILS if anything differs.
  * compare_at_price is left untouched (singles carry none; a permanent
    repricing is not a sale and must not manufacture one).

    python config/apply_price_book.py            # dry run: show the diff
    python config/apply_price_book.py --apply    # write + verify
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def api(method, path, payload=None, tries=5):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def fetch_variants():
    """sku -> (variant_id, live_price, product_id, product_title)."""
    out = {}
    prods = api('GET', 'products.json?limit=250&status=active'
                       '&fields=id,title,product_type,variants')['products']
    for p in prods:
        if p['product_type'] == 'Bundles & Kits':
            continue
        for v in p['variants']:
            if v.get('sku'):
                out[v['sku']] = (v['id'], float(v['price']),
                                 str(p['id']), p['title'])
    return out


def main():
    apply = '--apply' in sys.argv
    book = json.load(open(os.path.join(ROOT, 'config', 'price_book.json'),
                          encoding='utf-8'))
    want = {}                     # sku -> (book price, product title)
    for pid, entry in book.items():
        for sku, price in entry['variants'].items():
            want[sku] = (price, entry['title'])

    live = fetch_variants()
    missing = [s for s in want if s not in live]
    changes = [(s, live[s][0], live[s][1], want[s][0], want[s][1])
               for s in want if s in live
               and abs(live[s][1] - want[s][0]) >= 0.005]

    print(f'{len(want)} variants in book, {len(live)} on store, '
          f'{len(changes)} need a price change, {len(missing)} missing\n')
    for s in missing:
        print(f'  MISSING ON STORE  {s}  ({want[s][1]})')
    last = ''
    for s, vid, old, new, title in sorted(changes, key=lambda c: (c[4], c[3])):
        if title != last:
            print(title.encode('ascii', 'replace').decode())
            last = title
        print(f'   {s:22} ${old:>7.2f} -> ${new:>7.2f}')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0
    if missing:
        print('\nRefusing to apply while book SKUs are missing from the store.')
        return 1

    print(f'\nwriting {len(changes)} prices...')
    for i, (s, vid, old, new, title) in enumerate(changes, 1):
        api('PUT', f'variants/{vid}.json',
            {'variant': {'id': vid, 'price': f'{new:.2f}'}})
        time.sleep(0.55)
        if i % 25 == 0:
            print(f'  {i}/{len(changes)}')

    # verify against the live system, never the write's return value
    after = fetch_variants()
    bad = [(s, want[s][0], after[s][1]) for s in want
           if s in after and abs(after[s][1] - want[s][0]) >= 0.005]
    if bad:
        print(f'\nVERIFY FAILED: {len(bad)} variants do not match the book:')
        for s, w, a in bad:
            print(f'  {s}: book ${w:.2f}, live ${a:.2f}')
        return 1
    print(f'\nverified: all {len(want)} variants match the book.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
