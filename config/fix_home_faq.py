#!/usr/bin/env python3
"""Correct the homepage FAQ to the 2026-08-04 range.

Two rows were out of date and both were actively misleading:

  f2  "Are these suitable for senior dogs?" answered "that is who the range was
      built around", which stopped being true when the Senior Dog Kit was
      retired. Replaced with the question a first-time visitor to a six-kit
      store actually has, which also happens to be the strongest AOV prompt on
      the page: which kit do I start with.

  f4  "priced below the combined cost of its four items" - kits now hold four
      OR five items. A specific number that can go stale does not belong in
      copy; the saving is already computed live on the product page.

The homepage template is the source that renders, so it is written directly;
config/build_homepage.py is updated to match so a future rebuild does not
reintroduce either row.

    python config/fix_home_faq.py            # show the diff
    python config/fix_home_faq.py --apply    # write + verify live
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = 187585560865
TEMPLATE = 'templates/index.json'

NEW = {
    'f2': ('Which kit should I start with?',
           '<p>Match it to the job in front of you. <strong>New Puppy</strong> '
           'covers the first month: crate, teething, teeth and first walks. '
           '<strong>Grooming Essentials</strong> is a full home session, coat '
           'to nails to teeth. <strong>Calm &amp; Comfort</strong> is for '
           'storms, fireworks and being left alone. <strong>Enrichment</strong> '
           'slows down dinner and gives a bored dog a job. '
           '<strong>Travel</strong> is the bag by the door, and the '
           '<strong>Toy Kit</strong> is five different games rather than five '
           'versions of the same one. Every kit costs less than buying its '
           'pieces separately.</p>'),
    'f4': ('Do the kits actually save money?',
           '<p>Yes. Each kit is priced below the combined cost of its items, '
           'and the exact saving is shown on the kit\'s own page. It also '
           'arrives as one parcel rather than several.</p>'),
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
    doc = json.loads(get_asset(TEMPLATE))
    rows = doc['sections']['faq']['blocks']['acc']['blocks']

    for key, (heading, text) in NEW.items():
        row = rows[key]
        print(f'{key}:')
        print(f'   was: {row["settings"]["heading"]}')
        print(f'        {row["blocks"]["a"]["settings"]["text"][:110]}...')
        print(f'   now: {heading}')
        print(f'        {text[:110]}...')
        row['settings']['heading'] = heading
        row['blocks']['a']['settings']['text'] = text

    body = json.dumps(doc, ensure_ascii=False, indent=1)
    for bad in ('—', '–'):
        if bad in body:
            print(f'REFUSING: template still contains {bad!r}')
            return 1

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    put_asset(TEMPLATE, body)

    # Shopify's CDN serves mixed stale/fresh renders for minutes after a theme
    # write, so verify against the ADMIN asset (authoritative) and then the
    # storefront with a cache-buster, checking every field in one response.
    fresh = json.loads(get_asset(TEMPLATE))
    live = fresh['sections']['faq']['blocks']['acc']['blocks']
    ok = all(live[k]['settings']['heading'] == NEW[k][0]
             and live[k]['blocks']['a']['settings']['text'] == NEW[k][1]
             for k in NEW)
    print('\nadmin asset verified' if ok else '\nADMIN VERIFY FAILED')
    if not ok:
        return 1

    for attempt in range(6):
        req = urllib.request.Request(
            f'https://{DOMAIN.replace(".myshopify.com", "")}'
            f'.myshopify.com/?nocache={int(time.time())}{attempt}',
            headers={'User-Agent': 'Mozilla/5.0'})
        try:
            html = urllib.request.urlopen(req, timeout=90).read().decode(
                'utf-8', 'replace')
        except Exception as exc:
            print(f'  storefront fetch failed: {str(exc)[:60]}')
            time.sleep(10)
            continue
        gone = 'suitable for senior dogs' not in html
        there = 'Which kit should I start with' in html
        if gone and there:
            print('storefront verified: new row live, senior row gone')
            return 0
        print(f'  attempt {attempt + 1}: stale render '
              f'(new={there}, old_gone={gone}), waiting')
        time.sleep(15)
    print('storefront still stale after retries; admin asset IS correct')
    return 0


if __name__ == '__main__':
    sys.exit(main())
