#!/usr/bin/env python3
"""Audit every kit for internal consistency, and optionally repair it.

WHY THIS EXISTS. The owner spotted that the Travel Kit's "What's inside the
kit" section listed products the kit does not contain. The cause: that section
is driven by a `wagvive.components` list.product_reference metafield, and
`apply_kits.py` rewrote the BUNDLE composition on 2026-08-04 without touching
the metafield. So the storefront kept advertising the pre-rebuild contents.

Nothing warns you about this. The bundle is correct, the cart is correct, the
fulfilment is correct, and the page lies. That is the worst kind of defect,
because every automated check that looks at the bundle passes.

There are FOUR independent descriptions of what is in a kit, and they can drift
apart one at a time:

  1. `bundleComponents`        the truth. What the customer is actually sold.
  2. `wagvive.components`      metafield driving the on-page contents section.
  3. the product images        cover grid plus one gallery shot per component.
  4. `bodyHtml`                the prose description naming each item.

Plus a fifth, pointing the other way:

  5. `custom.kits` on each component, listing every kit it belongs to. This is a
     LIST because six of the twenty two components are in two or three kits; the
     older single `custom.kit` reference could only name one and is kept only as
     a fallback for the storefront snippet.

This checks all five against the bundle and reports every divergence.

    python config/audit_kits.py            # report
    python config/audit_kits.py --apply    # repair metafields, then re-verify
"""
import json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'<[^>]+>')

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


KITS_Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes {
      id title handle bodyHtml
      variants(first: 100) { nodes { price compareAtPrice } }
      media(first: 30) { nodes { ... on MediaImage { alt } } }
      metafields(first: 25) { nodes { namespace key type value } }
      bundleComponents(first: 12) {
        nodes { componentProduct { id title status } } }
    }
  }
}'''

COMPONENT_LINK_Q = '''
query($q: String!) {
  products(first: 60, query: $q) {
    nodes { id title
      kit:  metafield(namespace: "custom", key: "kit")  { value }
      kits: metafield(namespace: "custom", key: "kits") { value } }
  }
}'''

SET_MF = '''
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) {
    metafields { key namespace }
    userErrors { field message }
  }
}'''


def short(t):
    return t.replace('Wagvive ', '')


def main():
    apply = '--apply' in sys.argv
    kits = gql(KITS_Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']
    prods = {n['id']: n for n in
             gql(COMPONENT_LINK_Q, {'q': 'status:ACTIVE'})['data']['products']['nodes']}

    problems, fixes = [], []

    for k in kits:
        title = k['title']
        comps = [c['componentProduct'] for c in k['bundleComponents']['nodes']]
        comp_ids = [c['id'] for c in comps]
        comp_names = [short(c['title']) for c in comps]
        print(f"\n=== {title} ===")
        print(f"  bundle ({len(comps)}): {comp_names}")

        # 1. the contents metafield
        mf = next((m for m in k['metafields']['nodes']
                   if m['namespace'] == 'wagvive' and m['key'] == 'components'),
                  None)
        if not mf:
            problems.append(f'{title}: NO wagvive.components metafield, so the '
                            f'"What\'s inside" section has nothing to render')
            print('  metafield: MISSING')
            fixes.append((k['id'], comp_ids, title))
        else:
            listed = json.loads(mf['value'])
            names = [short(prods[i]['title']) if i in prods else f'<{i}>'
                     for i in listed]
            if listed != comp_ids:
                extra = [n for i, n in zip(listed, names) if i not in comp_ids]
                miss = [n for i, n in zip(comp_ids, comp_names) if i not in listed]
                problems.append(
                    f'{title}: contents metafield does not match the bundle. '
                    f'Shows {extra or "nothing"} that is NOT in the kit; '
                    f'omits {miss or "nothing"}')
                print(f'  metafield ({len(listed)}): {names}')
                print(f'    !! NOT in kit : {extra}')
                print(f'    !! omitted    : {miss}')
                fixes.append((k['id'], comp_ids, title))
            else:
                print(f'  metafield: matches ({len(listed)})')

        # 2. images
        alts = [(m.get('alt') or '') for m in k['media']['nodes']]
        gallery = [short(a) for a in alts[1:]]
        img_missing = [n for n in comp_names if n not in gallery]
        img_extra = [a for a in gallery if a and a not in comp_names]
        if img_missing or img_extra:
            problems.append(f'{title}: gallery images off. missing '
                            f'{img_missing}, extra {img_extra}')
        print(f'  gallery: {len(gallery)} shots'
              + (f'  !! missing {img_missing}' if img_missing else '')
              + (f'  !! extra {img_extra}' if img_extra else ''))
        # The cover is a grid composed by make_kit_covers.py. It used to be a
        # fixed 2x2 taking the first four images, which silently dropped one
        # item from every five-component kit: the Travel Kit advertised four
        # pieces while selling five. That generator now lays out however many
        # there are, so this is no longer assumed to be broken.
        #
        # There is no way to count tiles inside a flattened JPEG, so the real
        # guard is the gallery check above. The cover is composed from the same
        # component list in the same run, so if the gallery is right the cover
        # was built from the right set. After changing the generator, eyeball
        # one five-item kit by hand.

        # 3. description names every component.
        # Match on significant words rather than any word over 4 characters:
        # "Lick Bowl with Ball" has no word longer than four, so the old test
        # flagged it as unnamed even though the description spells it out.
        body = TAG.sub(' ', k['bodyHtml'] or '').lower()
        stop = {'with', 'and', 'the', 'for', '&', 'a'}

        def named(name):
            words = [w.lower().strip('&,') for w in name.split()]
            words = [w for w in words if w and w not in stop]
            hits = sum(1 for w in words if w in body)
            return hits >= max(1, (len(words) + 1) // 2)   # at least half

        unnamed = [n for n in comp_names if not named(n)]
        if unnamed:
            problems.append(f'{title}: description does not name {unnamed}')
            print(f'  description: !! does not name {unnamed}')

        # 4. price consistency
        prices = {v['price'] for v in k['variants']['nodes']}
        cmps = {v['compareAtPrice'] for v in k['variants']['nodes']}
        if len(prices) > 1:
            problems.append(f'{title}: variants priced inconsistently {prices}')
        print(f'  price: {sorted(prices)}  compare_at: {sorted(c for c in cmps if c)}')

        # 5. reverse links.
        # Checked against `custom.kits` (a LIST), not the old single `custom.kit`.
        # Six components sit in two or three kits, so a single reference could
        # only ever name one of them and this check used to flag every correct
        # multi-kit component as wrong. What matters is that THIS kit appears in
        # the component's list; the component naming other kits as well is the
        # whole point. See config/link_kits_multi.py.
        wrong = []
        for c in comps:
            p = prods.get(c['id']) or {}
            mf = p.get('kits')
            listed = json.loads(mf['value']) if mf else []
            if not listed:
                wrong.append(f'{short(c["title"])}: no custom.kits list')
            elif k['id'] not in listed:
                named = [short(prods.get(i, {}).get('title', i)) for i in listed]
                wrong.append(f'{short(c["title"])}: lists {named}, not this kit')
        if wrong:
            problems.append(f'{title}: broken cross-links {wrong}')
            print(f'  cross-links: !! {wrong}')
        else:
            print(f'  cross-links: all {len(comps)} components list this kit')

    print('\n' + '=' * 64)
    if problems:
        print(f'{len(problems)} PROBLEM(S):')
        for p in problems:
            print(f'  ! {p}')
    else:
        print('No problems found.')

    if fixes and apply:
        print(f'\nrepairing {len(fixes)} contents metafield(s)...')
        payload = [{'ownerId': pid, 'namespace': 'wagvive', 'key': 'components',
                    'type': 'list.product_reference',
                    'value': json.dumps(ids)} for pid, ids, _ in fixes]
        r = gql(SET_MF, {'mf': payload})
        errs = r['data']['metafieldsSet']['userErrors']
        if errs:
            print('  FAILED:', json.dumps(errs)[:300])
            return 1
        for _, _, t in fixes:
            print(f'  set {t}')
        # re-read and confirm
        fresh = gql(KITS_Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
                    )['data']['products']['nodes']
        bad = 0
        for k in fresh:
            comp_ids = [c['componentProduct']['id']
                        for c in k['bundleComponents']['nodes']]
            mf = next((m for m in k['metafields']['nodes']
                       if m['namespace'] == 'wagvive'
                       and m['key'] == 'components'), None)
            ok = mf and json.loads(mf['value']) == comp_ids
            bad += not ok
            print(f"  {'OK ' if ok else 'BAD'} {k['title']}")
        return 1 if bad else 0
    elif fixes:
        print(f'\n{len(fixes)} metafield(s) need repair. Re-run with --apply.')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
