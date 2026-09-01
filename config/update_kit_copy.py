#!/usr/bin/env python3
"""Bring the two changed kits' copy in line with what is actually in the box.

The Toy Kit lost the Watermelon Rope Frisbee and the Dog Enrichment Kit lost the
Bouncy Egg Squeaker. NOTE the stated reason at the time ("CJ cannot ship them")
was later disproved: both are healthy at CJ and back on sale as standalone
products. The swap itself was kept because the replacements are good products,
the kits are live and verified on them, and churning back would be pure cost.
Copy, SEO description and the `wagvive.components` reference list all named the
removed item.

TWO TRAPS THIS SCRIPT EXISTS TO AVOID:

1. `product.bundleComponents` IS STALE after a rebuild. Immediately after
   rebuild_kits.py it still reported the Watermelon Rope Frisbee and the Bouncy
   Egg Squeaker as components, while the variant-level
   `variant.productVariantComponents` correctly reported their replacements.
   Anything deriving component identity from the product-level field writes the
   OLD composition back. This script reads the variant level only.

2. The Toy Kit's line "Cheaper than picking any four separately" is FALSE at the
   new price and was already false at the old one. The four cheapest components
   now total $49.96 against a $50.00 kit, so the kit is 4 cents MORE. It is
   replaced with the claim that is true and bigger anyway: all five separately
   cost $62.95, so the kit saves $12.95.

Run with no flags for a diff. --apply writes.
"""
# DELIVERY PROMISE LITERAL. The canonical text lives in
# config/delivery_promise.py; the literal below is a copy because it sits
# inside plain triple-quoted HTML. If they diverge, config/audit_claims.py
# fails against the LIVE store and config/apply_delivery_promise.py repairs
# every product body in one pass.
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

BODY = {
    'toy-kit': """<p><strong>Five toys, five different games.</strong></p>
<p>Dogs get bored of a toy, not of playing. This is a spread rather than five
versions of the same thing, so there is always one that suits the mood.</p>
<ul>
<li>
<strong>Barnyard squeaker</strong> - soft plush, for carrying and squeaking</li>
<li>
<strong>Woodland rope-limb plush</strong> - rope arms and legs to tug and
shake, so one toy covers two games</li>
<li>
<strong>Sneaker chew buddy</strong> - for chewing that spares your own shoes</li>
<li>
<strong>Jingle plush ball</strong> - rattles when it rolls, for the dogs who
answer to sound</li>
<li>
<strong>Corduroy squeak pals</strong> - light enough for small dogs to carry
around all day</li>
</ul>
<p>The five cost $62.95 bought separately. Together they are $50.00, and they
arrive in one parcel.</p>
<p><strong>Arrives in 10 to 16 business days.</strong></p>""",

    'dog-enrichment-kit': """<p><strong>A busy dog is a calm dog.</strong></p>
<p>Four tools that turn meals and quiet time into work a dog actually enjoys:
eating slower, licking to settle, learning to ask instead of barking, and
something to chew on when they want a job of their own.</p>
<ul>
<li>
<strong>Talk button</strong> - record a word and let them learn to press it.
Most dogs surprise their owners inside a week</li>
<li>
<strong>Lick bowl with ball</strong> - spread something tasty on it and
licking does what licking is for, calming them down</li>
<li>
<strong>Slow feeder bowl</strong> - dinner becomes a ten minute puzzle
instead of a thirty second inhale</li>
<li>
<strong>Dental chew stick</strong> - something to work at alone, and it
cleans their teeth while they do it</li>
</ul>
<p>The four cost $62.96 bought separately. Together they are $50.00, and they
arrive in one parcel.</p>
<p><strong>Arrives in 10 to 16 business days.</strong></p>""",
}

META_DESC = {
    'toy-kit': ('Five toys and five different games: a barnyard squeaker, a '
                'rope-limb plush, a sneaker chew, a jingle ball and a corduroy '
                'pal. Save $12.95 on the five.'),
    'dog-enrichment-kit': ('Four tools that turn meals and quiet time into work '
                           'a dog enjoys: a talking button, a lick bowl, a slow '
                           'feeder maze bowl and a dental chew stick.'),
}

COMPONENTS_Q = '''
query($h: String!) {
  productByHandle(handle: $h) {
    id title
    variants(first: 30) { nodes {
      productVariantComponents(first: 12) { nodes {
        productVariant { product { id title } } } } } }
  }
}'''


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    time.sleep(0.4)
    return out


def rest(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data,
        method=method, headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:400]}')
    time.sleep(0.55)
    return out


def live_components(handle):
    """Component product ids, from the VARIANT level. See trap 1 in the docstring."""
    p = gql(COMPONENTS_Q, {'h': handle})['data']['productByHandle']
    seen, ids = set(), []
    for v in p['variants']['nodes']:
        for c in v['productVariantComponents']['nodes']:
            prod = c['productVariant']['product']
            if prod['id'] not in seen:
                seen.add(prod['id'])
                ids.append((prod['id'], prod['title']))
    return p, ids


def main():
    apply = '--apply' in sys.argv
    changed = 0

    for handle in ['toy-kit', 'dog-enrichment-kit']:
        prod, comps = live_components(handle)
        pid = prod['id'].rsplit('/', 1)[-1]
        current = rest(f'products/{pid}.json')['product']
        print('=' * 70)
        print(f"{prod['title']}  ({handle})")
        print('=' * 70)

        print('  components now in the box (variant level):')
        for _, title in comps:
            print(f"    - {title.replace('Wagvive ', '')}")

        want_body = BODY[handle]
        if current['body_html'].strip() != want_body.strip():
            changed += 1
            print('  BODY changes:')
            old = set(current['body_html'].split('\n'))
            for ln in want_body.split('\n'):
                if ln not in old and ln.strip():
                    print(f'    + {ln.strip()[:100]}')
            for ln in current['body_html'].split('\n'):
                if ln not in set(want_body.split('\n')) and ln.strip():
                    print(f'    - {ln.strip()[:100]}')
            if apply:
                rest(f'products/{pid}.json', 'PUT',
                     {'product': {'id': int(pid), 'body_html': want_body}})
                print('    written')
        else:
            print('  body already correct')

        mfs = rest(f'products/{pid}/metafields.json')['metafields']
        by_key = {f"{m['namespace']}.{m['key']}": m for m in mfs}

        desc = by_key.get('global.description_tag')
        if desc and desc['value'] != META_DESC[handle]:
            changed += 1
            print(f"  META description:\n    - {desc['value']}\n"
                  f"    + {META_DESC[handle]}")
            if apply:
                rest(f"metafields/{desc['id']}.json", 'PUT',
                     {'metafield': {'id': desc['id'],
                                    'value': META_DESC[handle],
                                    'type': 'string'}})
                print('    written')
        else:
            print('  meta description already correct')

        ref = by_key.get('wagvive.components')
        want_ids = [cid for cid, _ in comps]
        if ref and json.loads(ref['value']) != want_ids:
            changed += 1
            have = json.loads(ref['value'])
            print(f'  wagvive.components: {len(have)} -> {len(want_ids)} refs')
            for gid in have:
                if gid not in want_ids:
                    print(f'    - {gid}')
            for gid in want_ids:
                if gid not in have:
                    print(f'    + {gid}')
            if apply:
                rest(f"metafields/{ref['id']}.json", 'PUT',
                     {'metafield': {'id': ref['id'],
                                    'value': json.dumps(want_ids),
                                    'type': 'list.product_reference'}})
                print('    written')
        else:
            print('  wagvive.components already correct')
        print()

    if not apply:
        print(f'{changed} change(s) pending. Use --apply to write.')
        return 0
    print(f'{changed} change(s) written. Verify by re-fetching.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
