#!/usr/bin/env python3
"""Correct two fall descriptions that did not match the actual product.

Both were caught by opening the CJ photography at full size, which is the only
check that catches this class of error: the option values and the listing title
were both consistent with what I wrote.

  * Thanksgiving Turkey Coat. I called it "a lapel coat" with a "retro lapel
    collar". It is a KNIT SWEATER with a mock neck and ribbed trim. The three
    designs are real (argyle Plaid, embroidered BOO, Turkey) but the garment
    type was wrong.
  * Glow in the Dark Skeleton Suit. Its four sizes are SMALL BREED sizing. CJ's
    own copy says "your small dog" and "your puppy's comfort". Saying only "four
    sizes, small through extra large" invites a labrador owner to buy it. The
    Pumpkin Hoodie (XS-9XL) and Big Dog Costume (3XL-8XL) are pointed at instead.
"""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for line in open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8'):
    line = line.strip()
    if line and '=' in line:
        k, v = line.split('=', 1)
        env[k] = v
D, T, V = env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'], env['SHOPIFY_API_VERSION']

FIX = {
 'wagvive-thanksgiving-turkey-coat': {
  'title': 'Wagvive Thanksgiving Turkey Sweater',
  'seo_title': 'Thanksgiving Dog Sweater, Turkey, Boo and Argyle',
  'body': """<p><strong>One sweater, the whole of autumn.</strong></p>
<p>A chunky knit with a mock neck and ribbed trim, in three designs, so it covers
Halloween and Thanksgiving without buying twice.</p>
<ul>
<li>Turkey for Thanksgiving, an embroidered Boo for Halloween, and a mustard
argyle for every day in between</li>
<li>Ribbed collar, cuffs and hem in contrast colour</li>
<li>Four sizes, small through extra large</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},
 'wagvive-glow-skeleton-suit': {
  'body': """<p><strong>It glows once the sun goes down.</strong></p>
<p>A black four leg suit with a bone print that charges in daylight and glows on
the evening walk, which is exactly when everyone is out looking at dogs.</p>
<ul>
<li>Soft brushed knit, pulls on over the head</li>
<li>Ribbed neck and cuffs so it stays put</li>
<li><strong>Cut for small dogs.</strong> Sizes S to XL here run small, so this
suits chihuahuas, dachshunds, terriers and similar. For anything bigger see the
Pumpkin Hoodie, which runs XS to 9XL, or the Big Dog Costume at 3XL to 8XL</li>
</ul>
<p><strong>Arrives in 5 to 12 business days.</strong></p>"""},
}


def api(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    rq = urllib.request.Request(f'https://{D}/admin/api/{V}/{path}', data=data,
                                method=method,
                                headers={'X-Shopify-Access-Token': T,
                                         'Content-Type': 'application/json'})
    raw = urllib.request.urlopen(rq, timeout=180).read().decode()
    time.sleep(0.6)
    return json.loads(raw) if raw.strip() else {}


def main():
    apply = '--apply' in sys.argv
    for handle, fix in FIX.items():
        ps = api(f'products.json?handle={handle}&limit=1&status=active')['products']
        if not ps:
            print(f'{handle}: not found'); continue
        p = ps[0]
        print(f"\n{p['title']}")
        for k in ('title', 'body'):
            if k in fix:
                print(f'  {k}: updating')
        if not apply:
            continue
        payload = {'product': {'id': p['id'], 'body_html': fix['body']}}
        if 'title' in fix:
            payload['product']['title'] = fix['title']
        api(f"products/{p['id']}.json", 'PUT', payload)
        if 'seo_title' in fix:
            mfs = api(f"products/{p['id']}/metafields.json")['metafields']
            m = next((x for x in mfs if x['namespace'] == 'global'
                      and x['key'] == 'title_tag'), None)
            if m:
                api(f"metafields/{m['id']}.json", 'PUT',
                    {'metafield': {'id': m['id'], 'value': fix['seo_title'],
                                   'type': 'string'}})
        print('  written')
    if not apply:
        print('\nDry run. Use --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
