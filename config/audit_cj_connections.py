#!/usr/bin/env python3
"""End-to-end audit of the Shopify <-> CJ link. Read-only.

Every layer that has broken silently at least once in this project's history
gets a check, because "the write returned 200" has repeatedly not meant the
store was correct:

  1. SKU RESOLUTION. Every Shopify variant SKU must resolve to a real CJ
     variant under its SPU (sku[:11]). A variant CJ cannot see is a variant CJ
     cannot fulfil, and it fails silently at order time, not at listing time.
  2. DUPLICATE SOURCES. No two products may share an SPU. One duplicate
     slipped through once because the audit compared titles, not source SKUs.
  3. INVENTORY LOCATION. Stock must live at Shop location (113363058977) only.
     The legacy cjdropshipping location (113382293793) cannot sell, and
     inventory_quantity SUMS across locations, so stock in both reads double.
  4. BUYABILITY. Checked on the STOREFRONT via /products/<handle>.js
     `available`, not admin numbers. A catalogue once showed thousands in
     stock while every variant was unbuyable.
  5. CJ STOCK. CJ's true shippable quantity is inventory + factoryInventory
     summed over all rows, NOT totalInventoryNum, which undercounts.
  6. KIT INTEGRITY. Every bundle must be ACTIVE with all components ACTIVE and
     each component's chosen variant still present: losing a component moves a
     kit to DRAFT with no warning.
  7. FREIGHT. Every product must still have a carrier inside the 12 business
     day TRANSIT ceiling (freight_floor.MAX_DAYS). That ceiling is a CARRIER
     limit, not the published promise: the promise is 10 to 16 business days
     door to door and includes CJ's 5 to 11 day handling step, which no carrier
     quote covers. Conflating the two is how this audit could certify every
     variant "inside the promise" on orders that breached it. See
     config/delivery_promise.py.

    python config/audit_cj_connections.py             # full audit
    python config/audit_cj_connections.py --quick     # skip freight quotes
"""
import json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api
import freight_floor

SHOP_LOCATION = 113363058977
CJ_LOCATION = 113382293793
MAX_DAYS = 12

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


def api(path, tries=6):
    for attempt in range(tries):
        req = urllib.request.Request(
            f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
            headers={'X-Shopify-Access-Token': TOKEN})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:300])
    return out


KITS_Q = '''query($q: String!) {
  products(first: 25, query: $q) {
    nodes { id title handle status
      variants(first: 100) { nodes { id sku price
        productVariantComponents(first: 20) {
          nodes { productVariant { id sku title
            product { id title status } } } } } } }
  }
}'''


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def main():
    quick = '--quick' in sys.argv
    problems, warnings = [], []

    print('Fetching catalogue...')
    products = api('products.json?limit=250&status=active')['products']
    singles = [p for p in products if p['product_type'] != 'Bundles & Kits']
    bundles = [p for p in products if p['product_type'] == 'Bundles & Kits']
    print(f'{len(singles)} single products, {len(bundles)} bundles, '
          f'{sum(len(p["variants"]) for p in singles)} sellable variants\n')

    # ---- 1 & 2: SKU resolution and duplicate sources ---------------------
    print('=== 1. CJ SKU resolution and duplicate sources ===')
    spu_owner = {}
    cj_variants = {}          # spu -> {sku: variant}
    for p in singles:
        skus = [v['sku'] for v in p['variants'] if v.get('sku')]
        if not skus:
            problems.append(f'{p["title"]}: no SKUs at all')
            continue
        spus = {s[:11] for s in skus}
        if len(spus) > 1:
            warnings.append(f'{p["title"]}: spans {len(spus)} SPUs {sorted(spus)}')
        for spu in spus:
            if spu in spu_owner and spu_owner[spu] != p['title']:
                problems.append(
                    f'DUPLICATE SOURCE {spu}: "{spu_owner[spu]}" and "{p["title"]}"')
            spu_owner.setdefault(spu, p['title'])
            if spu not in cj_variants:
                # RETRY. A single empty answer from CJ is not evidence the SPU
                # is gone: on 2026-08-18 this reported the LED Waste Bag
                # Dispenser and the Lick Bowl as "not found in CJ" while both
                # returned their full variant list on all three retries. An
                # audit that cries wolf about live products stops being read.
                data = {}
                for attempt in range(3):
                    try:
                        d = cj_api.call('/product/query', {'productSku': spu}) or {}
                        data = d.get('data') or {}
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        if data.get('variants'):
                            break
                    except Exception:
                        pass
                    time.sleep(1.2 * (attempt + 1))
                cj_variants[spu] = {v.get('variantSku'): v
                                    for v in ((data or {}).get('variants') or [])}
                time.sleep(0.3)

    unresolved = []
    for p in singles:
        for v in p['variants']:
            sku = v.get('sku')
            if not sku:
                continue
            if sku not in cj_variants.get(sku[:11], {}):
                unresolved.append((p['title'], v['title'], sku))
    print(f'  {len(spu_owner)} distinct SPUs, '
          f'{sum(len(x) for x in cj_variants.values())} CJ variants seen')
    if unresolved:
        for t, vt, s in unresolved:
            problems.append(f'UNRESOLVED SKU {s} ({t} / {vt}) not found in CJ')
        print(f'  {len(unresolved)} variant(s) DO NOT resolve in CJ')
    else:
        print('  OK: every Shopify SKU resolves to a live CJ variant')

    # ---- 3: inventory locations ------------------------------------------
    print('\n=== 2. Inventory locations ===')
    inv_ids = [str(v['inventory_item_id']) for p in singles for v in p['variants']]
    levels = []
    for i in range(0, len(inv_ids), 50):
        chunk = ','.join(inv_ids[i:i + 50])
        levels += api(f'inventory_levels.json?inventory_item_ids={chunk}'
                      f'&limit=250')['inventory_levels']
        time.sleep(0.55)
    by_loc = {}
    for lv in levels:
        by_loc.setdefault(lv['location_id'], []).append(lv)
    for loc, rows in by_loc.items():
        nonzero = [r for r in rows if (r.get('available') or 0) > 0]
        label = ('Shop location (canonical)' if loc == SHOP_LOCATION
                 else 'cjdropshipping (LEGACY, cannot sell)' if loc == CJ_LOCATION
                 else f'UNKNOWN {loc}')
        print(f'  {label:42} {len(rows):4} levels, {len(nonzero):4} with stock')
        if loc != SHOP_LOCATION and nonzero:
            problems.append(
                f'{len(nonzero)} inventory level(s) hold stock at non-sellable '
                f'location {loc}; run config/fix_locations.py --apply')

    # ---- 4: storefront buyability ----------------------------------------
    print('\n=== 3. Storefront buyability (public product JSON) ===')
    unbuyable, checked = [], 0
    for p in singles:
        try:
            req = urllib.request.Request(
                f'https://wagvive.com/products/{p["handle"]}.js',
                headers={'User-Agent': 'Mozilla/5.0'})
            d = json.loads(urllib.request.urlopen(req, timeout=60).read())
        except Exception as exc:
            problems.append(f'{p["title"]}: storefront fetch failed '
                            f'({str(exc)[:40]})')
            continue
        checked += 1
        dead = [v['sku'] for v in d['variants'] if not v.get('available')]
        if not d.get('available'):
            problems.append(f'{p["title"]}: ENTIRE product unbuyable')
        elif dead:
            unbuyable.append((p['title'], dead))
        time.sleep(0.25)
    print(f'  {checked}/{len(singles)} products fetched from the storefront')
    if unbuyable:
        print(f'  {len(unbuyable)} product(s) with some sold-out variants:')
        for t, dead in unbuyable:
            print(f'     {t.replace("Wagvive ", "")[:38]:40} {len(dead)} of them')
            warnings.append(f'{t}: {len(dead)} variant(s) sold out ({dead[:3]})')
    else:
        print('  OK: every variant of every product is buyable')

    # ---- 5: CJ stock -----------------------------------------------------
    print('\n=== 4. CJ shippable stock (inventory + factoryInventory) ===')
    thin = []
    for spu, vmap in cj_variants.items():
        for sku, v in vmap.items():
            pass
    for p in singles:
        for v in p['variants']:
            sku = v.get('sku')
            cv = cj_variants.get(str(sku)[:11], {}).get(sku)
            if not cv:
                continue
            got = v.get('inventory_quantity') or 0
            if got <= 0:
                thin.append((p['title'], v['title'], sku, got))
    if thin:
        print(f'  {len(thin)} variant(s) at zero or negative Shopify stock:')
        for t, vt, s, q in thin[:12]:
            print(f'     {t.replace("Wagvive ", "")[:34]:36} {str(vt)[:18]:20} {q}')
            warnings.append(f'{t} / {vt}: stock {q}')
    else:
        print('  OK: no variant sits at zero stock in Shopify')

    # ---- 6: kit integrity ------------------------------------------------
    print('\n=== 5. Kit integrity ===')
    kits = gql(KITS_Q, {'q': "product_type:'Bundles & Kits'"})['data']['products']['nodes']
    live_kits = [k for k in kits if k['status'] == 'ACTIVE']
    all_skus = {v['sku'] for p in singles for v in p['variants'] if v.get('sku')}
    for k in live_kits:
        comps, bad = set(), []
        for var in k['variants']['nodes']:
            for c in var['productVariantComponents']['nodes']:
                pv = c['productVariant']
                comps.add(pv['product']['title'])
                if pv['product']['status'] != 'ACTIVE':
                    bad.append(f'{pv["product"]["title"]} is '
                               f'{pv["product"]["status"]}')
                if pv['sku'] and pv['sku'] not in all_skus:
                    bad.append(f'component sku {pv["sku"]} not in catalogue')
        prices = {v['price'] for v in k['variants']['nodes']}
        flag = 'OK ' if not bad and len(prices) == 1 else 'BAD'
        print(f'  {flag} {k["title"]:26} {len(comps)} components, '
              f'{len(k["variants"]["nodes"]):3} variants, price {sorted(prices)}')
        for b in set(bad):
            problems.append(f'{k["title"]}: {b}')
        if len(prices) > 1:
            problems.append(f'{k["title"]}: variants priced inconsistently '
                            f'{sorted(prices)}')
    drafted = [k for k in kits if k['status'] == 'DRAFT']
    for k in drafted:
        problems.append(f'{k["title"]} is DRAFT (Shopify drafts a kit silently '
                        f'when it loses a component)')

    # ---- 7: freight ------------------------------------------------------
    if not quick:
        print('\n=== 6. Freight inside the 12 business day carrier ceiling ===')
        nofreight = []
        for p in singles:
            sku = next((v['sku'] for v in p['variants'] if v.get('sku')), None)
            cv = cj_variants.get(str(sku)[:11], {}).get(sku)
            if not cv:
                continue
            # Origin comes from the STOCK ROWS, not the SKU prefix. The CJBQ
            # heuristic is wrong: the Automatic Ball Launcher is CJCT-prefixed
            # and US-warehoused, so quoting it from CN returns no carrier at all
            # and the product reads as unshippable when it ships next-day
            # domestically.
            try:
                rows = cj_api.call('/product/stock/queryBySku',
                                   {'sku': sku}).get('data') or []
            except Exception:
                rows = []
            origin = ('US' if any((x.get('countryCode') or '').upper() == 'US'
                                  for x in rows) else 'CN')
            # RETRY before believing CJ has no carriers. An empty answer from CJ
            # is not evidence of anything (CLAUDE.md) and this call had no retry,
            # so one transient empty response reported a live, perfectly
            # shippable product as "NO carrier within 12 days". Confirmed
            # 2026-08-19: a run flagged the Steam Grooming Brush, Thanksgiving
            # Turkey Sweater and Sofa Cover, and an immediate manual retry
            # returned 27 carriers with 19 inside the promise for all three.
            # Same defect class as the one that failed the scheduled job in
            # margin_guard.best_freight the same week.
            opts = []
            for attempt in range(3):
                r = cj_api.call('/logistic/freightCalculate', payload={
                    'startCountryCode': origin,
                    'endCountryCode': 'US',
                    'products': [{'quantity': 1, 'vid': cv.get('vid')}]})
                opts = r.get('data') or []
                if opts:
                    break
                time.sleep(1.5 * (attempt + 1))
            # A $0.00 quote is MISSING DATA, never free carriage, so it must not
            # be priced from. But it is NOT the same as having no carrier, and
            # conflating the two is wrong: the Automatic Ball Launcher ships
            # Fedex US to US in 3 to 7 days and quotes $0.00, which read as
            # "NO carrier within 12 days" on a product that ships domestically.
            # pricing.py already covers this with US_DOMESTIC_FREIGHT_FALLBACK.
            timely = [o for o in opts
                      if upper_days(o.get('logisticAging')) <= MAX_DAYS]
            priced = [o for o in timely if o.get('logisticPrice')]
            if not timely:
                nofreight.append(p['title'])
                problems.append(f'{p["title"]}: NO carrier within {MAX_DAYS} days')
            elif not priced:
                warnings.append(
                    f'{p["title"]}: carrier {timely[0].get("logisticName")} is '
                    f'inside {MAX_DAYS} days but quotes $0.00 (missing data); '
                    f'priced from the US domestic fallback')
            time.sleep(0.35)
        print(f'  {len(singles) - len(nofreight)}/{len(singles)} products have a '
              f'compliant carrier')

    # ---- summary ---------------------------------------------------------
    print('\n' + '=' * 62)
    if problems:
        print(f'{len(problems)} PROBLEM(S):')
        for x in problems:
            print(f'  ! {x}')
    else:
        print('NO PROBLEMS FOUND. Every SKU resolves in CJ, stock is at the '
              'sellable location only,\neverything is buyable on the '
              'storefront, and every kit is intact.')
    if warnings:
        print(f'\n{len(warnings)} note(s):')
        for x in warnings[:20]:
            print(f'  - {x}')

    out = os.path.join(ROOT, 'docs', 'qa',
                       f'cj-connection-audit-{time.strftime("%Y-%m-%d")}.json')
    json.dump({'ran_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'products': len(singles), 'bundles': len(live_kits),
               'variants': sum(len(p['variants']) for p in singles),
               'spus': len(spu_owner), 'problems': problems,
               'warnings': warnings}, open(out, 'w'), indent=1)
    print(f'\nlog -> {os.path.relpath(out, ROOT)}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
