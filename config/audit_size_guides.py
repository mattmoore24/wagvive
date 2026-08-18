#!/usr/bin/env python3
"""Every product that asks for a size must say which dog each size fits.

This is a gate, not a report. It exists because the failure it catches is
invisible from the admin: a product can be active, stocked, imaged, correctly
priced and paired to CJ, and still be unbuyable in practice because the shopper
cannot tell whether their dog is a Medium.

WHAT IT CHECKS, and why each rule is here rather than a looser one:

  1. A guide exists at all. Nine of fifteen products had nothing.
  2. Every value of the Size option appears as a row. A guide covering four of
     thirteen sizes is worse than none, because it reads complete.
  3. The guide carries real MEASUREMENTS with units, not adjectives. "Cut for
     small dogs" passed every eye that looked at the Skeleton Suit for weeks.
  4. It does not carry a bare weight range as its only number. This is the
     specific shape of the bug that put a 2x error on the Quick-Dry Bath Robe
     for as long as it was live: a weight-only table looks authoritative, and
     nothing in it can be cross-checked. A girth or a length is falsifiable
     against the garment, so at least one is required.

Rule 4 has two deliberate exemptions, both stated rather than special cased
quietly: the Sofa & Furniture Cover is sized to furniture, and the Paw Washing
Cup is sized to a paw. Neither has a body measurement to give and pretending
otherwise is what this audit is trying to prevent.

    python config/audit_size_guides.py           # report, exits non-zero on a gap
    python config/audit_size_guides.py --json    # also write a qa log
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

# A length in inches or centimetres, single or range: "13 in", "17.7 to 21.7 in".
LENGTH = re.compile(r'\d+(?:\.\d+)?\s*(?:to\s*\d+(?:\.\d+)?\s*)?(?:in\b|cm\b)',
                    re.I)
WEIGHT = re.compile(r'\d+(?:\.\d+)?\s*to\s*\d+(?:\.\d+)?\s*(?:lb|kg)\b', re.I)
# Products where a body measurement genuinely does not apply. See the docstring.
NO_BODY_MEASURE = {
    'wagvive-waterproof-sofa-furniture-cover': 'sized to the furniture',
    'wagvive-paw-washing-cup': 'sized to the paw, not the body',
}


def api(path):
    req = urllib.request.Request(f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
                                 headers={'X-Shopify-Access-Token': TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    time.sleep(0.55)
    return out


def text(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment)))


def main():
    prods = api('products.json?limit=250&status=active')['products']
    sized = [p for p in prods
             if any(o['name'].lower() == 'size' for o in p['options'])]
    if not sized:
        print('no active product takes a size, which is itself suspicious')
        return 1

    log, bad = [], []
    for p in sorted(sized, key=lambda x: x['title']):
        body = p.get('body_html') or ''
        opt = next(o for o in p['options'] if o['name'].lower() == 'size')
        faults = []

        m = re.search(r'<div class="wagvive-size-guide">.*?</div>', body, re.S)
        if not m:
            faults.append('no size guide')
            guide = ''
        else:
            guide = m.group(0)
            # Strip the <style> block first: its CSS contains "1px" and "100%",
            # which would otherwise read as measurements and pass rule 3 for a
            # table that has none.
            plain = text(re.sub(r'<style>.*?</style>', ' ', guide, flags=re.S))

            uncovered = [v for v in opt['values']
                         if v.lower() not in plain.lower()]
            if uncovered:
                faults.append(f'{len(uncovered)} size(s) not in the table: '
                              f'{", ".join(uncovered)}')

            lengths = LENGTH.findall(plain)
            if not lengths:
                faults.append('no measurement with units anywhere')
            elif (p['handle'] not in NO_BODY_MEASURE
                  and not re.search(r'girth|back length|chest|neck', plain, re.I)):
                faults.append('measurements present but none is a body '
                              'measurement (girth, chest, neck or back length)')

            if WEIGHT.search(plain) and not lengths:
                faults.append('weight only, with nothing checkable against '
                              'the product')

        mark = 'ok' if not faults else '; '.join(faults)
        print(f"{p['title'][:44]:46} {len(opt['values']):2d} sizes  {mark}")
        log.append({'product': p['title'], 'handle': p['handle'],
                    'sizes': opt['values'], 'faults': faults,
                    'exempt': NO_BODY_MEASURE.get(p['handle'])})
        if faults:
            bad.append(p['title'])

    print('\n' + '=' * 72)
    print(f'{len(sized)} products take a size, {len(sized) - len(bad)} carry a '
          f'complete measurement guide')
    for h, why in NO_BODY_MEASURE.items():
        print(f'  exempt from the body measurement rule: {h} ({why})')

    if '--json' in sys.argv:
        out = os.path.join(ROOT, 'docs', 'qa',
                           f'size-guides-{time.strftime("%Y-%m-%d")}.json')
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(log, fh, indent=1, ensure_ascii=False)
        print(f'log -> {os.path.relpath(out, ROOT)}')

    if bad:
        print(f'\n{len(bad)} product(s) need a size guide:')
        for t in bad:
            print(f'  ! {t}')
        return 1
    print('\nEvery size product tells the shopper which dog each size fits.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
