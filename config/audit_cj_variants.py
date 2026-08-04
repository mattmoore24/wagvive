#!/usr/bin/env python3
"""
Dump CJ variant and sizing data for every source product in the catalogue.

Feeds the imagery/sizing audit: for each SPU it records the full variant list
(so missing sizes show up), each variant's key, dimensions and weight, and the
supplier description HTML, which is where CJ hides its size charts.

Query CJ by SPU (`sku[:11]`), NOT by variant SKU — the variant SKU returns
"Product not found".

Usage:
    python config/audit_cj_variants.py <spus.json> <out.json>
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

TAG = re.compile(r'<[^>]+>')


def text_of(html):
    """Description HTML flattened to text, keeping table cells separable."""
    if not html:
        return ''
    s = re.sub(r'</(td|th|tr|p|div|li|br)>', ' | ', html, flags=re.I)
    s = TAG.sub(' ', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&')
    return re.sub(r'\s*\|\s*(\|\s*)+', ' | ', re.sub(r'[ \t]+', ' ', s)).strip()


def main():
    spu_file, out_file = sys.argv[1], sys.argv[2]
    with open(spu_file, encoding='utf-8') as fh:
        wanted = json.load(fh)

    out = {}
    for i, entry in enumerate(wanted, 1):
        spu = entry['spu']
        res = cj_api.call('/product/query', {'productSku': spu})
        d = res.get('data')
        if not d:
            print(f'{i:2}. {spu}  NO DATA: {json.dumps(res)[:160]}')
            out[spu] = {'error': json.dumps(res)[:300], 'title': entry.get('title')}
            continue
        variants = []
        for v in (d.get('variants') or []):
            variants.append({
                'sku': v.get('variantSku'),
                'key': v.get('variantKey'),
                'nameEn': v.get('variantNameEn'),
                'len_mm': v.get('variantLength'),
                'wid_mm': v.get('variantWidth'),
                'hei_mm': v.get('variantHeight'),
                'standard': v.get('variantStandard'),
                'weight_g': v.get('variantWeight'),
                'cost': v.get('variantSellPrice'),
            })
        out[spu] = {
            'title': entry.get('title'),
            'cj_name': d.get('productNameEn'),
            'weight_g': d.get('productWeight'),
            'variant_count': len(variants),
            'variants': variants,
            'description_text': text_of(d.get('description'))[:6000],
        }
        print(f'{i:2}. {spu}  {len(variants):2} variants  {str(d.get("productNameEn"))[:50]}')

    with open(out_file, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(f'\nwrote {out_file}: {len(out)} products')


if __name__ == '__main__':
    main()
