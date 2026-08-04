#!/usr/bin/env python3
"""
Replace Wagvive placeholder illustrations with real CJ supplier photos
for the 6 SKUs that have usable imagery.

Nail grinder and comfort bed are deliberately skipped: every image in their
CJ galleries is either cat-focused or carries burned-in marketing text.
"""
import base64, json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, 'config', 'branding', 'cj-raw')

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'], env['SHOPIFY_API_VERSION']

# product id -> (alt text, [image files in gallery order])
PLAN = {
    10456336990497: ('Wagvive Self-Cleaning Slicker Brush',
                     ['slicker_01.jpg', 'slicker_03.jpg']),
    10456337056033: ('Wagvive Grooming & Shedding Gloves',
                     ['gloves_05.jpg', 'gloves_07.png']),
    10456337154337: ('Wagvive Ear & Teeth Cleaning Wipes',
                     ['wipes_08.jpg', 'wipes_09.jpg']),
    10456337383713: ('Wagvive Cooling Comfort Mat',
                     ['mat_15.jpg']),
    10456337547553: ('Wagvive Anti-Spill Floating Water Bowl',
                     ['bowl_19.jpg']),
    10456337613089: ('Wagvive Slow Feeder Bowl',
                     ['feeder_20.jpg', 'feeder_21.jpg']),
}


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or '{}')


def main():
    for pid, (alt, files) in PLAN.items():
        paths = [os.path.join(RAW, f) for f in files]
        missing = [p for p in paths if not os.path.exists(p)]
        if missing:
            print(f'SKIP {pid}: missing {missing}')
            continue

        for img in api('GET', f'products/{pid}/images.json').get('images', []):
            api('DELETE', f'products/{pid}/images/{img["id"]}.json')

        for n, p in enumerate(paths, 1):
            with open(p, 'rb') as fh:
                b64 = base64.b64encode(fh.read()).decode()
            res = api('POST', f'products/{pid}/images.json', {'image': {
                'attachment': b64,
                'filename': os.path.basename(p),
                'alt': alt if n == 1 else f'{alt} - detail',
                'position': n}})
            i = res['image']
            print(f'  {os.path.basename(p):20} -> {pid}  {i["width"]}x{i["height"]}')
        print(f'OK  {alt}\n')

    print('Skipped (no clean CJ imagery available):')
    print('  10456337318177  Quiet Electric Nail Grinder  - all shots are text-overlay marketing slides')
    print('  10456337711393  Calming Comfort Bed          - entire gallery is cat-focused + size text')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, e.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
