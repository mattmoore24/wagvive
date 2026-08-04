#!/usr/bin/env python3
"""Push approved Runway re-shoot images to Shopify and wire variant swatches.

Reads a manifest JSON (see MANIFEST FORMAT below), then per product:

  1. POSTs the new images as base64 attachments, in manifest order, with alt text.
  2. Associates images to variants by colour value: an image whose `colour`
     matches option1/option2 of a variant gets that variant's id attached, which
     is what makes selecting a swatch swap the photo.
  3. DELETEs the old images only after every new one is in, so the product
     never sits with an empty gallery.

MANIFEST FORMAT (config/reshoot_manifests/<group>.json):
{
  "<product handle>": [
     {"file": "<abs path>", "alt": "...", "colour": "Green" | null,
      "cover": true|false}
  ], ...
}
The first entry becomes position 1. `colour` null means no variant association
(lifestyle shots, dimension graphics).

Usage: python apply_reshoot.py <manifest.json> [--keep-old]
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


def api(method, path, payload=None, retries=3):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(3); continue
            raise


def main():
    manifest_path = sys.argv[1]
    keep_old = '--keep-old' in sys.argv
    with open(manifest_path, encoding='utf-8') as fh:
        manifest = json.load(fh)

    products = {p['handle']: p for p in
                api('GET', 'products.json?limit=250&status=active')['products']}

    for handle, shots in manifest.items():
        p = products.get(handle)
        if not p:
            print(f'!! {handle} not found, skipped'); continue
        print(f'== {p["title"]}')
        old_ids = [i['id'] for i in p['images']]

        # colour -> variant ids (colour can be option1 or option2)
        cmap = {}
        for v in p['variants']:
            for opt in (v.get('option1'), v.get('option2'), v.get('option3')):
                if opt:
                    cmap.setdefault(opt, []).append(v['id'])

        for pos, shot in enumerate(shots, 1):
            with open(shot['file'], 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
            payload = {'image': {
                'attachment': b64,
                'filename': os.path.basename(shot['file']),
                'alt': shot['alt'], 'position': pos}}
            colour = shot.get('colour')
            if colour:
                vids = cmap.get(colour, [])
                if vids:
                    payload['image']['variant_ids'] = vids
                else:
                    print(f'   ?? no variants match colour "{colour}"')
            img = api('POST', f'products/{p["id"]}/images.json', payload)['image']
            tag = f' -> {len(payload["image"].get("variant_ids", []))} variant(s)' \
                if colour else ''
            print(f'   pos {pos}: {os.path.basename(shot["file"])[:44]}{tag}')
            time.sleep(0.6)

        if not keep_old:
            for iid in old_ids:
                api('DELETE', f'products/{p["id"]}/images/{iid}.json')
                time.sleep(0.4)
            print(f'   removed {len(old_ids)} old image(s)')

        # verify every variant now has an image
        fresh = api('GET', f'products/{p["id"]}.json')['product']
        naked = [v['title'] for v in fresh['variants'] if not v.get('image_id')]
        if naked:
            print(f'   !! variants without image: {naked}')
        else:
            print('   all variants wired')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
