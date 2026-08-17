#!/usr/bin/env python3
"""Let a component page name EVERY kit it belongs to, not just one.

`custom.kit` is a single product_reference, so a component that sits in more
than one kit could only advertise one of them. Six of the twenty two components
are in two or three:

    Paw Print Fleece Blanket   New Puppy, Travel, Calm & Comfort
    Cooling Comfort Pad        Travel, Calm & Comfort
    Paw Washing Cup            Grooming, Travel
    Quick-Dry Bath Robe        Grooming, Travel
    Finger Toothbrush          New Puppy, Grooming
    Sneaker Chew Buddy         New Puppy, Toy

So the Cooling Pad page said "Also in the Travel Kit" and stayed silent about
Calm & Comfort, the highest-contribution kit in the range at $43.06. That is a
missed cross-sell on exactly the pages where a shopper is already interested.

This adds `custom.kits` (list.product_reference), fills it from actual bundle
membership, and leaves the old single `custom.kit` in place so the existing
snippet keeps working until the template switches over.

Membership is read from the LIVE bundles, never from a hand-kept list, because
the whole reason the contents metafield went stale is that it was maintained
separately from the bundle. Re-run this after any kit composition change.

    python config/link_kits_multi.py            # report
    python config/link_kits_multi.py --apply    # create definition + populate
"""
import json, os, sys, time, urllib.error, urllib.request
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


def gql(query, variables=None, tries=5):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    for attempt in range(tries):
        req = urllib.request.Request(
            f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
            method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                    'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read().decode())
            if out.get('errors'):
                raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
            return out
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


# Membership is read at the VARIANT level, never from product.bundleComponents.
# That product-level field is STALE after a kit rebuild: following the 2026-08-17
# composition change it still named the Watermelon Rope Frisbee and the Bouncy
# Egg Squeaker as components long after productVariantComponents had switched to
# their replacements. Trusting it here would have written "Also in the Toy Kit"
# onto a product no longer in the Toy Kit, and left the real component with no
# callout at all.
KITS_Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes { id title
      variants(first: 30) { nodes {
        productVariantComponents(first: 12) {
          nodes { productVariant { product { id title } } } } } } }
  }
}'''

DEF_CREATE = '''
mutation($d: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $d) {
    createdDefinition { id name }
    userErrors { field message code }
  }
}'''

SET_MF = '''
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) {
    metafields { key }
    userErrors { field message }
  }
}'''

READ_BACK = '''
query($q: String!) {
  products(first: 60, query: $q) {
    nodes { id title
      metafield(namespace: "custom", key: "kits") { value } }
  }
}'''

# Dropping out of a kit has to remove the callout, not just stop refreshing it.
# When the Watermelon Rope Frisbee left the Toy Kit its custom.kits metafield
# survived, so its page kept advertising "Also in the Toy Kit" for a kit that no
# longer contained it. The value is DELETED rather than set to an empty list,
# because the snippet renders on presence.
CLEAR_MF = '''
mutation($mf: [MetafieldIdentifierInput!]!) {
  metafieldsDelete(metafields: $mf) {
    deletedMetafields { key }
    userErrors { field message }
  }
}'''


def main():
    apply = '--apply' in sys.argv
    kits = gql(KITS_Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']

    membership = defaultdict(list)     # component id -> [kit ids]
    names = {}
    for k in kits:
        names[k['id']] = k['title']
        for v in k['variants']['nodes']:
            for c in v['productVariantComponents']['nodes']:
                cp = c['productVariant']['product']
                names[cp['id']] = cp['title'].replace('Wagvive ', '')
                if k['id'] not in membership[cp['id']]:
                    membership[cp['id']].append(k['id'])

    multi = {c: ks for c, ks in membership.items() if len(ks) > 1}
    print(f'{len(kits)} kits, {len(membership)} components, '
          f'{len(multi)} in more than one kit\n')
    for cid, kids in sorted(multi.items(), key=lambda kv: names[kv[0]]):
        print(f'  {names[cid]:30} {[names[k] for k in kids]}')

    if not apply:
        print('\nDry run. Use --apply to create custom.kits and populate it.')
        return 0

    print('\ncreating the custom.kits definition...')
    r = gql(DEF_CREATE, {'d': {
        'name': 'Kits', 'namespace': 'custom', 'key': 'kits',
        'description': 'Every kit this product belongs to. Generated from the '
                       'live bundles by config/link_kits_multi.py.',
        'type': 'list.product_reference', 'ownerType': 'PRODUCT'}})
    errs = r['data']['metafieldDefinitionCreate']['userErrors']
    if errs and not any(e.get('code') == 'TAKEN' for e in errs):
        print('  FAILED:', json.dumps(errs)[:250])
        return 1
    print('  ok' if not errs else '  already exists')

    stale = [n for n in gql(READ_BACK, {'q': 'status:ACTIVE'}
                            )['data']['products']['nodes']
             if n.get('metafield') and n['id'] not in membership]
    if stale:
        print(f'clearing custom.kits from {len(stale)} product(s) no longer in '
              f'any kit:')
        for n in stale:
            print(f"  - {n['title'].replace('Wagvive ', '')}")
        r = gql(CLEAR_MF, {'mf': [{'ownerId': n['id'], 'namespace': 'custom',
                                   'key': 'kits'} for n in stale]})
        e = r['data']['metafieldsDelete']['userErrors']
        if e:
            print('  FAILED:', json.dumps(e)[:250])
            return 1

    payload = [{'ownerId': cid, 'namespace': 'custom', 'key': 'kits',
                'type': 'list.product_reference', 'value': json.dumps(kids)}
               for cid, kids in membership.items()]
    print(f'writing {len(payload)} component(s)...')
    for i in range(0, len(payload), 25):
        r = gql(SET_MF, {'mf': payload[i:i + 25]})
        e = r['data']['metafieldsSet']['userErrors']
        if e:
            print('  FAILED:', json.dumps(e)[:250])
            return 1
        time.sleep(0.4)

    # verify against the live system rather than the mutation's return value
    fresh = {n['id']: n for n in
             gql(READ_BACK, {'q': 'status:ACTIVE'})['data']['products']['nodes']}
    bad = []
    for cid, kids in membership.items():
        mf = (fresh.get(cid) or {}).get('metafield')
        got = json.loads(mf['value']) if mf else []
        if sorted(got) != sorted(kids):
            bad.append(names[cid])
    # A leftover callout is as wrong as a missing one, so the clear is verified
    # too rather than trusted from the mutation's return value.
    for n in stale:
        if (fresh.get(n['id']) or {}).get('metafield'):
            bad.append(f"{n['title']} (stale callout survived)")
    if bad:
        print(f'\nVERIFY FAILED on {len(bad)}: {bad}')
        return 1
    print(f'verified: all {len(membership)} components list every kit they '
          f'belong to, and {len(stale)} ex-component(s) list none')
    return 0


if __name__ == '__main__':
    sys.exit(main())
