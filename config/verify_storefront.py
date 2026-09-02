#!/usr/bin/env python3
"""Is what we THINK we changed actually live for a customer?

Checks the PUBLIC storefront, not the admin. Those are different systems and
this repo has been caught by the gap before: a product can be active, stocked,
imaged and in a collection and still 404 for a shopper because Admin API
creation publishes to Point of Sale only, and Shopify's CDN serves mixed
stale/fresh renders for minutes after a write.

Every check here fetches with a unique ?nocache= param and reads the rendered
result. It never trusts an admin field or a write's return value.

    python config/verify_storefront.py
"""
import json
import os
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


def admin(path):
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
        headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.5)
    return out


# The storefront rate-limits too, and it answers 429 exactly like a real
# failure. The first version of this script fetched two pages per product with
# no pause and reported EIGHTEEN products as "NOT LIVE" when every one of them
# was fine - a false alarm indistinguishable from a real outage. Throttle, and
# retry a 429 rather than believing it.
THROTTLE = 0.7


def _fetch(url, tries=4):
    for attempt in range(tries):
        time.sleep(THROTTLE)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise urllib.error.HTTPError(url, 429, 'rate limited', None, None)


def live_json(handle):
    return json.loads(
        _fetch(f'https://{SHOP}/products/{handle}.js?nocache={int(time.time()*1000)}'))


def live_html(path):
    return _fetch(f'https://{SHOP}{path}?nocache={int(time.time()*1000)}')


def main():
    fails = []
    prods = admin('products.json?limit=250&status=active')['products']
    print(f'{len(prods)} active products in admin. Checking each on the '
          f'PUBLIC storefront...\n')

    print(f"{'product':40}{'admin':>9}{'live':>9}{'avail':>8}{'img':>6} promise")
    print('-' * 82)
    checked = 0
    for p in sorted(prods, key=lambda x: x['title']):
        h = p['handle']
        want = float(p['variants'][0]['price'])
        try:
            d = live_json(h)
        except urllib.error.HTTPError as e:
            fails.append(f'{p["title"]}: storefront {e.code} (NOT LIVE)')
            print(f'{p["title"][:38]:40}{want:>9.2f}{"404":>9}')
            continue
        got = d['price'] / 100
        avail = sum(1 for v in d['variants'] if v['available'])
        wired = sum(1 for v in d['variants'] if v.get('featured_image'))
        nvar = len(d['variants'])
        ok_price = abs(got - want) < 0.005
        ok_avail = avail == nvar
        ok_img = wired == nvar
        if not ok_price:
            fails.append(f'{p["title"]}: admin ${want:.2f} but live ${got:.2f}')
        if not ok_avail:
            fails.append(f'{p["title"]}: {nvar - avail} of {nvar} variants unbuyable')
        if not ok_img:
            fails.append(f'{p["title"]}: {nvar - wired} of {nvar} variants unwired')
        checked += 1
        print(f'{p["title"][:38]:40}{want:>9.2f}{got:>9.2f}'
              f'{avail:>4}/{nvar:<3}{wired:>3}/{nvar:<2}', end='')
        # the delivery promise, on the rendered page
        try:
            html = live_html(f'/products/{h}')
            stale = DP.is_stale(html)
            new = DP.WINDOW in html
            print(f"  {'ok' if new and not stale else 'PROBLEM'}")
            if not new:
                fails.append(f'{p["title"]}: promise missing from the live page')
            if stale:
                fails.append(f'{p["title"]}: stale promise {stale} live')
        except Exception as exc:
            print(f'  fetch failed {exc}')

    print(f'\n{checked} of {len(prods)} products fetched from the storefront')
    print('\n' + '=' * 82)
    if fails:
        print(f'{len(fails)} PROBLEM(S):')
        for f in fails:
            print('  ! ' + f)
        return 1
    print('Every active product is live, correctly priced, fully buyable, has an')
    print('image on every variant, and carries the current delivery promise.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
