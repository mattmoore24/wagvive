#!/usr/bin/env python3
"""
Find every place the storefront makes a factual claim that is now wrong.

Three drifted:
  supplier   - "one vetted supplier" is false now that sourcing spans CJ in-house,
               Manifest Store LLC and (potentially) others
  shipping   - copy promises "$5.95 flat, free over $60"; live rates are
               $8.00 and free over $70
  transit    - copy promises 5-11 business days; the carriers actually quoted
               run 7-14 and up to 10-23 days
  archived   - links or names referring to the archived mat / bed / Comfort kit
"""
import json, os, re, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise as DP  # noqa: E402

PATTERNS = {
    'supplier': re.compile(r'(one vetted supplier|single (audited|vetted) (partner|supplier)|'
                           r'one (audited|vetted) partner|same supplier|single supplier)', re.I),
    'shipping': re.compile(r'(\$5\.95|\$8\.00|free (?:US )?shipping over \$\d+|over \$60|over \$70)', re.I),
    # Every promise this store has retired, built from delivery_promise.RETIRED
    # so a future change adds one line there instead of editing a regex here.
    # The old pattern hunted a hard-coded "5-11" and ALSO matched any hyphenated
    # "N-N business days", so it flagged the current wording as a violation
    # while missing the "1 to 3" spelled with the word "to".
    'transit': re.compile('|'.join(re.escape(r) for r in DP.RETIRED)
                          + r'|\d+\s*[-–]\s*\d+\s*business days', re.I),
    'archived': re.compile(r'(calming comfort bed|orthopedic comfort bed|cooling comfort mat|'
                           r'comfort-health-kit|comfort & health kit)', re.I),
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
THEME = 187585560865


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def strip(html):
    t = re.sub(r'<[^>]+>', ' ', html or '')
    return re.sub(r'\s+', ' ', t)


def scan(source, text):
    hits = []
    for name, pat in PATTERNS.items():
        for m in pat.finditer(text):
            start = max(0, m.start() - 70)
            hits.append((name, m.group(0), text[start:m.end() + 70].strip()))
    if hits:
        print(f'\n=== {source} ===')
        seen = set()
        for name, found, ctx in hits:
            key = (name, found.lower())
            if key in seen:
                continue
            seen.add(key)
            print(f'  [{name:9}] {found!r}')
            print(f'              ...{ctx}...')


def main():
    # pages
    for p in api('pages.json?limit=50')['pages']:
        scan(f'page: {p["title"]} (/{p["handle"]})', strip(p.get('body_html')))

    # products
    for p in api('products.json?limit=250')['products']:
        scan(f'product: {p["title"]} [{p["status"]}]', strip(p.get('body_html')))

    # theme templates and sections
    assets = api(f'themes/{THEME}/assets.json')['assets']
    keys = [a['key'] for a in assets
            if a['key'].startswith(('templates/', 'sections/', 'locales/', 'snippets/'))
            and a['key'].endswith(('.json', '.liquid'))]
    for k in keys:
        try:
            v = api(f'themes/{THEME}/assets.json?asset[key]={k}')['asset'].get('value')
        except urllib.error.HTTPError:
            continue
        if not v:
            continue
        scan(f'theme: {k}', re.sub(r'\s+', ' ', v))


if __name__ == '__main__':
    main()
