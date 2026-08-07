#!/usr/bin/env python3
"""Swap one product image for a new file, keeping position, alt and variant wiring.

Written to remove a SUPPLIER's brand mark that was embossed on the orange module
in the Heartbeat Soothing Sloth photo. A third-party logo has no business sitting
on a Wagvive product page, and it also turns to garbled pseudo-lettering whenever
that photo is used as a reference for generated art.

Three things have to survive the swap or the listing quietly degrades:

  * position    a new image lands last unless told otherwise, so the product
                card would start showing the lifestyle shot instead.
  * alt         accessibility, and several audits key off it.
  * variant_ids `variant.image_id` is what drives the cart thumbnail and the
                swatch photo swap. Deleting an image silently nulls it, and
                nothing on the storefront complains: the cart just shows a
                generic placeholder. This re-points the variants and then proves
                it by re-reading the variant, not the image.

Upload happens BEFORE the delete, so a failure leaves the old image in place
rather than a product with no photo.

    python config/replace_product_image.py <product_id> <old_image_id> <file>
"""
import base64, json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode()
            time.sleep(0.55)          # REST is capped at 2 calls/second
            return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    pid, old_id, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    before = api('GET', f'products/{pid}.json')['product']
    old = next((i for i in before['images'] if i['id'] == old_id), None)
    if not old:
        print(f'image {old_id} is not on product {pid}')
        return 1
    wired = [v['id'] for v in before['variants'] if v.get('image_id') == old_id]
    # Bundle variants carry no image at all, by design. Compare orphans before
    # and after rather than demanding zero, or every kit fails a check that is
    # describing its normal state instead of anything this swap did.
    orphans_before = {v['id'] for v in before['variants'] if not v.get('image_id')}
    print(f"{before['title']}")
    print(f"  replacing image {old_id} at position {old['position']}")
    print(f"  alt      : {old.get('alt')!r}")
    print(f"  variants : {wired or 'none wired to it'}")
    print(f"  gallery  : {len(before['images'])} image(s)")

    with open(path, 'rb') as fh:
        blob = fh.read()
    new = api('POST', f'products/{pid}/images.json', {'image': {
        'attachment': base64.b64encode(blob).decode(),
        'filename': os.path.basename(path),
        'alt': old.get('alt') or '',
        'position': old['position'],
        'variant_ids': old.get('variant_ids') or [],
    }})['image']
    print(f"  uploaded {len(blob)//1024} KB as image {new['id']}")

    api('DELETE', f'products/{pid}/images/{old_id}.json')

    after = api('GET', f'products/{pid}.json')['product']
    img = next((i for i in after['images'] if i['id'] == new['id']), None)
    now_wired = [v['id'] for v in after['variants']
                 if v.get('image_id') == new['id']]
    orphans_after = {v['id'] for v in after['variants'] if not v.get('image_id')}
    orphans = sorted(orphans_after - orphans_before)

    checks = {
        'image present': bool(img),
        'gallery size unchanged': len(after['images']) == len(before['images']),
        'position kept': bool(img) and img['position'] == old['position'],
        'alt kept': bool(img) and (img.get('alt') or '') == (old.get('alt') or ''),
        'variants re-wired': sorted(now_wired) == sorted(wired),
        'no variant newly lost its image': not orphans,
        'old image gone': all(i['id'] != old_id for i in after['images']),
    }
    for k, v in checks.items():
        print(f"  {'OK ' if v else 'BAD'} {k}")
    if not all(checks.values()):
        print(f'\ndebug: orphan variants {orphans}, wired {now_wired}')
        return 1
    print(f"\n{after['title']}: image replaced and verified")
    print(f"  new src: {img['src']}")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
