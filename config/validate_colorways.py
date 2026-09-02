#!/usr/bin/env python3
"""Prove every value in kit_colorways.py resolves to a real, buyable variant.

This must pass before rebuild_kits.py is allowed to write. A colorway naming a
value the supplier does not stock produces a kit variant that maps to no SKU:
the storefront sells it, and fulfilment fails after the customer has paid. That
is the worst possible failure mode, so it is checked up front against the live
catalogue rather than trusted.

Checks, per kit and per (size, colorway) combination:
  * every component named in the colorway is actually in the kit's bundle
  * every component in the bundle that HAS choices is named in the colorway
  * the resulting option values resolve to exactly one live variant
  * that variant is available for sale

    python config/validate_colorways.py
"""
import json, os, sys, time, urllib.request

# Pass --composition-change when kit_colorways.py deliberately adds or drops a
# component. See the note beside its use below.
COMPOSITION_CHANGE = '--composition-change' in sys.argv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from kit_colorways import KITS, SIZE_MAP, COMPONENT_OPTIONS   # noqa: E402

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

KITS_Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes { id title
      bundleComponents(first: 12) { nodes { componentProduct { id title } } } }
  }
}'''

COMP_Q = '''
query($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Product { id title
      variants(first: 100) {
        nodes { id title availableForSale sku
                selectedOptions { name value } } } }
  }
}'''


def gql(q, v=None):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit(json.dumps(out['errors'])[:500])
    time.sleep(0.35)
    return out


def short(t):
    return t.replace('Wagvive ', '')


def main():
    kits = gql(KITS_Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']
    by_title = {k['title']: k for k in kits}

    ids = sorted({c['componentProduct']['id'] for k in kits
                  for c in k['bundleComponents']['nodes']})
    comps = {n['id']: n for n in gql(COMP_Q, {'ids': ids})['data']['nodes']}
    by_name = {short(c['title']): c for c in comps.values()}

    # A component being ADDED by a composition change is not yet in any bundle,
    # so it is absent from the ids above and every lookup would report
    # "not found". Pull any design-named product that is missing, so a new
    # component is resolved against the real catalogue like any other.
    wanted = {name for spec in KITS.values()
              for cw in spec['values'].values() for name in cw}
    if wanted - set(by_name):
        extra_q = '''query($q: String!) { products(first: 60, query: $q) {
          nodes { id title
            variants(first: 60) { nodes {
              id title sku availableForSale
              selectedOptions { name value } } } } } }'''
        found = gql(extra_q, {'q': 'status:ACTIVE'})['data']['products']['nodes']
        for p in found:
            by_name.setdefault(short(p['title']), p)
        still = wanted - set(by_name)
        if still:
            print(f'!! design names products not in the catalogue: {sorted(still)}')

    problems = []
    for kit_title, spec in KITS.items():
        kit = by_title.get(kit_title)
        print(f'\n=== {kit_title} ===')
        if not kit:
            problems.append(f'{kit_title}: not an active kit')
            print('  !! no such active kit')
            continue

        bundle = {short(c['componentProduct']['title'])
                  for c in kit['bundleComponents']['nodes']}
        # which bundle components actually offer a choice
        choosers = set()
        for name in bundle:
            c = by_name.get(name)
            if c and len(c['variants']['nodes']) > 1:
                choosers.add(name)

        named = set()
        for cw in spec['values'].values():
            named |= set(cw)
        extra = named - bundle
        missed = choosers - named
        # A DELIBERATE composition change makes the design differ from the live
        # bundle, which is not an error: it is the whole point of the edit, and
        # rebuild_kits.py is what closes the gap. Without this flag the
        # validator blocks the very rebuild that would fix it. With the flag,
        # the design's own component set is what gets resolved below, so the
        # values still have to be real.
        if COMPOSITION_CHANGE:
            if extra:
                print(f'  .. composition change pending rebuild, design adds: '
                      f'{sorted(extra)}')
            if missed:
                print(f'  .. composition change pending rebuild, design drops: '
                      f'{sorted(missed)}')
            bundle = (bundle - missed) | extra
        else:
            if extra:
                problems.append(f'{kit_title}: colorway names non-components {sorted(extra)}')
                print(f'  !! names components not in the bundle: {sorted(extra)}')
            if missed:
                problems.append(f'{kit_title}: components with choices not covered {sorted(missed)}')
                print(f'  !! has choices but no colorway entry: {sorted(missed)}')

        sizes = spec['sizes'] or [None]
        for size in sizes:
            for cw_name, cw in spec['values'].items():
                label = f'{size} / {cw_name}' if size else cw_name
                bad = []
                for comp_name in sorted(bundle):
                    c = by_name.get(comp_name)
                    if not c:
                        bad.append(f'{comp_name}: not found')
                        continue
                    variants = c['variants']['nodes']
                    if len(variants) == 1:
                        continue
                    want = {}
                    if comp_name in cw:
                        # the non-size axis: Color or Character
                        axis = next((o['name'] for o in variants[0]['selectedOptions']
                                     if o['name'].lower() != 'size'), None)
                        want[axis] = cw[comp_name]
                    if size and comp_name in SIZE_MAP[size]:
                        want['Size'] = SIZE_MAP[size][comp_name]
                    want.update(COMPONENT_OPTIONS.get(kit_title, {})
                                .get(comp_name, {}))
                    matches = [v for v in variants
                               if all(any(o['name'] == n and o['value'] == val
                                          for o in v['selectedOptions'])
                                      for n, val in want.items())]
                    if len(matches) != 1:
                        bad.append(f'{comp_name} {want} -> {len(matches)} matches')
                    elif not matches[0]['availableForSale']:
                        bad.append(f'{comp_name} {want} -> NOT available for sale')
                flag = 'OK ' if not bad else '!! '
                print(f'  {flag}{label}')
                for b in bad:
                    print(f'        {b}')
                    problems.append(f'{kit_title} [{label}] {b}')

    print('\n' + '=' * 66)
    if problems:
        print(f'{len(problems)} PROBLEM(S) - do NOT rebuild until these are fixed')
        return 1
    total = sum(len(s['sizes'] or [None]) * len(s['values']) for s in KITS.values())
    print(f'every value resolves to exactly one live, buyable variant '
          f'({total} kit variants)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
