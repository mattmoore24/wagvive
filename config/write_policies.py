#!/usr/bin/env python3
"""Publish the store policies. Only a privacy policy existed.

Shopify links these from the checkout footer and from order emails, so their
absence is visible at exactly the moment a first-time buyer is deciding whether
to trust the store. A stated refund policy is also one of the few trust signals
that reliably moves conversion, and card processors expect them to exist.

Every figure here matches what the site already promises on the FAQ and
Shipping & Returns pages and what the delivery profile actually charges - a
policy that contradicts the checkout is worse than no policy.
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
We will send a prepaid label and either replace the item or refund you in full -
your choice.</li>
<li>If you simply changed your mind, return shipping is on you.</li>
</ul>
<h3>How to start a return</h3>
<p>Email <a href="mailto:{email}">{email}</a> with your order number and, if the
item arrived damaged, a photo. We reply within one business day. Please do not
send anything back before you hear from us - we will tell you where to send it.</p>
<h3>Refunds</h3>
<p>Once your return is received and checked, we refund to the original payment
method within 5 business days. Your bank may take a few days longer to show it.
Original shipping charges are refunded only where the item was faulty, damaged or
incorrect.</p>
<h3>Items we cannot take back</h3>
<ul>
<li>Used grooming consumables where the seal has been broken, for hygiene reasons
(ear and dental wipes).</li>
<li>Items returned after 30 days, or without their original packaging.</li>
</ul>
<h3>Cancellations</h3>
<p>Orders can be cancelled for a full refund any time before they are dispatched.
Email us as soon as possible - once a parcel has left the warehouse it has to be
handled as a return.</p>
<h3>Faulty items</h3>
<p>Nothing in this policy affects your statutory rights.</p>"""

SHIPPING = """<h3>Where we ship</h3>
<p>We currently ship within the <strong>United States only</strong>. We would
rather do one country properly than give the rest of the world a delivery estimate
we cannot keep.</p>
<h3>Cost</h3>
<ul>
<li><strong>Free standard shipping on orders over $50.</strong></li>
<li>$5.95 flat rate below that.</li>
</ul>
<h3>How long it takes</h3>
<ul>
<li><strong>Processing:</strong> 1-3 business days.</li>
<li><strong>Delivery:</strong> typically 5-12 business days after dispatch.</li>
<li><strong>Tracking:</strong> emailed as soon as your parcel leaves the warehouse.</li>
</ul>
<p>We ship direct from our fulfilment partner rather than paying to hold stock in
a domestic warehouse. That keeps our prices down, and it is why delivery takes
longer than a marketplace that warehouses everything. We would rather tell you
that up front than surprise you after you have paid.</p>
<h3>Orders with several items</h3>
<p>If an order contains several items they may ship separately, each with its own
tracking. You are not charged twice - the shipping you paid at checkout covers
the whole order.</p>
<h3>If something goes wrong</h3>
<p>If tracking has not moved for 7 days, or your parcel is late beyond the window
above, email <a href="mailto:{email}">{email}</a> and we will chase it. If it is
lost we will replace or refund it.</p>
<h3>Wrong address</h3>
<p>Please check your address at checkout. If you spot a mistake, email us
immediately - we can usually correct it before dispatch. Once shipped, a parcel
sent to an address you supplied cannot be recovered.</p>"""

TERMS = """<p>These terms cover your use of this website and any order you place
with Wagvive. By placing an order you accept them.</p>
<h3>Orders</h3>
<p>An order is an offer to buy. A contract is formed when we email you to confirm
dispatch. We may decline an order - for example if an item is out of stock, if
there was a pricing error, or if we cannot deliver to your address - and if we do,
we refund you in full.</p>
<h3>Pricing</h3>
<p>Prices are in US dollars and exclude sales tax, which is calculated at
checkout where applicable. We try hard to keep prices accurate. If an item is
listed at an obviously incorrect price we will contact you before charging you,
and you may cancel.</p>
<h3>Products</h3>
<p>Our products are pet accessories for general use. They are not veterinary
devices and nothing on this site is veterinary advice. If your dog has a medical
condition, talk to your vet. Supervise your dog with any new product, and stop
using it if it becomes damaged.</p>
<h3>Images and descriptions</h3>
<p>We show supplier photography alongside our own descriptions. Colors can vary
slightly between screens, and sizes are given so you can check the fit before
buying.</p>
<h3>Returns</h3>
<p>See our Refund Policy, which forms part of these terms.</p>
<h3>Liability</h3>
<p>We are responsible for foreseeable loss caused by our breaking these terms. We
are not responsible for loss that was not foreseeable, or for misuse of a product.
Nothing here limits liability that cannot legally be limited.</p>
<h3>Your account and conduct</h3>
<p>Keep your account details secure. Do not use this site fraudulently or in a way
that disrupts it for others.</p>
<h3>Changes</h3>
<p>We may update these terms. The version in force is the one published when you
place your order.</p>
<h3>Contact</h3>
<p>Questions about these terms: <a href="mailto:{email}">{email}</a>.</p>"""

CONTACT = """<p>We are a small team and we answer our own email.</p>
<ul>
<li><strong>Email:</strong> <a href="mailto:{email}">{email}</a></li>
<li><strong>Response time:</strong> within one business day, from a person.</li>
</ul>
<p>For order questions, please include your order number - it is in your
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


def main():
    for ptype, body in POLICIES.items():
        res = gql(MUTATION, {'input': {'type': ptype,
                                       'body': body.replace('{email}', SUPPORT_EMAIL)}})
        if res.get('errors'):
            print(f'{ptype:24} GQL error {json.dumps(res["errors"])[:180]}'); continue
        d = res['data']['shopPolicyUpdate']
        if d['userErrors']:
            print(f'{ptype:24} {json.dumps(d["userErrors"])[:180]}')
        else:
            print(f'{ptype:24} written -> {d["shopPolicy"]["url"]}')

    check = gql('{ shop { shopPolicies { type body } } }')
    print('\nfinal state:')
    for p in check['data']['shop']['shopPolicies']:
        print(f'   {p["type"]:24} {len(p["body"] or "")} chars')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
