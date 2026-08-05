#!/usr/bin/env python3
"""
Build the curated variant set on the six original SKUs.

Curated, not exhaustive: no spare parts, no multipacks, one product family per
listing. Every variant has to be something the listing's own title honestly
describes.

The first variant in each product keeps its existing Shopify variant id, because
the Grooming Essentials Kit references those ids as bundle components - replacing
them outright would break the kit.

Prices come from config/pricing.py against measured CJ freight. Anything already
clearing the floor keeps its current price; only the wipes move.
"""
import json, os, sys, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pricing import margin, min_price

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# product id -> (option name, [(CJ variant key, storefront value, price, freight)])
PLAN = {
    10456336990497: ('Color', 'Self-Cleaning Slicker Brush', [
        ('Green',  'Green',  28.00, 3.00),
        ('Pink',   'Pink',   28.00, 3.00),
        ('Orange', 'Orange', 28.00, 3.00),
    ]),
    10456337056033: ('Color', 'Grooming & Shedding Gloves', [
        ('Dark brown-1PCS',            'Dark Brown',  19.00, 4.94),
        ('Black-1PCS',                 'Black',       19.00, 4.94),
        ('Light Brown-1PCS',           'Light Brown', 19.00, 4.94),
        ('Hair Removal Gloves-1PCS',   'Classic',     19.00, 4.94),
    ]),
    10456337154337: ('Type', 'Ear & Teeth Cleaning Wipes', [
        ('Set',                            'Ear & Teeth (both)', 44.00, 12.03),
        ('Ear Cleaning Wipes 50 Pieces',   'Ear wipes only',     30.00, 7.88),
        ('Tooth Cleaning Wipes 50 Pieces', 'Teeth wipes only',   30.00, 7.88),
    ]),
    10456337318177: ('Color', 'Quiet Electric Nail Grinder', [
        ('Deep Green', 'Deep Green', 32.00, 7.79),
        ('Pure White', 'Pure White', 32.00, 7.79),
    ]),
    # Two axes: Shopify rejects "/" in an option name, and colour x capacity is
    # a better picker than eight concatenated values anyway.
    10456337547553: (['Color', 'Capacity'], 'Anti-Spill Floating Water Bowl', [
        ('Pink',     ['Pink', '1.5L'],  42.00, 11.77),
        ('Blue',     ['Blue', '1.5L'],  42.00, 11.77),
        ('Grey',     ['Grey', '1.5L'],  42.00, 11.77),
        ('White',    ['White', '1.5L'], 42.00, 11.77),
        ('Pink 2L',  ['Pink', '2L'],    46.00, 12.50),
        ('Blue 2L',  ['Blue', '2L'],    46.00, 12.50),
        ('Grey 2L',  ['Grey', '2L'],    46.00, 12.50),
        ('White 2L', ['White', '2L'],   46.00, 12.50),
    ]),
    10456337613089: ('Color', 'Slow Feeder Bowl', [
        ('Green',  'Green',  22.00, 8.01),
        ('Pink',   'Pink',   22.00, 8.01),
        ('Orange', 'Orange', 22.00, 8.01),
    ]),
}

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


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def main():
    with open(os.path.join(ROOT, 'config', 'cj_variants.json'), encoding='utf-8') as fh:
        cj = json.load(fh)

    for pid, (option_spec, label, rows) in PLAN.items():
        names = option_spec if isinstance(option_spec, list) else [option_spec]
        cjv = {(v['key'] or '').strip(): v for v in cj[str(pid)]['variants']}
        current = api('GET', f'products/{pid}.json')['product']
        keep_id = current['variants'][0]['id']

        variants, report = [], []
        for i, (cj_key, value, price, freight) in enumerate(rows):
            vals = value if isinstance(value, list) else [value]
            v = cjv.get(cj_key)
            if not v:
                print(f'  !! {label}: CJ key not found {cj_key!r}')
                continue
            entry = {
                'price': f'{price:.2f}',
                'sku': v['sku'], 'weight': v['weight_g'] or 0, 'weight_unit': 'g',
                'inventory_management': 'shopify', 'inventory_policy': 'deny',
                'requires_shipping': True,
            }
            for n, val in enumerate(vals, 1):
                entry[f'option{n}'] = val
            if i == 0:
                entry['id'] = keep_id      # preserve the bundle component reference
            variants.append(entry)
            report.append((' / '.join(vals), v['cost'], freight, price,
                           margin(price, v['cost'], freight) * 100,
                           min_price(v['cost'], freight)))

        options = []
        for n, name in enumerate(names):
            seen, vals = set(), []
            for r in rows:
                rv = r[1] if isinstance(r[1], list) else [r[1]]
                if rv[n] not in seen:
                    seen.add(rv[n]); vals.append(rv[n])
            options.append({'name': name, 'values': vals})

        res = api('PUT', f'products/{pid}.json', {'product': {
            'id': pid, 'options': options, 'variants': variants,
        }})['product']

        print(f'{label}  ({" x ".join(names)}) -> {len(res["variants"])} variants')
        for value, cost, freight, price, m, floor in report:
            flag = 'ok' if price >= floor else 'BELOW FLOOR'
            print(f'    {value:22} cost ${cost:<6.2f} freight ${freight:<6.2f} '
                  f'${price:<7.2f} {m:5.1f}%  (floor ${floor:.2f}) {flag}')
        print()


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
