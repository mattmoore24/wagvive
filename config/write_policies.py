#!/usr/bin/env python3
"""Publish the store policies.

Rewritten 2026-08-04 after a full compliance review
(docs/legal-compliance-review-2026-08.md). What changed and why:

  * SHIPPING said "free over $50" while the live delivery profile charges free
    over $60. A published policy that contradicts checkout is the worst kind of
    error here: it is both a customer-service problem and, because it is a
    price representation, an FTC deception exposure. Fixed, and this script now
    refuses to publish if it disagrees with config/shipping_rates.py.
  * SHIPPING now carries the cancellation right required by the FTC Mail,
    Internet, or Telephone Order Merchandise Rule (16 CFR 435): if we cannot
    ship inside the time we stated, the buyer must be offered the choice of
    consenting to the delay or cancelling for a full refund. That right existed
    in practice; it was not written down.
  * SHIPPING now says plainly that orders ship from an overseas fulfillment
    partner. It already implied it. Saying it is both honest and the thing that
    makes a 5 to 12 business day estimate credible.
  * TERMS was twelve short paragraphs with no governing law, no warranty
    disclaimer, no liability cap, no IP clause, no user-content terms and no
    severability. Those are the clauses that do the work if anything goes
    wrong. Expanded, in the same plain voice.
  * British spellings corrected ("colour", "fulfilment"). US store, US buyers.

Deliberately NOT stated anywhere: anything about customs, duties or import
charges. The margin model assumes duties are included (DDP) but that is
UNCONFIRMED with CJ (task #64). A "no surprise charges" promise the business
cannot verify would be worse than silence.

Every figure here must match the live delivery profile, the FAQ page and the
Shipping & Returns page.
"""
import json, os, sys, urllib.error, urllib.request

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
# The only customer-facing address. Was a personal Gmail until 2026-08-02;
# re-running this script with the old value would silently reintroduce it into
# the live policies. hello@ forwards to a dedicated inbox and is the verified,
# DKIM-signed sender for all Shopify notifications.
SUPPORT_EMAIL = 'hello@wagvive.com'
# Must match config/shipping_rates.py. Enforced in main().
FREE_THRESHOLD = 60
BUSINESS_ADDRESS = 'Wagvive, 333 Pearl St, New York, NY 10038, United States'

REFUND = """<p>We want you to be happy with what you bought. If you are not, you
have <strong>30 days from delivery</strong> to start a return.</p>
<h3>What we accept</h3>
<ul>
<li>Items in unused condition, in their original packaging.</li>
<li>Returns started within 30 days of the delivery date.</li>
</ul>
<h3>Who pays for return shipping</h3>
<ul>
<li><strong>If the item arrived faulty, damaged or incorrect, we pay.</strong>
We will send a prepaid label and either replace the item or refund you in full,
your choice.</li>
<li>If you simply changed your mind, return shipping is on you.</li>
</ul>
<p>We do not charge a restocking fee.</p>
<h3>How to start a return</h3>
<p>Email <a href="mailto:{email}">{email}</a> with your order number and, if the
item arrived damaged, a photo. We reply within one business day. Please do not
send anything back before you hear from us, because we will tell you where to
send it.</p>
<h3>Exchanges</h3>
<p>The quickest way to exchange something, for a different size for example, is
to return the original for a refund and place a new order. Tell us that is what
you are doing and we will make sure the two are handled together.</p>
<h3>Refunds</h3>
<p>Once your return is received and checked, we refund to the original payment
method within 5 business days. Your bank or card issuer may take a few days
longer to show it. Original shipping charges are refunded only where the item
was faulty, damaged or incorrect.</p>
<h3>Items we cannot take back</h3>
<ul>
<li>Used grooming consumables where the seal has been broken, for hygiene
reasons (ear and dental wipes).</li>
<li>Items returned after 30 days, or without their original packaging.</li>
</ul>
<h3>Cancellations</h3>
<p>Orders can be cancelled for a full refund any time before they are
dispatched. Email us as soon as possible, because once a parcel has left the
warehouse it has to be handled as a return.</p>
<h3>If your order is delayed</h3>
<p>If we cannot ship within the time stated in our Shipping Policy, we will
contact you, and you may either agree to the new date or cancel for a full
refund.</p>
<h3>Faulty items</h3>
<p>Nothing in this policy affects your statutory rights.</p>
<h3>Questions</h3>
<p>Email <a href="mailto:{email}">{email}</a>, or write to {address}.</p>"""

SHIPPING = """<h3>Where we ship</h3>
<p>We currently ship within the <strong>United States only</strong>. We would
rather do one country properly than give the rest of the world a delivery
estimate we cannot keep.</p>
<h3>Cost</h3>
<ul>
<li><strong>Free standard shipping on orders over ${free}.</strong></li>
<li>$5.95 flat rate below that, however many items you order.</li>
</ul>
<h3>How long it takes</h3>
<ul>
<li><strong>Processing:</strong> 1 to 3 business days.</li>
<li><strong>Delivery:</strong> typically 5 to 12 business days after
dispatch.</li>
<li><strong>Tracking:</strong> emailed as soon as your parcel leaves the
warehouse.</li>
</ul>
<h3>Where your order ships from</h3>
<p>Your order is packed and dispatched by our overseas fulfillment partner and
shipped directly to you, rather than being held first in a domestic warehouse.
That is how we keep prices where they are, and it is why delivery takes longer
than a marketplace that warehouses everything. We would rather tell you that up
front than surprise you after you have paid.</p>
<h3>If your order is delayed</h3>
<p>If we cannot ship your order within the time stated above, we will contact
you with a revised date. You can either agree to the new date or
<strong>cancel for a full refund</strong>. If we cannot reach you, or you would
rather not wait, we refund you in full without you having to ask.</p>
<h3>Orders with several items</h3>
<p>If an order contains several items they may ship separately, each with its
own tracking. You are not charged twice, because the shipping you paid at
checkout covers the whole order.</p>
<h3>If something goes wrong</h3>
<p>If tracking has not moved for 7 days, or your parcel is late beyond the
window above, email <a href="mailto:{email}">{email}</a> and we will chase it.
If it is lost we will replace or refund it.</p>
<h3>Wrong address</h3>
<p>Please check your address at checkout. If you spot a mistake, email us
immediately, because we can usually correct it before dispatch. Once shipped, a
parcel sent to an address you supplied cannot be recovered.</p>
<h3>Questions</h3>
<p>Email <a href="mailto:{email}">{email}</a>, or write to {address}.</p>"""

TERMS = """<p>These terms cover your use of this website and any order you place
with Wagvive. By using the site or placing an order you accept them. Please read
them, particularly the sections on warranties and liability, which limit what we
are responsible for.</p>
<p><strong>Who we are:</strong> {address}. Contact:
<a href="mailto:{email}">{email}</a>.</p>

<h3>Who can order</h3>
<p>You must be at least 18 and able to enter a contract. By ordering you confirm
that you are.</p>

<h3>Orders</h3>
<p>An order is an offer to buy. A contract is formed when we email you to confirm
dispatch. We may decline an order, for example if an item is out of stock, if
there was a pricing error, or if we cannot deliver to your address, and if we do,
we refund you in full.</p>

<h3>Pricing</h3>
<p>Prices are in US dollars and exclude sales tax, which is calculated at
checkout where applicable. We try hard to keep prices accurate. If an item is
listed at an obviously incorrect price we will contact you before charging you,
and you may cancel. We may change prices at any time, but a change never affects
an order we have already accepted.</p>

<h3>Shipping and returns</h3>
<p>Our Shipping Policy and Refund Policy form part of these terms. If we cannot
ship within the time we stated, you may cancel for a full refund.</p>

<h3>Products</h3>
<p>Our products are pet accessories for general use. <strong>They are not
veterinary devices, and nothing on this site is veterinary advice.</strong> If
your dog has a medical condition, talk to your vet. Supervise your dog with any
new product, check it regularly, and stop using it if it becomes damaged. No pet
product is indestructible, and none is a substitute for supervision.</p>

<h3>Images and descriptions</h3>
<p>We show supplier photography alongside our own descriptions. Colors can vary
slightly between screens, and sizes are given so you can check the fit before
buying.</p>

<h3>California residents</h3>
<p>Please see our <a href="/pages/proposition-65">Proposition 65 notice</a>.</p>

<h3>Our content</h3>
<p>The text, photography, logos and design on this site belong to us or our
licensors and are protected by copyright and trademark law. You may browse,
share links, and print pages for your own use. You may not copy our content for
commercial use, or use the Wagvive name or logo, without our written
permission.</p>

<h3>Anything you send us</h3>
<p>If you send us a review, photo, comment or creator application, you keep
ownership of it, and you give us a non-exclusive, royalty-free, worldwide
license to use it to promote the store. Only send us material you have the right
to share, and that does not include anyone else's copyrighted work. We can
remove any submission. If you believe something on this site infringes your
copyright, email <a href="mailto:{email}">{email}</a> and we will act on it.</p>

<h3>Acceptable use</h3>
<p>Keep your account details secure. Do not use this site fraudulently, do not
attempt to interfere with it or with other people's use of it, and do not
scrape, resell or systematically copy its contents. We may suspend access if you
do.</p>

<h3>Links to other sites</h3>
<p>Where we link to another site, we do not control it and are not responsible
for its content or its privacy practices.</p>

<h3>Warranties</h3>
<p>We will supply your order with reasonable care and skill, and everything we
say about a product is our honest description of it. <strong>Beyond that, and to
the fullest extent the law allows, the site and the products are provided as is,
and we disclaim all implied warranties, including implied warranties of
merchantability and fitness for a particular purpose.</strong> Some states do not
allow the exclusion of implied warranties, so this may not apply to you.</p>

<h3>Liability</h3>
<p>We are responsible for foreseeable loss caused by our breaking these terms.
We are not responsible for loss that was not foreseeable, for loss caused by
misuse of a product, or for lost profits or business losses. <strong>To the
fullest extent the law allows, our total liability for any order is limited to
the amount you paid for that order.</strong> Nothing here limits liability that
cannot legally be limited, including liability for death or personal injury
caused by our negligence, or for fraud.</p>

<h3>Indemnity</h3>
<p>If your misuse of this site or breach of these terms causes a claim against
us, you agree to cover the reasonable costs of dealing with it.</p>

<h3>Events outside our control</h3>
<p>We are not liable for delays caused by events outside our reasonable control,
such as extreme weather, carrier failures, strikes, or government action. If one
happens we will tell you, and you may cancel any order that has not shipped.</p>

<h3>If we disagree</h3>
<p>Please email <a href="mailto:{email}">{email}</a> first. Almost everything is
resolved that way, quickly. If it cannot be, these terms are governed by the
laws of the State of New York, and any dispute will be handled by the state or
federal courts located in New York County, New York.</p>

<h3>Electronic communications</h3>
<p>By using the site you agree that we may communicate with you electronically,
and that emails and on-site notices satisfy any requirement that a communication
be in writing. Marketing email is separate and always optional: every marketing
message has an unsubscribe link, and unsubscribing never affects order
updates.</p>

<h3>General</h3>
<p>If any part of these terms is found unenforceable, the rest still applies.
Our not enforcing a term is not a waiver of it. We may transfer these terms if
our business is sold, and your rights are unaffected. These terms, with the
policies they refer to, are the whole agreement between us.</p>

<h3>Changes</h3>
<p>We may update these terms. The version in force is the one published when you
place your order.</p>

<h3>Contact</h3>
<p>Questions about these terms: <a href="mailto:{email}">{email}</a>, or write to
{address}.</p>"""

CONTACT = """<p>We are a small team and we answer our own email.</p>
<ul>
<li><strong>Email:</strong> <a href="mailto:{email}">{email}</a></li>
<li><strong>Response time:</strong> within one business day, from a person.</li>
<li><strong>Postal address:</strong> {address}</li>
</ul>
<p>For order questions, please include your order number. It is in your
confirmation email and starts with a #.</p>"""

POLICIES = {
    'REFUND_POLICY': REFUND,
    'SHIPPING_POLICY': SHIPPING,
    'TERMS_OF_SERVICE': TERMS,
    'CONTACT_INFORMATION': CONTACT,
}

MUTATION = """
mutation($input: ShopPolicyInput!) {
  shopPolicyUpdate(shopPolicy: $input) {
    shopPolicy { type url }
    userErrors { field message }
  }
}
"""


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def fill(body):
    return (body.replace('{email}', SUPPORT_EMAIL)
                .replace('{address}', BUSINESS_ADDRESS)
                .replace('{free}', str(FREE_THRESHOLD)))


def main():
    # The $50/$60 mismatch that this rewrite fixed came from two files holding
    # the same number. Check rather than trust.
    sys.path.insert(0, os.path.join(ROOT, 'config'))
    import shipping_rates
    if float(shipping_rates.FREE_THRESHOLD) != float(FREE_THRESHOLD):
        print(f'REFUSING: policy says free over ${FREE_THRESHOLD} but '
              f'shipping_rates.py says ${shipping_rates.FREE_THRESHOLD}',
              file=sys.stderr)
        return 1

    for ptype, body in POLICIES.items():
        res = gql(MUTATION, {'input': {'type': ptype, 'body': fill(body)}})
        if res.get('errors'):
            print(f'{ptype:24} GQL error {json.dumps(res["errors"])[:180]}')
            continue
        d = res['data']['shopPolicyUpdate']
        if d['userErrors']:
            print(f'{ptype:24} {json.dumps(d["userErrors"])[:180]}')
        else:
            print(f'{ptype:24} written -> {d["shopPolicy"]["url"]}')

    check = gql('{ shop { shopPolicies { type body } } }')
    print('\nfinal state (re-fetched):')
    bad = 0
    for p in check['data']['shop']['shopPolicies']:
        body = p['body'] or ''
        issues = []
        if 'colour' in body.lower() or 'fulfilment' in body.lower():
            issues.append('British spelling')
        if '—' in body or '–' in body:
            issues.append('em/en dash')
        if p['type'] == 'SHIPPING_POLICY' and f'${FREE_THRESHOLD}' not in body:
            issues.append(f'missing ${FREE_THRESHOLD} threshold')
        bad += len(issues)
        print(f'   {p["type"]:24} {len(body):6} chars'
              + ('  ISSUES: ' + ', '.join(issues) if issues else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
