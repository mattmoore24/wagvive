#!/usr/bin/env python3
"""Take dashes-as-punctuation out of the customer-facing copy.

Em dashes read as machine-written to a lot of people now, so they go. Three
distinct uses needed three different fixes rather than one blanket replace:

  1. Bullet separators   "<strong>Dental wipes</strong> - the bit that gets
                          skipped"  ->  a colon
  2. Number ranges       "5-12 business days" with an en dash  ->  "5 to 12"
  3. Prose dashes        an em dash joining two clauses  ->  a comma when the
                          second half is a fragment, a full stop when it is an
                          independent clause. A blanket comma would leave comma
                          splices, which reads worse than the dash did.

Hyphens INSIDE words are left alone. "Self-cleaning", "anti-spill",
"Rope-Limb" and "30-day" are ordinary English, and stripping them would break
product names and make the copy wrong rather than human.

Theme Liquid is deliberately untouched: nearly every " - " in it is CSS calc()
or Liquid arithmetic, and rewriting those would break the storefront.
"""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request

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

DASH = r'(?:—|–|&mdash;|&ndash;|-)'

# Prose replacements, longest first so partials cannot fire early. Each was
# chosen for what the second clause actually is.
PROSE = [
    ("drink — without the mess", "drink, without the mess"),
    ("or on the go — ideal for senior dogs", "or on the go. Ideal for senior dogs"),
    ("Contact cooling — works as soon as", "Contact cooling that works as soon as"),
    ("weighs almost nothing — easy to take along",
     "weighs almost nothing, so it is easy to take along"),
    ("scaled down for cats — the smallest option",
     "scaled down for cats. The smallest option"),
    ("no brushing standoff — for most dogs",
     "no brushing standoff. For most dogs"),
    ("single button press — no pulling fur",
     "single button press, with no pulling fur"),
    ("with a brush handle - and most dogs",
     "with a brush handle, and most dogs"),
    ("a sherpa border - soft on both sides",
     "a sherpa border, soft on both sides"),
    ("novelty wears off - and they are the part",
     "novelty wears off, and they are the part"),
    ("versions of the same thing - something to squeak",
     "versions of the same thing. Something to squeak"),
    ("something to throw - so there is always",
     "something to throw, so there is always"),
    ("and grooming — the parts of pet care",
     "and grooming. These are the parts of pet care"),
    ("everyday pet care — and you'd genuinely use products like ours — we'd love",
     "everyday pet care, and you would genuinely use products like ours, we would love"),
    ("scripted reads — we want your honest take",
     "scripted reads. We want your honest take"),
    ("Can I track my order? Yes — a tracking link",
     "Can I track my order? Yes. A tracking link"),
    ("easier mealtimes — the things that matter",
     "easier mealtimes. These are the things that matter"),
    ("come in size options — check the individual",
     "come in size options, so check the individual"),
    ("that's a vet visit — not a wipe", "that's a vet visit, not a wipe"),
    ("it's a person — not a bot", "it's a person, not a bot"),
    ("four items separately — the saving is shown",
     "four items separately. The saving is shown"),
    ("in a domestic warehouse — which keeps costs down",
     "in a domestic warehouse, which keeps costs down"),
    ("That's normal — each tracking number",
     "That's normal. Each tracking number"),
    ("or full refund — your choice", "or full refund, whichever you prefer"),
    ("in one box — priced below buying", "in one box, priced below buying"),
    ("feel gentle — so brushing", "feel gentle, so brushing"),
    ("easy to add on — pick any three", "easy to add on. Pick any three"),
    ("your order number - it is in your confirmation",
     "your order number, which is in your confirmation"),
    ("refund you in full - your choice", "refund you in full, whichever you prefer"),
    ("hear from us - we will tell you", "hear from us, because we will tell you"),
    ("as soon as possible - once a parcel", "as soon as possible. Once a parcel"),
    ("not charged twice - the shipping you paid",
     "not charged twice, because the shipping you paid"),
    ("email us immediately - we can usually correct it",
     "email us immediately, because we can usually correct it"),
    ("decline an order - for example", "decline an order, for example"),
    ("deliver to your address - and if we do",
     "deliver to your address, and if we do"),
    ("Any <strong>3 toys</strong> &mdash; <strong>15% off</strong>",
     "Any <strong>3 toys</strong>, <strong>15% off</strong>"),
]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def clean(text):
    t = text or ''
    if not t:
        return t
    for old, new in PROSE:
        t = t.replace(old, new)
    # bullet separators after a bolded label
    t = re.sub(r'(</strong>)\s*' + DASH + r'\s+', r'\1: ', t)
    # number ranges, including the degree range on the cooling pad
    t = re.sub(r'(\d)\s*(?:–|&ndash;)\s*(\d)', r'\1 to \2', t)
    # anything left that is a dash used as punctuation, never one inside a word
    t = re.sub(r'\s+(?:—|–|&mdash;|&ndash;)\s+', ', ', t)
    t = re.sub(r'(?<=[a-z,;])\s+-\s+(?=[a-z])', ', ', t)
    return t


def main():
    changed = 0

    for p in api('GET', 'products.json?limit=250&status=active')['products']:
        new = clean(p.get('body_html'))
        if new != (p.get('body_html') or ''):
            api('PUT', f'products/{p["id"]}.json',
                {'product': {'id': p['id'], 'body_html': new}})
            print(f'product     {p["handle"]}'); changed += 1

    for pg in api('GET', 'pages.json?limit=250')['pages']:
        new = clean(pg.get('body_html'))
        if new != (pg.get('body_html') or ''):
            api('PUT', f'pages/{pg["id"]}.json',
                {'page': {'id': pg['id'], 'body_html': new}})
            print(f'page        {pg["handle"]}'); changed += 1

    for kind, key in (('custom_collections', 'custom_collection'),
                      ('smart_collections', 'smart_collection')):
        for c in api('GET', f'{kind}.json?limit=50')[kind]:
            new = clean(c.get('body_html'))
            if new != (c.get('body_html') or ''):
                api('PUT', f'{kind[:-1]}s/{c["id"]}.json',
                    {key: {'id': c['id'], 'body_html': new}})
                print(f'collection  {c["handle"]}'); changed += 1

    pols = gql('{ shop { shopPolicies { type body } } }')['data']['shop']['shopPolicies']
    for p in pols:
        new = clean(p['body'])
        if new != (p['body'] or ''):
            gql("""mutation($input: ShopPolicyInput!){
                     shopPolicyUpdate(shopPolicy:$input){ userErrors{ message } } }""",
                {'input': {'type': p['type'], 'body': new}})
            print(f'policy      {p["type"]}'); changed += 1

    # only my own snippets, and only their visible strings
    theme = next(t for t in api('GET', 'themes.json')['themes'] if t['role'] == 'main')
    for key in ('snippets/toy-deal.liquid', 'snippets/kit-callout.liquid',
                'snippets/cart-cross-sell.liquid', 'snippets/toy-progress.liquid',
                'snippets/free-shipping-progress.liquid'):
        q = urllib.parse.quote(key)
        val = api('GET', f'themes/{theme["id"]}/assets.json?asset[key]={q}'
                  )['asset'].get('value') or ''
        new = val
        for old, rep in PROSE:
            new = new.replace(old, rep)
        new = new.replace('&mdash;', ',').replace('&ndash;', ' to ')
        if new != val:
            api('PUT', f'themes/{theme["id"]}/assets.json',
                {'asset': {'key': key, 'value': new}})
            print(f'snippet     {key}'); changed += 1

    print(f'\n{changed} item(s) rewritten')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
