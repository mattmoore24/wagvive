#!/usr/bin/env python3
"""Bring the THEME's delivery copy onto the current promise.

Three strings, two files, and between them they render on every page of the
store:

  templates/product.json  - the trust badge ("Ships in 1 to 3 business days")
                            and the Shipping & delivery accordion. These show
                            on ALL product pages, so they were the most-read
                            statement of the promise anywhere on the site.
  templates/index.json    - the homepage FAQ answer.

All three said "1 to 3 business days" for dispatch, which was measured at 4.9,
8.8 and 11 calendar days on the only three real orders, and "5 to 12" for
delivery against actual deliveries of ~10, ~13 and ~14 business days.

TWO TRAPS THIS HANDLES.

1. Theme JSON escapes forward slashes, so the stored text is `<\\/p>`, not
   `</p>`. Matching on `</p>` finds nothing and the script reports success
   having changed nothing. Replacements are done on the RAW asset text.

2. `.github/workflows/theme-copy-fix.yml` runs `fix_product_care_copy.py
   --apply` on pushes to main and rewrites these same JSON paths
   UNCONDITIONALLY, without comparing current content. That file must be
   updated in the same commit or CI silently restores the old promise.

    python config/fix_theme_delivery_copy.py           # show the plan
    python config/fix_theme_delivery_copy.py --apply
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

# Written with the escaped slash exactly as the theme stores it.
EDITS = {
 'templates/product.json': [
   ('<p>Ships in 1 to 3 business days<\\/p>',
    f'<p>Ships within {DP.DISPATCH_DAYS} business days<\\/p>'),
   ('<p>Dispatched in 1 to 3 business days. Typical US delivery is 5 to 12 '
    'business days after dispatch, with tracking emailed as soon as it ships. '
    'Free over $60, otherwise $5.95 flat.<\\/p>',
    f'<p>Dispatched within {DP.DISPATCH_DAYS} business days. Typical US '
    f'delivery is {DP.WINDOW} from the day you order, with tracking emailed '
    'when your parcel is handed to the carrier. Free over $60, otherwise '
    '$5.95 flat.<\\/p>'),
 ],
 'templates/index.json': [
   ('<p>Orders are processed in 1 to 3 business days, then typically arrive in '
    '5 to 12 business days within the US. Tracking is emailed the moment your '
    'parcel ships. We ship direct rather than paying for domestic warehousing, '
    'which keeps prices down, and we would rather say so plainly than surprise '
    'you at checkout.<\\/p>',
    f'<p>Orders are dispatched within {DP.DISPATCH_DAYS} business days, then '
    f'typically arrive {DP.WINDOW} from the day you order. Tracking is emailed '
    'when your parcel is handed to the carrier, and it can be quiet for the '
    'first week or so while your order is being packed. We ship direct from '
    'our overseas fulfilment partner rather than paying for domestic '
    'warehousing, which keeps prices down, and we would rather say so plainly '
    'than surprise you at checkout.<\\/p>'),
 ],
}


def api(path, method='GET', payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
            time.sleep(0.6)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def main():
    apply = '--apply' in sys.argv
    theme = next(t for t in api('themes.json')['themes'] if t['role'] == 'main')
    print(f"theme {theme['id']} {theme['name']}\n")

    plan = []
    for key, pairs in EDITS.items():
        val = api(f"themes/{theme['id']}/assets.json?asset[key]={key}")['asset']['value']
        new = val
        hits = 0
        for old, repl in pairs:
            if old in new:
                new = new.replace(old, repl)
                hits += 1
            elif repl in new:
                pass                      # already applied, not a failure
            else:
                print(f'  ! {key}: source string not found, copy changed under us')
                print(f'    {old[:90]}')
                return 1
        print(f'  {key:26} {hits} replacement(s)')
        if new != val:
            plan.append((key, new))

    if not plan:
        print('\nNothing to change.')
        return 0
    if not apply:
        print(f'\n{len(plan)} file(s) would change. Dry run, use --apply.')
        return 0

    for key, new in plan:
        api(f"themes/{theme['id']}/assets.json", 'PUT',
            {'asset': {'key': key, 'value': new}})
        print(f'  wrote {key}')

    print('\n--- verify (re-fetched) ---')
    bad = 0
    for key in EDITS:
        val = api(f"themes/{theme['id']}/assets.json?asset[key]={key}")['asset']['value']
        stale = DP.is_stale(val)
        print(f"  {key:26} {'clean' if not stale else 'STALE ' + str(stale)}")
        bad += bool(stale)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
