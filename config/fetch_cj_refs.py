#!/usr/bin/env python3
"""
Fetch a CJ product's reference data and images for visual QA.

Downloads the CJ product record for a SKU/SPU plus every product image CJ
holds, so a session without CJ credentials (e.g. claude.ai/code) can eyeball
our generated imagery against the real product. Run via the cj-image-refs
GitHub Actions workflow, which has the credentials.

Usage:
    python config/fetch_cj_refs.py <productSku> <outdir> [shopify_image_url]

Writes to <outdir>:
    product.json          full CJ product record
    cj-01.jpg, cj-02.jpg  every image URL found in the record
    shopify-current.png   our current storefront image (if URL given)
"""
import json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cj_api

IMG_RE = re.compile(r'https?://[^"\'\s,\\]+\.(?:jpg|jpeg|png|webp)', re.I)


def image_urls(obj):
    """Every image URL anywhere in the record, first-seen order.

    CJ nests image lists as JSON-encoded strings inside JSON, so regex over
    the serialized record catches ones a structural walk would miss.
    """
    seen, out = set(), []
    for m in IMG_RE.finditer(json.dumps(obj)):
        u = m.group(0)
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as fh:
        fh.write(r.read())
    return os.path.getsize(dest)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sku, outdir = sys.argv[1], sys.argv[2]
    shopify_url = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(outdir, exist_ok=True)

    res = cj_api.call('/product/query', {'productSku': sku})
    if not res.get('data'):
        print('no data from CJ:', json.dumps(res)[:400])
        sys.exit(1)
    d = res['data']
    with open(os.path.join(outdir, 'product.json'), 'w', encoding='utf-8') as fh:
        json.dump(d, fh, indent=1, ensure_ascii=False)

    urls = image_urls(d)
    print(f'{sku}: {len(urls)} image urls in record')
    for i, u in enumerate(urls, 1):
        ext = os.path.splitext(u)[1].lower() or '.jpg'
        dest = os.path.join(outdir, f'cj-{i:02d}{ext}')
        try:
            size = fetch(u, dest)
            print(f'  cj-{i:02d}{ext}  {size} bytes  {u}')
        except Exception as exc:
            print(f'  FAILED {u}: {exc}')

    if shopify_url:
        ext = os.path.splitext(shopify_url.split('?')[0])[1].lower() or '.png'
        dest = os.path.join(outdir, f'shopify-current{ext}')
        size = fetch(shopify_url, dest)
        print(f'  shopify-current{ext}  {size} bytes')


if __name__ == '__main__':
    main()
