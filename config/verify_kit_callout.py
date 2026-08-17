#!/usr/bin/env python3
"""Prove the multi-kit callout renders on the LIVE storefront.

`custom.kits` being populated and the snippet being uploaded are two separate
facts, and neither of them means the page shows anything: a Liquid error renders
as silence, not as an exception anyone sees. So this loads each component's real
product page and checks the rendered HTML.

For a component in one kit it expects the card and NO "also part of" line. For a
component in several it expects the card to name the kit with the biggest dollar
saving and the extra line to name every other one.

Storefront HTML is CDN cached, so each fetch carries a unique ?nocache= param and
every fact is read from the SAME response.
"""
import html as htmllib
import json, os, re, sys, time, urllib.error, urllib.request
from collections import defaultdict

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
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')

# Membership comes from the VARIANT level. product.bundleComponents is stale
# after a rebuild: on 2026-08-17 it kept naming the Watermelon Rope Frisbee and
# the Bouncy Egg Squeaker as components of kits they had already left, so this
# check passed while asserting the composition the store no longer sells.
Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes {
      id title
      variants(first: 30) { nodes {
        price compareAtPrice
        productVariantComponents(first: 12) {
          nodes { productVariant { product { id title handle } } } } } }
    }
  }
}'''


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    return out


def page(handle):
    url = f'https://{SHOP}/products/{handle}?nocache={int(time.time()*1000)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'replace')


def main():
    kits = gql(Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']

    saving = {}
    membership = defaultdict(list)
    handles, names = {}, {}
    for k in kits:
        v = k['variants']['nodes'][0]
        cap = float(v['compareAtPrice'] or 0)
        saving[k['id']] = round(cap - float(v['price']), 2)
        names[k['id']] = k['title']
        for var in k['variants']['nodes']:
            for c in var['productVariantComponents']['nodes']:
                cp = c['productVariant']['product']
                handles[cp['id']] = cp['handle']
                names[cp['id']] = cp['title'].replace('Wagvive ', '')
                if k['id'] not in membership[cp['id']]:
                    membership[cp['id']].append(k['id'])

    def check(cid, kids):
        """Fetch one page and grade it. Returns (errors, shown, more_txt)."""
        src = page(handles[cid])
        best = max(kids, key=lambda k: saving[k])
        others = [k for k in kids if k != best]

        eyebrow = re.search(r'wv-kit__eyebrow">([^<]+)<', src)
        shown = htmllib.unescape(eyebrow.group(1)).strip() if eyebrow else ''
        more = re.search(r'wv-kit__more">(.*?)</p>', src, re.S)
        more_txt = htmllib.unescape(re.sub(r'<[^>]+>', '', more.group(1))) if more else ''

        errs = []
        if not shown:
            errs.append('no callout card at all')
        elif names[best] not in shown:
            errs.append(f'card names "{shown}", expected the best saving '
                        f'({names[best]}, ${saving[best]:.2f})')
        for o in others:
            if names[o] not in more_txt:
                errs.append(f'does not mention {names[o]}')
        if not others and more_txt:
            errs.append(f'unexpected extra line: {more_txt.strip()}')
        return errs, shown, more_txt

    bad = []
    for cid, kids in sorted(membership.items(), key=lambda kv: names[kv[0]]):
        # Shopify's CDN serves mixed stale and fresh renders for minutes after a
        # theme write, and ?nocache= does not reliably defeat it: across two runs
        # the SAME pages passed and failed alternately. So a single miss proves
        # nothing. Retry before believing it, or this reports phantom breakage.
        for attempt in range(5):
            errs, shown, more_txt = check(cid, kids)
            if not errs:
                break
            if attempt < 4:
                time.sleep(3 * (attempt + 1))

        flag = 'OK ' if not errs else '!! '
        print(f'{flag}{names[cid]:28} {len(kids)} kit(s)  card="{shown}"'
              + (f'  more="{more_txt.strip()}"' if more_txt else '')
              + (f'  [{attempt + 1} fetches]' if attempt else ''))
        for e in errs:
            print(f'      ! {e}')
            bad.append(f'{names[cid]}: {e}')
        time.sleep(0.4)

    print('\n' + '=' * 64)
    if bad:
        print(f'{len(bad)} PROBLEM(S)')
        return 1
    multi = sum(1 for v in membership.values() if len(v) > 1)
    print(f'all {len(membership)} component pages render the callout correctly '
          f'({multi} of them naming more than one kit)')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
