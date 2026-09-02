#!/usr/bin/env python3
"""Check every bundle kit against the kit margin floor.

margin_guard skips them: a Shopify bundle carries no SKU of its own, so there is
nothing to look up. Their economics are real though - the kit price is fixed
while the cost is the sum of the component goods plus ONE consolidated parcel,
which is why kits work at all (the Grooming kit's four items ship together for a
fraction of four separate shipments).

Components are read from the live bundle definition rather than hardcoded, so
this stays correct if a kit is rebuilt.
"""
import json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
import freight_floor
from pricing import DUTY_PCT, DUTY_PCT_US_WAREHOUSE, landed, FLAT, PCT, SALES_TAX_AVG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 20% since 2026-09-02, matching the store-wide floor. It was 30% from
# 2026-08-04, on the reasoning that a kit is more work to assemble and should
# earn more for the complexity.
#
# That reasoning was retired by the owner for a plain commercial reason: at 30%
# the kits price themselves out of the basket. A kit only earns its complexity
# if somebody buys it, and a store with no traction cannot afford a premium on
# its highest-consideration items. Kits are still free to run ABOVE 20% where
# the demand model says the price holds; this is the floor, not the target.
FLOOR = 0.20

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

BUNDLE_Q = """
query($id: ID!) {
  product(id: $id) {
    title
    variants(first: 5) {
      nodes {
        id price
        productVariantComponents(first: 20) {
          nodes { quantity productVariant { sku title product { title } } }
        }
      }
    }
  }
}
"""


def gql(query, variables):
    body = json.dumps({'query': query, 'variables': variables}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def cj_lookup(sku):
    """sku -> (vid, cost, weight_g) via the parent SPU.

    Weight is returned because a kit ships as ONE parcel and its freight has to
    be estimated from the COMBINED weight; without it the only fallback is
    summing per-item parcels, which overstated the Dog Enrichment Kit's freight
    by 71% against the real invoice.
    """
    r = cj_api.call('/product/query', {'productSku': str(sku)[:11]})
    for v in ((r.get('data') or {}).get('variants') or []):
        if v.get('variantSku') == sku:
            raw = str(v.get('variantSellPrice') or '').split('-')[0]
            try:
                wt = float(v.get('variantWeight') or 0)
            except (TypeError, ValueError):
                wt = 0.0
            return v.get('vid'), float(raw), wt
    return None, None, 0.0


def main():
    kits = [p for p in api('products.json?limit=250&status=active')['products']
            if not any(v.get('sku') for v in p['variants'])]
    if not kits:
        print('no bundle products found'); return

    fee_rate = PCT * (1 + SALES_TAX_AVG)
    problems = []

    for k in kits:
        d = gql(BUNDLE_Q, {'id': f'gid://shopify/Product/{k["id"]}'})
        pv = (d.get('data') or {}).get('product')
        if not pv:
            print(f'{k["title"]}: no bundle data'); continue
        for var in pv['variants']['nodes']:
            price = float(var['price'])
            comps = var['productVariantComponents']['nodes']
            if not comps:
                print(f'{pv["title"]}: variant has no components'); continue

            print(f'{pv["title"].encode("ascii", "replace").decode()}  ${price:.2f}')
            goods, items, china, weights = 0.0, [], False, []
            for c in comps:
                sku = c['productVariant']['sku']
                vid, cost, wt = cj_lookup(sku)
                if cost is None:
                    print(f'   {sku}  NOT RESOLVED'); continue
                qty = c['quantity']
                goods += cost * qty
                items.append({'quantity': qty, 'vid': vid})
                weights.append((wt or 0) * qty)
                if not str(sku).startswith('CJBQ'):
                    china = True
                print(f'   x{qty} {c["productVariant"]["product"]["title"][:34]:36} '
                      f'{sku:22} ${cost:.2f}')

            # A consolidated parcel is the point of a kit, but it only happens if
            # ONE carrier serves every component. The Grooming kit fails that: the
            # Slicker Brush has a single carrier option, so the combined quote
            # comes back empty and CJ ships the kit as separate parcels. Falling
            # back to an estimate there would flatter the margin badly - the real
            # cost is the sum of the individual shipments.
            start = 'CN' if china else 'US'
            r = cj_api.call('/logistic/freightCalculate', payload={
                'startCountryCode': start, 'endCountryCode': 'US', 'products': items})
            combined = r.get('data') or []
            if combined:
                freight, carrier, aging, estimated = freight_floor.resolve(combined)
                split = False
            else:
                # CJ would not quote the basket. It does NOT follow that the kit
                # ships as separate parcels, and assuming so was a real and
                # expensive error: summing per-item estimates charges the fixed
                # parcel cost once PER ITEM. For the Dog Enrichment Kit that gave
                # $25.42 of modelled freight against $14.85 CJ actually billed on
                # order #1002, turning a 45% margin kit into an 11% "breach" that
                # would have had its price RAISED.
                #
                # A kit ships as one parcel, so estimate it as one parcel, from
                # the combined weight, against the line fitted to real invoices.
                split = False
                estimated = True
                grams = sum(float(w or 0) for w in weights)
                freight = freight_floor.combined_estimate(grams)
                if freight is None:
                    freight, split = 0.0, True
                    for it in items:
                        ri = cj_api.call('/logistic/freightCalculate', payload={
                            'startCountryCode': start, 'endCountryCode': 'US',
                            'products': [it]})
                        f, _n, _a, _e = freight_floor.resolve(ri.get('data'))
                        freight += f
                    carrier = f'{len(items)} parcels (no weights)'
                    aging = ''
                else:
                    carrier = f'one parcel, {grams:.0f}g (invoice-fitted)'
                    aging = ''

            duty = DUTY_PCT if china else DUTY_PCT_US_WAREHOUSE
            cost_total = landed(goods, freight, duty) + fee_rate * price + FLAT
            m = (price - cost_total) / price * 100
            need = (landed(goods, freight, duty) + FLAT) / (1 - fee_rate - FLOOR)

            flag = '' if price >= need - 0.005 else f'   <-- needs ${need:.2f}'
            est = '  (freight estimated)' if estimated else ''
            print(f'   goods ${goods:.2f}  freight ${freight:.2f} via '
                  f'{str(carrier)[:26]} {aging or ""}{est}')
            print(f'   margin {m:.1f}%{flag}\n')
            if price < need - 0.005:
                problems.append((pv['title'], var['id'], price, need, m))

    if problems:
        print('BELOW FLOOR:')
        for t, vid, price, need, m in problems:
            print(f'  {t[:34]:36} ${price:.2f} -> ${need:.2f}  ({m:.1f}%)')
        sys.exit(1)
    print(f'All kits clear the {FLOOR:.0%} floor.')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
