#!/usr/bin/env python3
"""Prove every kit variant contains exactly the component variants it should.

Counting components is not enough. A kit variant can hold the right NUMBER of
components and still hold the wrong ones: the wrong colour blanket, the wrong
robe size. That failure is invisible on the product page and only surfaces when
a customer opens the box, so it is checked by identity here, against
kit_colorways.py, for all 39 variants.

    python config/verify_kit_variants.py
"""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from kit_colorways import KITS, SIZE_MAP           # noqa: E402

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

Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes { id title
      variants(first: 60) {
        nodes { id title selectedOptions { name value }
          productVariantComponents(first: 12) {
            nodes { quantity productVariant {
              id title product { title }
              selectedOptions { name value } } } } } } }
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
    kits = gql(Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']
    by_title = {k['title']: k for k in kits}
    problems, checked = [], 0

    for kit_title, spec in KITS.items():
        kit = by_title.get(kit_title)
        print(f'\n=== {kit_title} ===')
        if not kit:
            problems.append(f'{kit_title}: missing')
            continue
        for v in kit['variants']['nodes']:
            picked = {o['name']: o['value'] for o in v['selectedOptions']}
            size = picked.get('Size')
            cw_name = picked.get(spec['option'])
            cw = spec['values'].get(cw_name)
            if cw is None:
                problems.append(f'{kit_title} {v["title"]}: unknown '
                                f'{spec["option"]}={cw_name!r}')
                print(f'  !! {v["title"]:22} unknown {spec["option"]}')
                continue

            got = {}
            for c in v['productVariantComponents']['nodes']:
                pv = c['productVariant']
                got[short(pv['product']['title'])] = (
                    {o['name']: o['value'] for o in pv['selectedOptions']},
                    c['quantity'])

            bad = []
            for comp_name, (opts, qty) in got.items():
                if qty != 1:
                    bad.append(f'{comp_name} qty={qty}')
                want_col = cw.get(comp_name)
                if want_col is not None:
                    axis = next((n for n in opts if n.lower() != 'size'), None)
                    if axis and opts[axis] != want_col:
                        bad.append(f'{comp_name} {axis}={opts[axis]!r} '
                                   f'want {want_col!r}')
                if size and comp_name in SIZE_MAP[size] and 'Size' in opts:
                    want_sz = SIZE_MAP[size][comp_name]
                    if opts['Size'] != want_sz:
                        bad.append(f'{comp_name} Size={opts["Size"]!r} '
                                   f'want {want_sz!r}')
            for comp_name in cw:
                if comp_name not in got:
                    bad.append(f'{comp_name} MISSING from the variant')

            checked += 1
            if bad:
                problems += [f'{kit_title} [{v["title"]}] {b}' for b in bad]
                print(f'  !! {v["title"]:22} {bad}')
            else:
                print(f'  OK {v["title"]:22} {len(got)} components exact')

    print('\n' + '=' * 66)
    if problems:
        print(f'{len(problems)} PROBLEM(S) across {checked} variants')
        for p in problems[:20]:
            print(f'  ! {p}')
        return 1
    print(f'all {checked} kit variants contain exactly the components the '
          f'design specifies')
    return 0


if __name__ == '__main__':
    sys.exit(main())
