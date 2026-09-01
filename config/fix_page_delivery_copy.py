#!/usr/bin/env python3
"""Update the delivery promise on the FAQ and Shipping & Returns pages.

Both are live customer-facing pages with NO generator in this repo:
`config/faq_copy.py` has zero importers (dead code) and
`config/pages/shipping-returns.json` is a stale seed that does not match what
is published. So these are edited against the Admin API directly, from the
live body, rather than regenerated.

Beyond the day counts, three statements here were factually wrong and are
corrected:

  * "a tracking link is emailed as soon as your parcel is dispatched" - CJ
    marks an order dispatched when it generates a LABEL, up to 11 days before
    the parcel is handed over. The link arrives early and then does not move.
  * "any time before it is dispatched, for a full refund" - same problem: a
    customer cancelling on day two would have been wrongly refused because
    Shopify already said "fulfilled".
  * "Once tracking is issued, treat it as a return" - tracking is issued at
    label generation, so this denied cancellation for the entire handling
    window.

"Refunds are issued... within 5 to 7 business days" is left alone. It is about
refund processing, not delivery, and it is accurate.

    python config/fix_page_delivery_copy.py           # show the plan
    python config/fix_page_delivery_copy.py --apply
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

TRACKING_TRUTH = (
    'Yes. A tracking link is emailed when your parcel is handed to the '
    'carrier. That is usually several days after you order, and the link can '
    'be quiet for the first week or so while your order is being packed, '
    'which is normal. If an\norder contains several items, they may ship '
    'separately with their own\ntracking.')

CANCEL_TRUTH = (
    'Yes, any time before your parcel is handed to the carrier, for a full '
    'refund. That is later than the point where your order is marked '
    'fulfilled, so it is worth asking even if you have had a confirmation '
    'email. Email')

EDITS = {
 'faq': (172458737953, [
   ("Processing takes 1 to 3 business days, then typically 5 to 12 business days\n"
    "to arrive in the US. You'll get tracking by email the moment it ships. Full\n"
    "detail on our",
    f"We dispatch within {DP.DISPATCH_DAYS} business days, and orders typically "
    f"arrive {DP.WINDOW}\nfrom the day you order. Tracking is emailed when your "
    "parcel is handed to\nthe carrier. Full\ndetail on our"),
   ('Yes, a tracking link is emailed as soon as your parcel is dispatched. If an\n'
    'order contains several items, they may ship separately with their own\n'
    'tracking.', TRACKING_TRUTH),
   ('Yes, any time before it is dispatched, for a full refund. Email', CANCEL_TRUTH),
 ]),
 'shipping-returns': (172458705185, [
   ('1 to 3 business days', f'within {DP.DISPATCH_DAYS} business days'),
   ('typically 5 to 12 business days after dispatch',
    f'{DP.WINDOW} from the day you order'),
   ('Orders can be cancelled for a full refund any time before dispatch. Once '
    'tracking is issued, treat it as a return.',
    'Orders can be cancelled for a full refund any time before your parcel is '
    'handed to the carrier. That is later than the point where your order is '
    'marked fulfilled, so it is worth asking even if you have already had a '
    'confirmation email. Once the parcel is genuinely on its way, treat it as '
    'a return.'),
 ]),
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
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:300]}')
    return {}


def main():
    apply = '--apply' in sys.argv
    plan = []
    for handle, (pid, pairs) in EDITS.items():
        body = api(f'pages/{pid}.json')['page']['body_html']
        new, hits, missing = body, 0, []
        for old, repl in pairs:
            if old in new:
                new = new.replace(old, repl)
                hits += 1
            elif repl in new:
                pass                       # already applied
            else:
                missing.append(old[:70])
        print(f'  {handle:20} {hits} replacement(s)'
              + (f'  MISSING {missing}' if missing else ''))
        if missing:
            print('    Source copy changed under us. Nothing written.')
            return 1
        if new != body:
            plan.append((handle, pid, new))

    if not plan:
        print('\nNothing to change.')
        return 0
    if not apply:
        print(f'\n{len(plan)} page(s) would change. Dry run, use --apply.')
        return 0

    for handle, pid, new in plan:
        api(f'pages/{pid}.json', 'PUT', {'page': {'id': pid, 'body_html': new}})
        print(f'  wrote {handle}')

    print('\n--- verify (re-fetched) ---')
    bad = 0
    for handle, (pid, _) in EDITS.items():
        body = api(f'pages/{pid}.json')['page']['body_html']
        stale = DP.is_stale(body)
        print(f"  {handle:20} {'clean' if not stale else 'STALE ' + str(stale)}")
        bad += bool(stale)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
