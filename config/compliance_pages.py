#!/usr/bin/env python3
"""Publish the compliance pages the store was missing, and fix two stale ones.

From the 2026-08-04 compliance review
(docs/legal-compliance-review-2026-08.md):

  NEW /pages/proposition-65
      California requires a clear and reasonable warning BEFORE a Californian
      is exposed to a listed chemical. Our goods are imported pet accessories,
      largely plastics and textiles from China, and imported goods are not
      Prop 65 compliant by default. We have neither test reports nor supplier
      certificates, so we cannot say a warning is unnecessary. This page gives
      the warning site-wide. It is the honest, low-cost position while the
      supplier evidence is collected.
      NOTE FOR THE OWNER: a site-wide page is the weaker form of compliance.
      The stronger form is a warning on the affected product pages, which
      requires knowing WHICH products are affected, which requires either lab
      testing or written supplier certificates. See the review document.

  NEW /pages/accessibility
      Ecommerce sites are 69 to 77 percent of US digital accessibility suits,
      Shopify stores are about a third of platform-specific ones, and 64
      percent of defendants are under $25M revenue. A statement is not a
      defence, but having a named contact and a stated standard is the first
      thing a demand letter looks for, and it is how a real user tells us
      something is broken.

  FIX /pages/creator-affiliate-program
      Had no disclosure requirement at all. Under the FTC Endorsement Guides
      (16 CFR 255) an endorser must disclose a material connection, and the
      BRAND is exposed for failing to instruct and monitor its affiliates.
      Also still pitched "senior pet care", which the range stopped being
      about when the Senior Dog Kit was retired.

  FIX /pages/faq and /pages/shipping-returns
      British "fulfilment" and "odour", plus the stale $50 free-shipping
      figure if present.

    python config/compliance_pages.py            # report
    python config/compliance_pages.py --apply    # write + verify
"""
import json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPPORT_EMAIL = 'hello@wagvive.com'

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
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


PROP65 = """<p><strong>WARNING:</strong> These products can expose you to
chemicals including lead and di(2-ethylhexyl)phthalate (DEHP), which are known
to the State of California to cause cancer and birth defects or other
reproductive harm. For more information go to
<a href="https://www.P65Warnings.ca.gov" rel="nofollow noopener"
target="_blank">www.P65Warnings.ca.gov</a>.</p>

<h3>Why you are seeing this</h3>
<p>California's Proposition 65 requires businesses to give a warning before
knowingly exposing people in California to any of about 900 listed chemicals.
The list is long and the thresholds are low, so warnings appear on a very wide
range of ordinary goods, including many pet accessories, cables, bags and
homeware.</p>
<p>Our products are imported pet accessories, mostly plastics, silicone and
textiles. We do not currently hold chemical test reports for every item, and we
would rather warn you than quietly assume the answer is no. This warning is
given for our full range.</p>

<h3>What it does not mean</h3>
<p>It is not a finding that a product is unsafe, and it is not a recall or a
safety notice. A Proposition 65 warning means a listed chemical may be present
above California's threshold, which is set far below the level at which harm
has been observed. It is a disclosure requirement, not a safety verdict.</p>

<h3>Sensible use</h3>
<p>As we say in our Terms, supervise your dog with any new product, check it
regularly for damage, and replace anything that is coming apart. Wash hands
after handling. Keep products away from small children, who put things in their
mouths for longer and are more affected by the chemicals on this list.</p>

<h3>Questions</h3>
<p>Email <a href="mailto:{email}">{email}</a> and we will tell you what we know
about a specific item, including what we have asked our supplier for.</p>"""

ACCESSIBILITY = """<p>We want anyone to be able to use this store, including
people using a screen reader, keyboard navigation, magnification, or voice
control.</p>

<h3>What we aim for</h3>
<p>We work towards the Web Content Accessibility Guidelines (WCAG) 2.1 at Level
AA. That covers things like text contrast, keyboard access to every control,
alternative text on images, labelled form fields, and a page structure that
makes sense when it is read aloud.</p>

<h3>Where we are honest about it</h3>
<p>We are a small store and we do not claim the site is perfect. Parts of it
come from our theme and from third party tools, and those can change under us.
Where we know something falls short, we fix it rather than describe it away.</p>

<h3>Tell us if something does not work</h3>
<p>This is the part that actually matters. If any page, product, or step of
checkout is difficult or impossible to use, email
<a href="mailto:{email}">{email}</a>. Tell us the page and what happened, and
what you were using if you know it, for example a screen reader and browser. We
reply within one business day and we will help you complete your order over
email in the meantime.</p>

<h3>If you would rather just order by email</h3>
<p>Email us the products you want and a delivery address, and we will send a
secure payment link. You do not have to fight with a web page to buy something
from us.</p>"""

CREATOR = """<p>We are looking for pet content creators who care about the
everyday reality of living with a dog: grooming, comfort, play, and the small
problems that come up every week.</p>
<p>If you make content about dogs and you would genuinely use products like
ours, we would love to work with you.</p>

<h3>What you get</h3>
<ul>
<li>A commission on the sales you drive, paid monthly.</li>
<li>Free product to work with, and early access to new products.</li>
<li>Creative freedom. We are not looking for scripted reads. We want your
honest take, including when the honest take is that something is not for
everyone.</li>
</ul>

<h3>What we ask</h3>
<ul>
<li><strong>Disclose the relationship, every time.</strong> If we pay you, give
you commission, or send you free product, that has to be clear in the post
itself, not only in a bio or a linked page. On video, say it out loud and put it
on screen. Plain words work best: "paid partnership with Wagvive", "Wagvive sent
me this", or "commission link". This is the FTC's Endorsement Guides, it applies
to you and to us, and we take it seriously.</li>
<li><strong>Only say what is true.</strong> Say what you actually experienced.
Do not claim a product treats, prevents or cures any medical or behavioural
condition, and do not describe results that are not typical as if they
were.</li>
<li><strong>Own what you post.</strong> Use your own footage and music, or
material you are licensed to use.</li>
<li>Follow the rules of whichever platform you are posting on.</li>
</ul>
<p>We review what our partners post. If a post does not carry a clear
disclosure, we will ask you to fix it, and we will end the partnership if it
keeps happening. That protects you as much as us.</p>

<h3>Apply</h3>
<p>Tell us about yourself and your content using the form below: your handles,
roughly how many followers you have, and links to a few recent posts. We
personally review every application and follow up by email.</p>"""

PAGES = {
    'proposition-65': ('California Proposition 65 Notice', PROP65),
    'accessibility': ('Accessibility', ACCESSIBILITY),
    'creator-affiliate-program': ('Creator & Affiliate Program', CREATOR),
}

# Spelling and stale-figure repairs on pages we are not fully rewriting.
REPAIRS = [('fulfilment', 'fulfillment'), ('Fulfilment', 'Fulfillment'),
           ('odour', 'odor'), ('Odour', 'Odor'),
           ('centre', 'center'), ('Centre', 'Center'),
           ('colour', 'color'), ('Colour', 'Color'),
           ('over $50', 'over $60')]


def main():
    apply = '--apply' in sys.argv
    existing = {p['handle']: p for p in api('GET', 'pages.json?limit=250')['pages']}

    print('--- pages to write ---')
    for handle, (title, body) in PAGES.items():
        state = 'UPDATE' if handle in existing else 'CREATE'
        print(f'  {state}  /{handle:32} {title}')

    print('\n--- spelling and figure repairs ---')
    repairs = {}
    for handle, p in existing.items():
        if handle in PAGES:
            continue
        body = p.get('body_html') or ''
        new = body
        for a, b in REPAIRS:
            new = new.replace(a, b)
        if new != body:
            hits = [a for a, _ in REPAIRS if a in body]
            repairs[handle] = (p['id'], new)
            print(f'  /{handle:32} {hits}')
    if not repairs:
        print('  none')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    print('\n--- writing ---')
    for handle, (title, body) in PAGES.items():
        payload = {'page': {'title': title, 'handle': handle,
                            'body_html': body.replace('{email}', SUPPORT_EMAIL),
                            'published': True}}
        if handle in existing:
            payload['page']['id'] = existing[handle]['id']
            api('PUT', f'pages/{existing[handle]["id"]}.json', payload)
            print(f'  updated /{handle}')
        else:
            r = api('POST', 'pages.json', payload)
            print(f'  created /{handle} -> {r["page"]["id"]}')
        time.sleep(0.55)

    for handle, (pid, new) in repairs.items():
        api('PUT', f'pages/{pid}.json', {'page': {'id': pid, 'body_html': new}})
        print(f'  repaired /{handle}')
        time.sleep(0.55)

    # verify against the live system
    print('\n--- verify ---')
    fresh = {p['handle']: p for p in api('GET', 'pages.json?limit=250')['pages']}
    bad = 0
    for handle in list(PAGES) + list(repairs):
        p = fresh.get(handle)
        if not p:
            print(f'  MISSING /{handle}')
            bad += 1
            continue
        body = p.get('body_html') or ''
        issues = [w for w in ('colour', 'fulfilment', 'odour', 'over $50')
                  if w in body.lower()]
        if '—' in body or '–' in body:
            issues.append('em dash')
        bad += len(issues)
        print(f'  {"OK " if not issues else "BAD"} /{handle:32} '
              f'{len(body):5} chars {issues if issues else ""}')

    for handle in ('proposition-65', 'accessibility'):
        for attempt in range(4):
            try:
                req = urllib.request.Request(
                    f'https://wagvive.com/pages/{handle}?nocache={int(time.time())}',
                    headers={'User-Agent': 'Mozilla/5.0'})
                html = urllib.request.urlopen(req, timeout=60).read().decode(
                    'utf-8', 'replace')
                if 'P65Warnings' in html or 'WCAG' in html:
                    print(f'  storefront OK /pages/{handle}')
                    break
            except Exception as exc:
                print(f'  /{handle} fetch: {str(exc)[:50]}')
            time.sleep(10)
        else:
            print(f'  /{handle} not confirmed on storefront yet')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
