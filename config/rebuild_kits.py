#!/usr/bin/env python3
"""Rebuild every kit onto the Size + Colorway scheme in kit_colorways.py.

WHY NOT productBundleUpdate. The existing apply_kits.py derives each parent
option FROM a component's option, so a parent option can only ever carry one
component's own values. A shared "Colorway" that means Blue sneaker AND Beige
blanket AND Blue dispenser cannot be expressed that way, because those are three
different value vocabularies. So the options and variants are declared directly
with productSet, and each parent variant's components are then attached by hand
with productVariantRelationshipBulkUpdate. That mutation takes an explicit list
of component VARIANT ids per parent variant, which is exactly the control this
design needs.

ORDER OF OPERATIONS MATTERS. productSet replaces the variant set, which destroys
the old variants and with them their component relationships. Between that write
and the relationship write, the kit has variants that contain nothing. So each
kit is taken through the whole sequence before the next one starts, and the
relationship write is verified per variant. If the run dies midway, at most one
kit is in that state and the printed output says which.

Run config/validate_colorways.py first. This refuses to start otherwise: every
colour and size string must be known to resolve to a live buyable variant, or
the store ends up selling a kit that cannot be fulfilled.

    python config/rebuild_kits.py            # plan only
    python config/rebuild_kits.py --apply
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from kit_colorways import KITS, SIZE_MAP           # noqa: E402

BACKUP = os.path.join(ROOT, 'config', 'kit-backup')

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


def gql(q, v=None, tries=6):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    for a in range(tries):
        req = urllib.request.Request(
            f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
            method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                    'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                out = json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise
        if out.get('errors'):
            msg = json.dumps(out['errors'])
            if 'THROTTLED' in msg and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit('GraphQL: ' + msg[:600])
        time.sleep(0.4)
        return out
    return {}


KIT_Q = '''
query($q: String!) {
  products(first: 20, query: $q) {
    nodes { id title handle status
      options { name optionValues { name } }
      variants(first: 5) { nodes { price compareAtPrice taxable } }
      bundleComponents(first: 12) { nodes { componentProduct { id title } } } }
  }
}'''

COMP_Q = '''
query($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Product { id title
      variants(first: 100) {
        nodes { id title sku selectedOptions { name value } } } }
  }
}'''

SET = '''
mutation($input: ProductSetInput!) {
  productSet(input: $input, synchronous: true) {
    product { id
      options { name optionValues { name } }
      variants(first: 60) { nodes { id title selectedOptions { name value } } } }
    userErrors { field message code }
  }
}'''

REL = '''
mutation($input: [ProductVariantRelationshipUpdateInput!]!) {
  productVariantRelationshipBulkUpdate(input: $input) {
    parentProductVariants { id
      productVariantComponents(first: 12) {
        nodes { quantity productVariant { id title product { title } } } } }
    userErrors { code field message }
  }
}'''

REPRICE = '''
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id price compareAtPrice }
    userErrors { field message }
  }
}'''

VERIFY_Q = '''
query($id: ID!) {
  product(id: $id) {
    title status
    options { name optionValues { name } }
    variants(first: 60) {
      nodes { id title price compareAtPrice
        productVariantComponents(first: 12) {
          nodes { productVariant { id title product { id title } } } } }
    }
  }
}'''


def short(t):
    return t.replace('Wagvive ', '')


def build_plan(kit, spec, bundle_names, by_name):
    """[(variant option values, [component variant ids], label)] for one kit."""
    sizes = spec['sizes'] or [None]
    rows = []
    for size in sizes:
        for cw_name, cw in spec['values'].items():
            comp_ids, detail = [], []
            for comp_name in bundle_names:
                c = by_name[comp_name]
                variants = c['variants']['nodes']
                if len(variants) == 1:
                    comp_ids.append(variants[0]['id'])
                    detail.append(f'{comp_name}=only')
                    continue
                want = {}
                if comp_name in cw:
                    axis = next((o['name'] for o in variants[0]['selectedOptions']
                                 if o['name'].lower() != 'size'), None)
                    want[axis] = cw[comp_name]
                if size and comp_name in SIZE_MAP[size]:
                    want['Size'] = SIZE_MAP[size][comp_name]
                match = [v for v in variants
                         if all(any(o['name'] == n and o['value'] == val
                                    for o in v['selectedOptions'])
                                for n, val in want.items())]
                if len(match) != 1:
                    raise SystemExit(f'{kit}: {comp_name} {want} -> '
                                     f'{len(match)} matches (run validate first)')
                comp_ids.append(match[0]['id'])
                detail.append(f'{comp_name}={match[0]["title"]}')
            opts = ([('Size', size), (spec['option'], cw_name)] if size
                    else [(spec['option'], cw_name)])
            rows.append((opts, comp_ids, detail))
    return rows


def reprice(product_gid, price, compare):
    """Force every variant of a kit to the flat kit price."""
    cur = gql(VERIFY_Q, {'id': product_gid})['data']['product']
    want = [{'id': v['id'], 'price': price, 'compareAtPrice': compare}
            for v in cur['variants']['nodes']
            if v['price'] != price or v['compareAtPrice'] != compare]
    if not want:
        return 0
    for i in range(0, len(want), 25):
        r = gql(REPRICE, {'productId': product_gid, 'variants': want[i:i + 25]}
                )['data']['productVariantsBulkUpdate']
        if r['userErrors']:
            print(f'  !! reprice: {json.dumps(r["userErrors"])[:300]}')
    print(f'  repriced {len(want)} variant(s) to {price} / {compare}')
    return len(want)


def main():
    apply = '--apply' in sys.argv
    reprice_only = '--reprice-only' in sys.argv
    os.makedirs(BACKUP, exist_ok=True)

    kits = gql(KIT_Q, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
               )['data']['products']['nodes']
    by_title = {k['title']: k for k in kits}
    ids = sorted({c['componentProduct']['id'] for k in kits
                  for c in k['bundleComponents']['nodes']})
    comps = {n['id']: n for n in gql(COMP_Q, {'ids': ids})['data']['nodes']}
    by_name = {short(c['title']): c for c in comps.values()}

    # kit_colorways.py is the SOURCE OF TRUTH, including for WHICH components a
    # kit contains. A component being added by a composition change is not yet
    # in any bundle, so it is missing from the ids above; pull it from the
    # catalogue or the rebuild would silently keep planning the old component.
    wanted = {name for spec in KITS.values()
              for cw in spec['values'].values() for name in cw}
    if wanted - set(by_name):
        extra = gql('''query { products(first: 60, query: "status:ACTIVE") {
            nodes { id title
              variants(first: 60) { nodes { id title sku availableForSale
                selectedOptions { name value } } } } } }''')
        for p in extra['data']['products']['nodes']:
            by_name.setdefault(short(p['title']), p)

    failures = []
    for kit_title, spec in KITS.items():
        kit = by_title.get(kit_title)
        if not kit:
            print(f'!! {kit_title}: not an active kit, skipped')
            failures.append(kit_title)
            continue
        # Component set comes from the DESIGN, not the live bundle. Reading it
        # from live meant a composition change could never be applied: the Toy
        # Kit kept planning the Watermelon Rope Frisbee and the Enrichment Kit
        # died on the Bouncy Egg Squeaker, both of which CJ cannot ship.
        # Single-variant components carry no colorway entry, so union the design
        # names with any live component the design does not mention by choice.
        design_names = []
        for cw in spec['values'].values():
            for name in cw:
                if name not in design_names:
                    design_names.append(name)
        # Single-variant components carry no colorway entry, so they are declared
        # explicitly in `fixed`. Inferring them from the live bundle instead made
        # a single-variant component impossible to REMOVE, which is exactly the
        # state the Watermelon Rope Frisbee was stuck in.
        for name in spec.get('fixed', []):
            if name not in design_names:
                design_names.append(name)
        bundle_names = design_names
        # Intended price comes from the DESIGN. It cannot be read back from the
        # live product, because after a rebuild that is whatever Shopify derived
        # from the components. It can no longer be read from the backup either:
        # a composition change makes the previous kit's price simply wrong, and
        # the backup is by definition the kit as it was BEFORE the change, so the
        # Toy Kit would have been rebuilt at the frisbee-era $49.00.
        price = spec['price']
        compare = spec['compare_at']
        rows = build_plan(kit_title, spec, bundle_names, by_name)

        old_opts = [o['name'] for o in kit['options']]
        print(f'\n=== {kit_title} ===')
        print(f'  options {old_opts} -> '
              f'{["Size", spec["option"]] if spec["sizes"] else [spec["option"]]}')
        print(f'  variants {len(kit["variants"]["nodes"])}+ -> {len(rows)}   '
              f'price {price} / compare {compare}')
        for opts, cids, detail in rows[:2]:
            print(f'    {" / ".join(v for _, v in opts):22} {detail}')
        if len(rows) > 2:
            print(f'    ... {len(rows) - 2} more')

        if not apply and not reprice_only:
            continue

        if reprice_only:
            # Structure is already correct; only the derived prices need
            # overriding. Deliberately skips productSet, which would destroy and
            # recreate every variant and with it every component relationship.
            reprice(kit['id'], price, compare)
            fresh = gql(VERIFY_Q, {'id': kit['id']})['data']['product']
            ok = all(v['price'] == price and v['compareAtPrice'] == compare
                     for v in fresh['variants']['nodes'])
            print(f'  {"OK " if ok else "BAD"} all {len(fresh["variants"]["nodes"])} '
                  f'variants at {price} / {compare}')
            if not ok:
                failures.append(kit_title)
            continue

        with open(os.path.join(BACKUP, f'{kit["handle"]}.json'), 'w',
                  encoding='utf-8') as fh:
            json.dump(gql(VERIFY_Q, {'id': kit['id']})['data']['product'], fh,
                      indent=2)

        # 1. options + variants
        option_names = ([('Size', spec['sizes'])] if spec['sizes'] else []) + \
                       [(spec['option'], list(spec['values']))]
        payload = {
            'id': kit['id'],
            'productOptions': [{'name': n, 'position': i + 1,
                                'values': [{'name': v} for v in vals]}
                               for i, (n, vals) in enumerate(option_names)],
            'variants': [{
                'optionValues': [{'optionName': n, 'name': v} for n, v in opts],
                'price': price, 'compareAtPrice': compare, 'taxable': True,
                'inventoryPolicy': 'DENY',
                'inventoryItem': {'tracked': True, 'requiresShipping': True},
            } for opts, _, _ in rows],
        }
        r = gql(SET, {'input': payload})['data']['productSet']
        if r['userErrors']:
            print(f'  !! productSet: {json.dumps(r["userErrors"])[:400]}')
            failures.append(kit_title)
            continue
        made = {tuple(sorted((o['name'], o['value'])
                             for o in v['selectedOptions'])): v['id']
                for v in r['product']['variants']['nodes']}
        print(f'  productSet ok: {len(made)} variants')

        # 2. components, per variant
        batch = []
        for opts, cids, _ in rows:
            key = tuple(sorted((n, v) for n, v in opts))
            vid = made.get(key)
            if not vid:
                print(f'  !! no variant created for {opts}')
                failures.append(kit_title)
                continue
            batch.append({'parentProductVariantId': vid,
                          'removeAllProductVariantRelationships': True,
                          'productVariantRelationshipsToCreate':
                              [{'id': c, 'quantity': 1} for c in cids]})
        for i in range(0, len(batch), 10):
            rr = gql(REL, {'input': batch[i:i + 10]}
                     )['data']['productVariantRelationshipBulkUpdate']
            if rr['userErrors']:
                print(f'  !! relationships: {json.dumps(rr["userErrors"])[:400]}')
                failures.append(kit_title)
        print(f'  components attached to {len(batch)} variant(s)')

        # 3. reprice. This MUST come after the relationships, not before.
        # productVariantRelationshipBulkUpdate defaults to deriving the parent
        # price from the sum of its components, so it silently overwrites
        # whatever productSet just wrote: the first run left New Puppy at 63.95
        # for Small and 66.95 for Medium instead of a flat 54.00. A kit is sold
        # at one price regardless of which size or colorway is chosen, so the
        # price is re-asserted here and then verified.
        reprice(kit['id'], price, compare)

        # 4. verify this kit before moving to the next
        fresh = gql(VERIFY_Q, {'id': kit['id']})['data']['product']
        want_n = len(bundle_names)
        bad = [v['title'] for v in fresh['variants']['nodes']
               if len(v['productVariantComponents']['nodes']) != want_n]
        prices_ok = all(v['price'] == price and v['compareAtPrice'] == compare
                        for v in fresh['variants']['nodes'])
        ok = not bad and prices_ok and len(fresh['variants']['nodes']) == len(rows)
        print(f'  {"OK " if ok else "BAD"} {len(fresh["variants"]["nodes"])} variants, '
              f'each with {want_n} components, prices consistent={prices_ok}')
        if bad:
            print(f'      wrong component count: {bad[:5]}')
        if not ok:
            failures.append(kit_title)

    print('\n' + '=' * 66)
    if not apply and not reprice_only:
        print('Plan only. Use --apply to rebuild.')
        return 0
    if failures:
        print(f'FAILED: {sorted(set(failures))}')
        print('Backups of the previous state are in config/kit-backup/')
        return 1
    print('all six kits rebuilt and verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
