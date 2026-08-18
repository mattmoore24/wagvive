#!/usr/bin/env python3
"""Retire colourways CJ does not photograph, so we never depict the wrong thing.

The Jack-o-Lantern Sweater (CJGD1809813) sells FOUR colourways. CJ publishes
nine photos and only two of them are covered: Orange Stripe and Orange Pumpkin.
"Black Embroidered" and "Black Jacquard" have no reference image anywhere, so
there is nothing to shoot house art from and nothing honest to show. Left alone
they fall back to the product's lead image, meaning a customer who picks Black
Jacquard is looking at an orange striped sweater.

That is the exact failure the image gate exists to catch. It is what flagged
CJYD1861730, listed as "Halloween Pumpkin Vest For Dogs", which is really a CAT
head hood. Selling something we cannot depict is the same defect wearing a
different hat.

Owner approved the removal on 2026-08-18. Ten variants go, ten remain.

This DELETES variants. It refuses to run if a target colourway turns out to have
art on disk after all, and it re-reads the product afterwards rather than
trusting the deletes.

    python config/drop_unphotographed_colorways.py            # show the plan
    python config/drop_unphotographed_colorways.py --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'config', 'branding', 'fall')

# handle -> option1 values to retire
DROP = {
    'wagvive-jack-o-lantern-sweater': ['Black Embroidered', 'Black Jacquard'],
}

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


def api(method, path, payload=None, tries=6):
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


def by_handle(handle):
    for st in ('active', 'draft', 'archived'):
        ps = api('GET', f'products.json?handle={handle}&limit=1&status={st}'
                 ).get('products') or []
        if ps:
            return ps[0]
    return None


def main():
    apply = '--apply' in sys.argv
    problems = []

    for handle, looks in DROP.items():
        p = by_handle(handle)
        if not p:
            print(f'{handle}: not found')
            problems.append(handle)
            continue

        # Safety: if art exists for a colourway we are about to retire, someone
        # shot it since this was written and the right move is to wire it, not
        # delete it.
        for look in looks:
            f = os.path.join(ART, f'{handle}__{look}.jpg')
            if os.path.exists(f):
                print(f'REFUSING: art now exists for {look} ({f}). '
                      f'Wire it with apply_fall_art.py instead.')
                return 1

        targets = [v for v in p['variants'] if v.get('option1') in looks]
        keep = [v for v in p['variants'] if v.get('option1') not in looks]
        print(f"\n{p['title']}")
        print(f"  {len(p['variants'])} variants now -> {len(keep)} after")
        print(f"  retiring {len(targets)}:")
        for v in targets:
            print(f"    {v.get('option1'):18} / {v.get('option2'):4} {v['sku']}")
        if not keep:
            print('  REFUSING: that would remove every variant')
            return 1
        if not apply:
            continue

        for v in targets:
            api('DELETE', f"variants/{v['id']}.json")
        print(f'  deleted {len(targets)}')

    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    print('\n--- verify against the live product ---')
    for handle, looks in DROP.items():
        p = by_handle(handle)
        if not p:
            continue
        left = sorted({v.get('option1') for v in p['variants']})
        stragglers = [v['title'] for v in p['variants'] if v.get('option1') in looks]
        unwired = [v['title'] for v in p['variants'] if not v.get('image_id')]
        print(f"{p['title']}: {len(p['variants'])} variants, colourways {left}")
        print(f"  retired colourways still present: {stragglers or 'none'}")
        print(f"  variants with no image: {unwired or 'none'}")
        if stragglers or unwired:
            problems.append(handle)

    print('\n--- storefront ---')
    for handle in DROP:
        url = f'https://{SHOP}/products/{handle}.js?nocache={int(time.time()*1000)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            buy = sum(1 for v in d['variants'] if v['available'])
            print(f"  {d['title']}: {buy}/{len(d['variants'])} buyable")
        except Exception as e:
            print(f'  {handle}: {e}')

    if problems:
        print(f'\n{len(set(problems))} product(s) need attention')
        return 1
    print('\nEvery remaining colourway has its own photograph.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
