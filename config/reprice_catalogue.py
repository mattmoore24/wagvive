#!/usr/bin/env python3
"""Re-cost and reprice every active single product from first principles.

Built after the 2026-08-04 study was found to have costed five products against
CJ MULTIPACK variants (the Anti-Spill Water Bowl at 1,833g/$11.69 is CJ's
"Grey 3pcs"; the single is 620g/$4.13). Everything here reads the variant SKUs
we actually list, pulls cost and weight from CJ for those SKUs only, and quotes
freight live.

Pricing basis: market prices observed for competitors are DELIVERED prices.
Ours is an item price plus $5.95 shipping below the $60 free-shipping
threshold. So delivered parity means:

    item price = market delivered - 5.95

That is the aggressive end. The table also shows the margin if we simply price
AT the observed market number (customer pays shipping on top), which is the
soft end. Both are reported so the decision is visible rather than assumed.

    python config/reprice_catalogue.py            # table only, writes nothing
    python config/reprice_catalogue.py --json out.json
"""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import cj_api, freight_floor, pricing

SHIP = 5.95          # flat rate below the free-shipping threshold
FREE_OVER = 60.00

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


def live_products():
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/products.json'
        f'?limit=250&status=active&fields=id,title,handle,variants',
        headers={'X-Shopify-Access-Token': TOKEN})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())['products']


def charm(x):
    """Round to a .99 ending, never upward past the target."""
    if x <= 0:
        return 0.0
    base = int(x)
    out = base - 1 + 0.99 if x < base + 0.99 else base + 0.99
    return max(out, 0.99)


def main():
    study = {r['product']: r for r in json.load(
        open(os.path.join(ROOT, 'docs', 'qa', 'delivered-price.json'),
             encoding='utf-8'))['products']}

    rows = []
    prods = [p for p in live_products() if 'Kit' not in p['title']]
    for i, p in enumerate(prods, 1):
        skus = [v['sku'] for v in p['variants'] if v.get('sku')]
        if not skus:
            continue
        spu = skus[0][:11]
        d = cj_api.call('/product/query', {'productSku': spu}) or {}
        variants = (d.get('data') or {}).get('variants') or []
        mine = {v.get('variantSku'): v for v in variants
                if v.get('variantSku') in set(skus)}
        if not mine:
            print(f'  ! {p["title"][:38]}: no CJ variant match (spu {spu})',
                  file=sys.stderr)
            continue
        # Worst case the customer can choose.
        cost = max(float(v['variantSellPrice']) for v in mine.values())
        heavy = max(mine.values(), key=lambda v: float(v.get('variantWeight') or 0))
        weight = float(heavy.get('variantWeight') or 0)
        fr = cj_api.call('/logistic/freightCalculate', payload={
            'startCountryCode': 'CN', 'endCountryCode': 'US',
            'products': [{'quantity': 1, 'vid': heavy.get('vid')}]})
        freight, carrier, aging, est = freight_floor.resolve(fr.get('data'), spu, weight)

        s = study.get(p['title'], {})
        market = s.get('market_delivered')
        cur = float(p['variants'][0]['price'])

        rec_parity = charm(float(market) - SHIP) if market else None
        m_parity = (pricing.margin(rec_parity, cost, freight) * 100
                    if rec_parity else None)
        m_at_market = (pricing.margin(float(market), cost, freight) * 100
                       if market else None)
        m_current = pricing.margin(cur, cost, freight) * 100

        rows.append(dict(title=p['title'], id=p['id'], handle=p['handle'],
                         cost=cost, weight=weight, freight=freight,
                         carrier=carrier, est=est, market=market, cur=cur,
                         m_cur=m_current, rec=rec_parity, m_rec=m_parity,
                         m_mkt=m_at_market,
                         nvar=len(p['variants']),
                         old_m=s.get('margin_at_market_delivered')))
        time.sleep(0.4)

    rows.sort(key=lambda r: (r['m_rec'] if r['m_rec'] is not None else 999))

    print(f'\n{len(rows)} active single products, costed from the SKUs we list, '
          f'freight quoted live\n')
    print(f"{'product':32}{'g':>6}{'cost':>7}{'frt':>7}{'now':>8}{'mgn':>7}"
          f"{'mkt':>7}{'REC':>8}{'mgn':>7}  verdict")
    for r in rows:
        verdict = ('DROP' if (r['m_rec'] is not None and r['m_rec'] < 0) else
                   'thin' if (r['m_rec'] is not None and r['m_rec'] < 25) else
                   'ok')
        rec = f"{r['rec']:.2f}" if r['rec'] else '   -'
        mrec = f"{r['m_rec']:.0f}%" if r['m_rec'] is not None else '  -'
        mkt = f"{r['market']:.2f}" if r['market'] else '   -'
        print(f"  {r['title'].replace('Wagvive ','')[:30]:32}{r['weight']:>6.0f}"
              f"{r['cost']:>7.2f}{r['freight']:>7.2f}{r['cur']:>8.2f}"
              f"{r['m_cur']:>6.0f}%{mkt:>7}{rec:>8}{mrec:>7}  {verdict}")

    tot_cur = sum(r['cur'] for r in rows)
    tot_rec = sum(r['rec'] for r in rows if r['rec'])
    print(f"\ncatalogue price sum: ${tot_cur:,.2f} now -> ${tot_rec:,.2f} "
          f"at delivered parity ({(tot_rec/tot_cur-1)*100:+.0f}%)")
    print(f"median margin at recommended: "
          f"{sorted(r['m_rec'] for r in rows if r['m_rec'] is not None)[len(rows)//2]:.0f}%")

    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        json.dump(rows, open(out, 'w'), indent=1)
        print(f'\nwritten -> {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
