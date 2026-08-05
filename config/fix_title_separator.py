#!/usr/bin/env python3
"""Remove the en dashes from the <title> tag builder.

`snippets/meta-tags.liquid` builds every page title as:

    {{ seo_title }} &ndash; tagged "..."   (tag pages)
    {{ seo_title }} &ndash; Page N         (paginated)
    {{ seo_title }} &ndash; {{ shop.name }}

so an en dash appears in the browser tab, the search result, the shared link
preview and the Pinterest pin title of **every page on the site**. That is the
single most visible place house style could be broken, and it survived the
2026-08-04 dash sweep because that sweep checked rendered body copy, where the
`<title>` element does not appear.

Replaced with a pipe, which is what the homepage SEO title already uses
("Wagvive | Premium Dog Toys, Grooming & Enrichment Kits"), so the whole site
now separates title parts the same way.

    python config/fix_title_separator.py            # show the diff
    python config/fix_title_separator.py --apply    # write + verify live
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = 187585560865
SNIPPET = 'snippets/meta-tags.liquid'
PROBE = 'wagvive-cooling-comfort-pad'

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


def get_asset(key):
    q = urllib.parse.urlencode({'asset[key]': key})
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json?{q}',
        headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())['asset']['value']


def put_asset(key, value):
    body = json.dumps({'asset': {'key': key, 'value': value}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json',
        data=body, method='PUT',
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def main():
    apply = '--apply' in sys.argv
    src = get_asset(SNIPPET)

    hits = list(re.finditer(r'&ndash;|&mdash;|—|–', src))
    print(f'{len(hits)} dash(es) in {SNIPPET}:')
    for m in hits:
        a, b = max(0, m.start() - 70), min(len(src), m.end() + 60)
        print(f'   ...{re.sub(chr(92) + "s+", " ", src[a:b])}...')
    if not hits:
        print('  none; nothing to do')
        return 0

    new = src.replace('&ndash;', '|').replace('&mdash;', '|')
    new = new.replace('—', '|').replace('–', '|')

    remaining = re.findall(r'&ndash;|&mdash;|—|–', new)
    if remaining:
        print(f'REFUSING: {len(remaining)} dash(es) survive the replacement')
        return 1
    print('\nall dashes replaced with a pipe, matching the homepage SEO title')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    put_asset(SNIPPET, new)

    # Read back with retries. A read issued immediately after the PUT can
    # return the PREVIOUS version of the asset, which made the first run of
    # this script report a failure on a write that had actually succeeded.
    for attempt in range(5):
        fresh = get_asset(SNIPPET)
        if not re.search(r'&ndash;|&mdash;|—|–', fresh):
            print(f'admin asset verified: snippet is dash free '
                  f'(read {attempt + 1})')
            break
        time.sleep(4)
    else:
        print('ADMIN VERIFY FAILED: dashes still present after retries')
        return 1

    # The <title> element is not inside any renderable section, so the section
    # rendering API cannot see it. Full page fetch is the only option here.
    for attempt in range(8):
        try:
            req = urllib.request.Request(
                f'https://wagvive.com/products/{PROBE}?nocache={int(time.time())}',
                headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req, timeout=90).read().decode(
                'utf-8', 'replace')
        except Exception as exc:
            print(f'  fetch failed: {str(exc)[:60]}')
            time.sleep(10)
            continue
        m = re.search(r'<title>(.*?)</title>', html, re.S)
        title = m.group(1).strip() if m else ''
        if title and not re.search(r'&ndash;|&mdash;|—|–', title):
            print(f'live title verified: {title!r}')
            return 0
        print(f'  attempt {attempt + 1}: still {title!r}, waiting')
        time.sleep(15)
    print('live page still cached; the ADMIN asset IS correct')
    return 0


if __name__ == '__main__':
    sys.exit(main())
