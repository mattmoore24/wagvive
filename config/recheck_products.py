#!/usr/bin/env python3
"""Re-cost the products whose study rows used the wrong CJ variant.

For each product it takes the variant SKUs we ACTUALLY sell, reads cost and
weight from CJ, quotes freight live through freight_floor.resolve(), and
recomputes margin at the market delivered price the study observed.

    python config/recheck_products.py                 # the five known-bad rows
    python config/recheck_products.py --all           # every active product
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api, freight_floor, pricing

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

SUSPECT = ['Anti-Spill Floating Water Bowl', 'Waterproof Snuggle Blanket',
           'Dental & Ear Wipes', 'Waterproof Sofa & Furniture Cover',
           'Pet Hair Remover Mitt']


def live_products():
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/products.json'
        f'?limit=250&status=active&fields=id,title,variants',
        headers={'X-Shopify-Access-Token': TOKEN})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())['products']


def cj_variant_map(spu):
    """sku -> (cost, weight) straight from CJ for one SPU."""
    d = cj_api.call('/product/query', {'productSku': spu}) or {}
    out = {}
    for v in ((d.get('data') or {}).get('variants') or []):
        try:
            out[v.get('variantSku')] = (float(v.get('variantSellPrice')),
                                        float(v.get('variantWeight')))
        except (TypeError, ValueError):
            continue
    return out


def main():
    do_all = '--all' in sys.argv
    study = {r['product']: r for r in json.load(
        open(os.path.join(ROOT, 'docs', 'qa', 'delivered-price.json'),
             encoding='utf-8'))['products']}

    rows = []
    for p in live_products():
        title = p['title']
        if 'Kit' in title:
            continue
        if not do_all and not any(s in title for s in SUSPECT):
            continue
        skus = [v['sku'] for v in p['variants'] if v.get('sku')]
        if not skus:
            continue
        spu = skus[0][:11]
        cjmap = cj_variant_map(spu)
        # Only the variants we actually list.
        mine = {s: cjmap[s] for s in skus if s in cjmap}
        if not mine:
            print(f'  ! no CJ match for {title[:40]} (spu {spu})')
            continue
        # Worst case a customer can pick: dearest goods, heaviest parcel.
        cost = max(c for c, _ in mine.values())
        weight = max(w for _, w in mine.values())
        vid = None
        d = cj_api.call('/product/query', {'productSku': spu}) or {}
        for v in ((d.get('data') or {}).get('variants') or []):
            if v.get('variantSku') in mine and abs(float(v.get('variantWeight', 0)) - weight) < 1:
                vid = v.get('vid'); break
        freight, carrier, aging, est = (None, '', '', True)
        if vid:
            fr = cj_api.call('/logistic/freightCalculate', payload={
                'startCountryCode': 'CN', 'endCountryCode': 'US',
                'products': [{'quantity': 1, 'vid': vid}]})
            freight, carrier, aging, est = freight_floor.resolve(fr.get('data'), spu, weight)
        s = study.get(title, {})
        market = s.get('market_delivered')
        old_w, old_c, old_f = s.get('weight_g'), s.get('cost'), s.get('freight')
        m_at_market = None
        if market and freight:
            # market is a DELIVERED price; ours is item price + shipping under $60
            m_at_market = pricing.margin(float(market), cost, freight) * 100
        rows.append(dict(title=title, cost=cost, weight=weight, freight=freight,
                         carrier=carrier, aging=aging, est=est, market=market,
                         old_w=old_w, old_c=old_c, old_f=old_f, m=m_at_market,
                         old_m=s.get('margin_at_market_delivered'),
                         price=[v['price'] for v in p['variants']][0]))

    print(f"\n{'product':34}{'ours':>7}{'cost':>7}{'freight':>9}"
          f"{'mkt':>7}{'mgn@mkt':>9}   was (study)")
    for r in sorted(rows, key=lambda x: (x['m'] if x['m'] is not None else 99)):
        was = (f"{r['old_w']:.0f}g ${r['old_c']:.2f} fr${r['old_f']:.2f} "
               f"{r['old_m']:.1f}%" if r['old_w'] else '-')
        m = f"{r['m']:.1f}%" if r['m'] is not None else '   -'
        print(f"  {r['title'][:32]:34}{r['weight']:>6.0f}g{r['cost']:>7.2f}"
              f"{r['freight'] or 0:>9.2f}{r['market'] or 0:>7.2f}{m:>9}   {was}")
        print(f"      carrier {r['carrier']} {r['aging']}"
              f"{'  ESTIMATED' if r['est'] else ''}   live price ${r['price']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
