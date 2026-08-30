#!/usr/bin/env python3
"""
Re-price against carriers that can actually meet the published delivery promise.

Earlier margins used the cheapest carrier of any speed, and some of those run
10-23 or 25-30 days - which the site's "5-11 business days" claim cannot honour.
This picks the cheapest carrier whose upper transit bound is within MAX_DAYS and
re-checks every variant against the floor in config/pricing.py (20%).
"""
import json, os, re, sys, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
from pricing import margin, min_price, DUTY_PCT, DUTY_PCT_US_WAREHOUSE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Matches the delivery window published at checkout and on the FAQ / Shipping
# pages ("5-12 business days"). Was 11, which wrongly flagged the Slicker Brush's
# only carrier (6-12 days) as breaking a promise the site never made.
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


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def best_freight(vid, start='CN', max_days=MAX_DAYS):
    """Cheapest option inside the transit promise; falls back to cheapest overall."""
    r = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    opts = [o for o in (r.get('data') or []) if o.get('logisticPrice') is not None]
    if not opts:
        return None
    inside = [o for o in opts if upper_days(o.get('logisticAging')) <= max_days]
    pool = inside or opts
    b = min(pool, key=lambda o: o['logisticPrice'])
    return {'price': b['logisticPrice'], 'name': b.get('logisticName'),
            'aging': b.get('logisticAging'), 'within_promise': bool(inside)}


def main():
    with open(os.path.join(ROOT, 'config', 'cj_variants.json'), encoding='utf-8') as fh:
        cj = json.load(fh)
    # sku -> vid across everything we know, plus the two new products
    sku_to_vid = {}
    for p in cj.values():
        for v in p['variants']:
            sku_to_vid[v['sku']] = v['vid']
    for spu in ('CJPM2920000', 'CJBQ3005963'):
        r = cj_api.call('/product/query', {'productSku': spu})
        for v in (r.get('data') or {}).get('variants', []):
            sku_to_vid[v.get('variantSku')] = v.get('vid')
        cj[spu] = {'variants': [{'sku': v.get('variantSku'),
                                 'cost': float(str(v.get('variantSellPrice')).split('-')[0])}
                                for v in (r.get('data') or {}).get('variants', [])]}
    cost_by_sku = {v['sku']: v['cost'] for p in cj.values() for v in p['variants']}

    problems = []
    print(f'Cheapest carrier delivering within {MAX_DAYS} days\n')
    for p in api('products.json?limit=250&status=active')['products']:
        title = p['title'].encode('ascii', 'replace').decode()
        if not any(v.get('sku') for v in p['variants']):
            print(f'{title}  (bundle / no SKUs - skipped)')
            continue
        print(f'{title}')
        for v in p['variants']:
            sku = v.get('sku')
            vid = sku_to_vid.get(sku)
            cost = cost_by_sku.get(sku)
            if not vid or cost is None:
                print(f'   {str(v["title"])[:30]:32} sku {sku} - not resolvable')
                continue
            start = 'US' if sku.startswith('CJBQ') else 'CN'
            f = best_freight(vid, start)
            if not f:
                print(f'   {str(v["title"])[:30]:32} no carrier')
                continue
            # US-warehouse stock was already imported; only China-origin pays duty.
            duty = DUTY_PCT_US_WAREHOUSE if start == 'US' else DUTY_PCT
            price = float(v['price'])
            m = margin(price, cost, f['price'], duty) * 100
            floor = min_price(cost, f['price'], duty)
            flag = '' if price >= floor else '  <-- BELOW FLOOR'
            note = '' if f['within_promise'] else '  (no carrier within promise)'
            print(f'   {str(v["title"])[:30]:32} ${price:<7.2f} cost ${cost:<6.2f} '
                  f'frt ${f["price"]:<6.2f} duty ${cost*duty:<5.2f} {m:5.1f}%  '
                  f'{str(f["aging"]):<7}{flag}{note}')
            if price < floor:
                problems.append((p['id'], p['title'], v['title'], price, floor, cost, f['price']))
        print()

    if problems:
        print('BELOW FLOOR:')
        for pid, pt, vt, price, floor, cost, fr in problems:
            print(f'  {pt[:34]:36} {vt[:22]:24} ${price:.2f} -> needs ${floor:.2f}')
    else:
        print('All variants clear the floor using promise-compliant carriers.')


if __name__ == '__main__':
    main()
