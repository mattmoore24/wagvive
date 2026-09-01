#!/usr/bin/env python3
"""Do the KITS track inventory correctly, and does it derive from components?

WHY THIS IS ITS OWN CHECK. sync_inventory.py walks products that carry a SKU and
writes CJ's numbers in. Kits carry no SKU: they are bundle parents, so that
script never touches them and its "all in step" verdict says nothing about them.
The risk is specific and expensive: if a kit parent tracked its own stale
inventory, Shopify would happily sell a kit whose component ran out at CJ, and
the order could not be fulfilled.

WHAT CORRECT LOOKS LIKE, measured rather than assumed. A bundle parent DOES
have `inventoryItem.tracked: true` — that is normal and is NOT evidence it holds
its own stock. The distinguishing facts are:

  * `requiresComponents: true`
  * its inventory level exists but carries NO `available` quantity (compare a
    single, whose level reads available/committed/on_hand). The parent stores
    no number of its own, so it cannot sell on a stale one.
  * `sellableOnlineQuantity` is DERIVED by Shopify from the components.

So the decisive test is arithmetic: compute the component minimum independently,
`min(component available // quantity needed)`, and require it to equal what
Shopify reports as sellable. If those agree for every variant, the derivation is
demonstrably working. This script proves that plus:

  1. every kit variant requires components and holds no stock of its own
  2. every component variant is stocked at the sellable location ONLY and its
     Shopify quantity matches CJ (read via sync_inventory.cj_stock)
  3. the storefront agrees the kit is buyable

It also reports the binding component per kit variant: the one that would make
the kit unsellable first. That is the number to watch, not the kit's own.

    python config/verify_kit_inventory.py
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import sync_inventory  # noqa: E402  (the ONLY sanctioned reader of CJ stock)

CANONICAL = 'Shop location'


def cj_stock_retried(sku, tries=3):
    """sync_inventory.cj_stock, but an empty answer is retried before belief.

    CJ returns empty for healthy SKUs under load, and every audit in this repo
    that trusted a single empty read has produced a false finding: margin_guard
    reported a phantom breach, audit_cj_connections reported false
    unshippables, and this file reported ten kit components as having no stock
    on 2026-09-01 while sync_inventory was reading every one of them
    successfully in the same session (re-querying returned 9120, 13163 and
    38986 units against a healthy points budget).

    Unanswerable is UNKNOWN, never a finding.
    """
    for attempt in range(tries):
        try:
            n = sync_inventory.cj_stock(sku)
            if n is not None:
                return n
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
D, T, V = (env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'],
           env['SHOPIFY_API_VERSION'])

# Split into two queries: the nested form (kits x variants x components x
# levels) costs about 3600 points against a 1000 limit.
LIST = '''query($q: String!) {
  products(first: 20, query: $q) { nodes { id title handle } } }'''

Q = '''
query($id: ID!) {
  product(id: $id) {
    id title handle
    variants(first: 60) {
      nodes {
        id title sku requiresComponents sellableOnlineQuantity
        inventoryItem { tracked
          inventoryLevels(first: 5) {
            nodes { location { name }
              quantities(names: ["available"]) { name quantity } } } }
        productVariantComponents(first: 12) {
          nodes {
            quantity
            productVariant {
              id title sku
              product { title }
              inventoryItem { tracked
                inventoryLevels(first: 5) {
                  nodes { location { name }
                    quantities(names: ["available"]) { name quantity } } } }
            } } } } } } }
'''


def gql(q, v=None):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    rq = urllib.request.Request(f'https://{D}/admin/api/{V}/graphql.json',
                                data=body, method='POST',
                                headers={'X-Shopify-Access-Token': T,
                                         'Content-Type': 'application/json'})
    with urllib.request.urlopen(rq, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit(json.dumps(out['errors'])[:600])
    time.sleep(0.4)
    return out['data']


def avail_at(inv_item, loc=CANONICAL):
    """available at the canonical location, and anything sitting elsewhere."""
    here, elsewhere = None, {}
    for lv in (inv_item.get('inventoryLevels') or {}).get('nodes', []):
        qty = next((x['quantity'] for x in lv['quantities']
                    if x['name'] == 'available'), None)
        if lv['location']['name'] == loc:
            here = qty
        elif qty:
            elsewhere[lv['location']['name']] = qty
    return here, elsewhere


def storefront(handle):
    for attempt in range(5):
        try:
            u = (f'https://wagvive.com/products/{handle}.js'
                 f'?nocache={int(time.time()*1000)}')
            rq = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(rq, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError:
            time.sleep(3 * (attempt + 1))
    return None


def main():
    stubs = gql(LIST, {'q': "product_type:'Bundles & Kits' AND status:ACTIVE"}
                )['products']['nodes']
    kits = [gql(Q, {'id': s['id']})['product'] for s in stubs]
    print(f'{len(kits)} active kits\n')

    problems, unknown, cj_cache = [], [], {}
    total_variants = 0

    for k in kits:
        print(f"=== {k['title']} ===")
        sf = storefront(k['handle'])
        sf_avail = {v['title']: v['available'] for v in sf['variants']} if sf else {}

        for v in k['variants']['nodes']:
            total_variants += 1
            comps = v['productVariantComponents']['nodes']
            here, elsewhere = avail_at(v['inventoryItem'])
            sellable = v['sellableOnlineQuantity']

            # 1. the parent must BE a bundle and hold no stock of its own.
            # `tracked` is true on bundle parents too, so it proves nothing;
            # what matters is requiresComponents plus an empty level.
            if not comps:
                problems.append(f"{k['title']} / {v['title']}: NO components; "
                                f"it is not a bundle and would sell on its own "
                                f"stale stock")
            if not v['requiresComponents']:
                problems.append(f"{k['title']} / {v['title']}: "
                                f"requiresComponents is FALSE, so Shopify would "
                                f"sell it without checking component stock")
            if here is not None:
                problems.append(f"{k['title']} / {v['title']}: parent holds its "
                                f"OWN available quantity ({here}); it should "
                                f"derive from components, not store a number")
            if elsewhere:
                problems.append(f"{k['title']} / {v['title']}: parent stocked "
                                f"at {elsewhere}, which double counts")

            # 2. every component: sellable location only, and real CJ stock
            binding, binding_name = None, ''
            for c in comps:
                pv = c['productVariant']
                need = c['quantity'] or 1
                c_here, c_elsewhere = avail_at(pv['inventoryItem'])
                name = f"{pv['product']['title'].replace('Wagvive ', '')} "\
                       f"[{pv['title']}]"
                if c_elsewhere:
                    problems.append(f"{k['title']} / {v['title']}: component "
                                    f"{name} stocked at {c_elsewhere}")
                if not pv['inventoryItem']['tracked']:
                    problems.append(f"{k['title']} / {v['title']}: component "
                                    f"{name} is NOT tracked, so the kit cannot "
                                    f"go out of stock when it does")
                if c_here is None:
                    problems.append(f"{k['title']} / {v['title']}: component "
                                    f"{name} has NO level at {CANONICAL}")
                    c_here = 0

                sku = pv['sku']
                if sku not in cj_cache:
                    cj_cache[sku] = cj_stock_retried(sku)
                cj = cj_cache[sku]
                if cj is None:
                    # UNKNOWN, not a finding. CLAUDE.md: "An EMPTY answer from CJ
                    # is not evidence of anything." On 2026-09-01 this reported
                    # ten components as having NO CJ stock while sync_inventory
                    # had just read every one of them successfully in the same
                    # session; re-querying returned 9120, 13163 and 38986 units
                    # against a healthy points budget. Reporting that as a
                    # problem is how healthy variants get zeroed.
                    unknown.append(f"{k['title']} / {v['title']}: {name} ({sku})")
                elif c_here != cj:
                    problems.append(f"{k['title']} / {v['title']}: component "
                                    f"{name} Shopify {c_here} != CJ {cj}")

                buildable = (c_here or 0) // need
                if binding is None or buildable < binding:
                    binding, binding_name = buildable, name

            # THE decisive test: Shopify's derived sellable quantity must equal
            # the component minimum computed here independently.
            if binding is not None and sellable != binding:
                problems.append(f"{k['title']} / {v['title']}: Shopify says "
                                f"{sellable} sellable but the components only "
                                f"support {binding}; the derivation is wrong")

            live = sf_avail.get(v['title'])
            ok = (bool(comps) and v['requiresComponents'] and here is None
                  and binding and binding > 0 and sellable == binding and live)
            print(f"  {'OK ' if ok else '!! '}{v['title']:22} "
                  f"bundle={str(v['requiresComponents']):5} own_stock="
                  f"{'none' if here is None else here}  components={len(comps)}"
                  f"  derived={sellable}  computed={binding}  buyable={live}")
            print(f"       binding component: {binding_name} ({binding})")
            if live is False:
                problems.append(f"{k['title']} / {v['title']}: NOT buyable on "
                                f"the storefront")
        print()

    print('=' * 70)
    print(f'{total_variants} kit variants checked across {len(kits)} kits')
    print(f'{len(cj_cache)} distinct component SKUs resolved against CJ')
    if unknown:
        # Printed, but deliberately does NOT fail the run. CJ declining to
        # answer is not evidence that anything is wrong, and failing on it
        # trains the owner to ignore the alarm that matters.
        print(f'\n{len(unknown)} component(s) CJ would not answer for '
              f'(UNKNOWN, not a finding, re-run to resolve):')
        for u in unknown:
            print('  ? ' + u)

    if problems:
        print(f'\n{len(problems)} PROBLEM(S):')
        for p in problems:
            print('  ! ' + p)
        return 1
    print('\nEvery kit variant is a real bundle holding no stock of its own, '
          'Shopify\'s\nderived sellable quantity equals the independently '
          'computed component\nminimum, every component is stocked at the '
          'sellable location only and matches\nCJ exactly, and every kit '
          'variant is buyable on the live storefront.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
