#!/usr/bin/env python3
"""Upload the QC-approved round-4 renders and wire variant image_ids.

Local files live in the session scratchpad (master-<key>.png, rc-<key>_<sku>.png).
Colour-level images map to every size variant of that colour. The sneaker's
01AZ variant is renamed 'Yellow' -> 'Blue' because CJ's own variant image (the
ground truth for what ships) is the royal blue shoe.
"""
import base64, json, os, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = r'C:\Users\mattm\AppData\Local\Temp\claude\C--Users-mattm-OneDrive-Claude-Code-Pet-Store\07b37851-ac47-448b-b4a5-0b479e8e1101\scratchpad\round4'

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


def api(method, path, payload=None, tries=5):
    for i in range(tries):
        try:
            url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
            data = json.dumps(payload).encode() if payload is not None else None
            req = urllib.request.Request(url, data=data, method=method, headers={
                'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 409) and i < tries - 1:
                time.sleep(2.5 * (i + 1)); continue
            raise
        except Exception:
            if i < tries - 1:
                time.sleep(3); continue
            raise


# key -> list of (local file, colour value or None for all variants)
PLAN = {
 'sneaker': [('master-sneaker.png', 'Blue'), ('rc-sneaker_CJYD252933702BY.png', 'Black'),
             ('rc-sneaker_CJYD252933703CX.png', 'Sea Fog Blue')],
 'ringball': [('master-ringball.png', 'Monkey'), ('rc-ringball_CJST257870802BY.png', 'Frog'),
              ('rc-ringball_CJST257870803CX.png', 'Dog')],
 'teddy': [('master-teddy.png', None)],
 'vocalplush': [('master-vocalplush.png', 'Fawn'), ('rc-vocalplush_CJMY126277902BY.png', 'Crooked Neck'),
                ('rc-vocalplush_CJMY126277903CX.png', 'Frog')],
 'chicken': [('master-chicken.png', 'Green'), ('rc-chicken_CJST258510902BY.png', 'Orange'),
             ('rc-chicken_CJST258510903CX.png', 'Black')],
 'towel': [('master-towel.png', 'Blue'), ('rc-towel_CJGY138841304DW.png', 'Pink'),
           ('rc-towel_CJGY138841307GT.png', 'Green')],
 'lednail': [('master-lednail.png', 'Green'), ('rc-lednail_CJYD226496003CX.png', 'Pink'),
             ('rc-lednail_CJYD226496004DW.png', 'White')],
 'dematting': [('master-dematting.png', None)],
 'pawtrimmer': [('rc-pawtrimmer_master-regen.png', None)],
 'pawcup': [('master-pawcup.png', 'Blue'), ('rc-pawcup_CJSP293469607GT.png', 'Orange'),
            ('rc-pawcup_CJSP293469613MN.png', 'Green')],
 'wblanket': [('master-wblanket.png', 'Black'), ('rc-wblanket_CJGY192649706FU.png', 'Gray'),
              ('rc-wblanket_CJGY192649711KP.png', 'Coffee')],
 'thunder': [('master-thunder.png', 'Grey'), ('rc-thunder_CJYD264078602BY.png', 'Dark Blue'),
             ('rc-thunder_CJYD264078603CX.png', 'Grey and Blue')],
 'heartbeat': [('master-heartbeat.png', None)],
 'fleece': [('master-fleece.png', 'Camel'), ('rc-fleece_CJGY211711310JQ.png', 'Beige'),
            ('rc-fleece_CJGY211711317QJ.png', 'Pink')],
}

RENAME_OPTION1 = {'sneaker': {'CJYD252933701AZ': 'Blue'}}


def main():
    ids = json.load(open(os.path.join(ROOT, 'config', 'round4_product_ids.json')))
    for key, plan in PLAN.items():
        pid = ids[key]['id']
        p = api('GET', f'products/{pid}.json')['product']

        # option value fix first
        for sku, newval in RENAME_OPTION1.get(key, {}).items():
            v = next((v for v in p['variants'] if v['sku'] == sku), None)
            if v and v['option1'] != newval:
                api('PUT', f"variants/{v['id']}.json",
                    {'variant': {'id': v['id'], 'option1': newval}})
                print(f'  {key}: option1 {v["option1"]} -> {newval}')
        p = api('GET', f'products/{pid}.json')['product']

        for fname, colour in plan:
            fp = os.path.join(SCRATCH, fname)
            b64 = base64.b64encode(open(fp, 'rb').read()).decode()
            if colour is None:
                vids = [v['id'] for v in p['variants']]
            else:
                vids = [v['id'] for v in p['variants'] if v['option1'] == colour]
            img = api('POST', f'products/{pid}/images.json', {'image': {
                'attachment': b64, 'filename': fname,
                'alt': f"{ids[key]['title']}" + (f", {colour}" if colour else ''),
                'variant_ids': vids}})['image']
            print(f"  {key}: {fname} -> image {img['id']} covering {len(vids)} variant(s)")
            time.sleep(0.5)

        # verify no naked variants
        p = api('GET', f'products/{pid}.json')['product']
        naked = [v['sku'] for v in p['variants'] if not v.get('image_id')]
        print(f"{key}: {len(p['images'])} images, naked variants: {naked if naked else 'none'}")


if __name__ == '__main__':
    main()
