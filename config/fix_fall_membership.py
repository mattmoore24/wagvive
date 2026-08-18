#!/usr/bin/env python3
"""Take the two non-seasonal products out of the fall collection, and settle
the product_type drift that came in with the same batch.

WHY THEY WERE IN THERE. The fall lineup and the "viral products" work were two
separate briefs that ran in the same sittings, and both were built by scripts
that add EVERY product they create to the seasonal collection unconditionally
(`add_fall_lineup.py`, `add_fall_wave2.py`). The Automatic Ball Launcher and the
3-in-1 Steam Grooming Brush came from the viral brief. Neither carries a `fall`
or a `seasonal` tag, which is the tell: every genuine member of that collection
does.

This is not only a tidiness problem. The homepage "Dressed for fall" row is a
`product-list` bound to the `fall-halloween` collection with `max_products: 8`,
so two non-seasonal items were taking two of the eight slots away from the
costumes and jumpers that the row exists to sell, in the weeks those have to
sell in.

BOTH ALREADY HAVE A PROPER HOME, which is why this only removes:

  Automatic Ball Launcher     -> toys-play (smart collection, rule tag=toy)
  3-in-1 Steam Grooming Brush -> grooming (custom collection)

So this refuses to remove a product from fall unless it is already in another
collection. Dropping a product out of every collection would take it off the
navigation entirely while leaving it active and buyable, which is a worse bug
than the one being fixed and would be invisible from the admin.

THE product_type DRIFT. The catalogue types toys as `Toys & Play` 15 times and
`Toys` 4 times, and all four of the odd ones came in with the fall batch. The
Ball Launcher is one of them, so it cannot be "categorised properly" without
this. The other three are the same defect from the same scripts and are fixed
with it rather than left as the only inconsistent rows. Nothing reads
product_type except the kit filters, which match on `Bundles & Kits`, so this
is safe. Verified by grep before writing.

    python config/fix_fall_membership.py            # show the plan
    python config/fix_fall_membership.py --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

SEASONAL = 'fall-halloween'
# handle -> where it actually belongs, for the report
EVICT = {
    'wagvive-ball-launcher': 'Toys & Play (year round fetch toy, tag: toy)',
    'wagvive-steam-grooming-brush': 'Grooming (year round grooming tool)',
}
# The canonical spelling, used 15 times against 4 for the bare "Toys".
CANON_TYPE = {'Toys': 'Toys & Play'}


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


def collections_of(pid, customs, smarts):
    """Every collection the product is in, custom and smart.

    Smart collections have to be asked separately: they are rule based, so
    membership does not appear as a `collect` and a product can look homeless
    when it is not. The Ball Launcher is exactly that case, it reaches
    toys-play through its `toy` tag.
    """
    out = []
    for handle, cid in list(customs.items()) + list(smarts.items()):
        ids = {p['id'] for p in
               api(f'collections/{cid}/products.json?limit=250')['products']}
        if pid in ids:
            out.append(handle)
    return out


def main():
    apply = '--apply' in sys.argv

    customs = {c['handle']: c['id'] for c in
               api('custom_collections.json?limit=250')['custom_collections']}
    smarts = {c['handle']: c['id'] for c in
              (api('smart_collections.json?limit=250').get('smart_collections')
               or [])}
    if SEASONAL not in customs:
        print(f'{SEASONAL} collection not found')
        return 1
    seasonal_id = customs[SEASONAL]

    members = api(f'collections/{seasonal_id}/products.json?limit=250')['products']
    print(f'{SEASONAL} currently holds {len(members)} products\n')

    # ---- part 1: evictions
    plan, problems = [], []
    for handle, belongs in EVICT.items():
        hit = [p for p in members if p['handle'] == handle]
        if not hit:
            print(f'  {handle:34} already out of {SEASONAL}')
            continue
        p = hit[0]
        homes = [h for h in collections_of(p['id'], customs, smarts)
                 if h != SEASONAL]
        if not homes:
            print(f'  {p["title"]:34} REFUSING: removing it would leave the '
                  f'product in no collection at all')
            problems.append(handle)
            continue
        tags = [t.strip() for t in (p.get('tags') or '').split(',')]
        seasonal_tags = [t for t in tags if t in ('fall', 'seasonal',
                                                  'halloween', 'thanksgiving')]
        print(f'  {p["title"]}')
        print(f'      remove from : {SEASONAL}')
        print(f'      keeps       : {homes}')
        print(f'      belongs in  : {belongs}')
        print(f'      seasonal tags it carries: {seasonal_tags or "none"}')
        if seasonal_tags:
            print(f'      REFUSING: it carries {seasonal_tags}, so it may be '
                  f'seasonal after all. Check before removing.')
            problems.append(handle)
            continue
        plan.append(p)

    # ---- part 2: product_type drift
    allp = api('products.json?limit=250&status=active')['products']
    retype = [p for p in allp if p['product_type'] in CANON_TYPE]
    if retype:
        print(f'\nproduct_type drift, {len(retype)} product(s) use a spelling '
              f'the rest of the catalogue does not:')
        for p in retype:
            print(f'  {p["title"][:44]:46} '
                  f'{p["product_type"]!r} -> {CANON_TYPE[p["product_type"]]!r}')

    if problems:
        print(f'\n{len(problems)} product(s) blocked. Nothing written.')
        return 1
    if not plan and not retype:
        print('\nNothing to do.')
        return 0
    if not apply:
        print(f'\n{len(plan)} eviction(s), {len(retype)} retype(s). '
              f'Dry run, use --apply.')
        return 0

    for p in plan:
        collects = api(f'collects.json?product_id={p["id"]}&limit=250')['collects']
        gone = [c for c in collects if c['collection_id'] == seasonal_id]
        for c in gone:
            api(f'collects/{c["id"]}.json', 'DELETE')
        print(f'  removed {p["title"]} from {SEASONAL}')
    for p in retype:
        api(f'products/{p["id"]}.json', 'PUT',
            {'product': {'id': p['id'],
                         'product_type': CANON_TYPE[p['product_type']]}})
        print(f'  retyped {p["title"]}')

    # ---- verify against the live system
    print('\n--- verify ---')
    bad = 0
    fresh = api(f'collections/{seasonal_id}/products.json?limit=250')['products']
    print(f'{SEASONAL} now holds {len(fresh)} products')
    for p in plan:
        still = any(x['id'] == p['id'] for x in fresh)
        homes = collections_of(p['id'], customs, smarts)
        print(f'  {p["title"][:40]:42} in fall: {still}   now in: {homes}')
        if still or not homes:
            bad += 1
    left = [p for p in api('products.json?limit=250&status=active')['products']
            if p['product_type'] in CANON_TYPE]
    print(f'products still using a drifted product_type: {len(left)}')
    bad += bool(left)

    # The homepage row is a product-list bound to this collection, so the
    # eviction only counts if the storefront stops showing them there.
    print('\nstorefront:')
    for attempt in range(8):
        url = f'https://{SHOP}/collections/{SEASONAL}?nocache={int(time.time()*1000)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urllib.request.urlopen(req, timeout=90).read().decode('utf-8',
                                                                     'replace')
        showing = [p['title'] for p in plan if p['handle'] in page]
        if not showing:
            print(f'  collection page: neither product appears')
            break
        print(f'  attempt {attempt+1}: still showing {showing} (CDN)')
        time.sleep(15)
    else:
        print('  collection page STILL shows them')
        bad += 1

    # The homepage needs a STREAK, not one read. Shopify serves two different
    # cached renders of it concurrently and they alternate: a single clean
    # fetch here reported success while the very next fetch still carried both
    # products. Three consecutive clean reads is the bar.
    streak = 0
    for attempt in range(12):
        url = f'https://{SHOP}/?nocache={int(time.time()*1000)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        home = urllib.request.urlopen(req, timeout=90).read().decode('utf-8',
                                                                     'replace')
        on_home = [p['title'] for p in plan if p['handle'] in home]
        streak = streak + 1 if not on_home else 0
        print(f'  homepage attempt {attempt+1}: '
              f'{on_home or "clean"} (streak {streak})')
        if streak >= 3:
            break
        time.sleep(20)
    else:
        print('  homepage STILL shows an evicted product')
        bad += 1

    if bad:
        print(f'\n{bad} check(s) failed')
        return 1
    print('\nThe fall collection is seasonal products only.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
