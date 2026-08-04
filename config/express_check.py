#!/usr/bin/env python3
"""Is a paid Express tier actually deliverable, and at what price?

The checkout now offers Express at $15. Before promising a faster window we need
carriers that really hit it. This lists every CJ option for representative
variants sorted by transit time, so the Express promise can be set to something
the supply chain can honour - or dropped.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api
from pricing import margin, DUTY_PCT, DUTY_PCT_US_WAREHOUSE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def upper_days(aging):
    nums = re.findall(r'\d+', str(aging or ''))
    return int(nums[-1]) if nums else 999


def options(vid, start='CN'):
    r = cj_api.call('/logistic/freightCalculate', payload={
        'startCountryCode': start, 'endCountryCode': 'US',
        'products': [{'quantity': 1, 'vid': vid}]})
    return [o for o in (r.get('data') or []) if o.get('logisticPrice') is not None]


def main():
    with open(os.path.join(ROOT, 'config', 'cj_variants.json'), encoding='utf-8') as fh:
        cj = json.load(fh)

    # one representative variant per SPU, cheapest first so the sample spans the
    # catalogue rather than only light items
    samples = []
    for spu, p in cj.items():
        v = p['variants'][0]
        samples.append((spu, v['sku'], v['vid'], v.get('cost')))

    for spu, sku, vid, cost in samples:
        start = 'US' if str(sku).startswith('CJBQ') else 'CN'
        opts = options(vid, start)
        if not opts:
            print(f'{spu} / {sku}  ({start})  no carriers\n')
            continue
        opts.sort(key=lambda o: (upper_days(o.get('logisticAging')), o['logisticPrice']))
        print(f'{spu} / {sku}  ({start})  cost ${cost}')
        for o in opts[:6]:
            print(f'   {upper_days(o.get("logisticAging")):>3}d  '
                  f'${o["logisticPrice"]:<8.2f} {str(o.get("logisticAging")):<9} '
                  f'{str(o.get("logisticName"))[:44]}')
        fastest = opts[0]
        cheap = min(opts, key=lambda o: o['logisticPrice'])
        gap = fastest['logisticPrice'] - cheap['logisticPrice']
        print(f'   fastest costs ${gap:.2f} more than cheapest '
              f'({upper_days(fastest.get("logisticAging"))}d vs '
              f'{upper_days(cheap.get("logisticAging"))}d)\n')


if __name__ == '__main__':
    main()
