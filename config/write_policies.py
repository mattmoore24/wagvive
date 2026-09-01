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
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise  # noqa: E402  the single source of the delivery numbers

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

# The postal address is FETCHED from Shopify at publish time, not hardcoded.
# A constant here drifted once already: it said "333 Pearl St" while the store
# address is "333 Pearl St, 18H", so every published policy carried an
# incomplete address. Policies are plain HTML, so unlike the marketing emails
# they cannot use {{ shop.address.summary }} and must be resolved on publish.
BUSINESS_ADDRESS = None      # set by fetch_business_address()


def fetch_business_address():
    """'Wagvive, 333 Pearl St, 18H, New York, NY 10038, United States'."""
    q = ('{shop{name billingAddress{address1 address2 city provinceCode zip '
         'country}}}')
    shop = gql(q)['data']['shop']
    a = shop['billingAddress']
    parts = [shop['name'], a['address1']]
    if a.get('address2'):
        parts.append(a['address2'])
    parts.append(a['city'])
    parts.append(f"{a['provinceCode']} {a['zip']}")
    parts.append(a['country'])
    return ', '.join(p for p in parts if p)

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
<p>Orders can be cancelled for a full refund any time before the parcel is
handed to the carrier. That is usually several days after you order, and it is
later than the point where your order is marked fulfilled, so it is worth
asking even if you have already had a confirmation email. Email us as soon as
you can. Once the parcel is genuinely on its way it has to be handled as a
return.</p>
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
<li><strong>Dispatch:</strong> {dispatch}. Most orders leave sooner.</li>
<li><strong>Delivery:</strong> {window} from the day you order.</li>
<li><strong>Tracking:</strong> emailed when your parcel is handed to the
carrier. It can be quiet for the first week or so while your order is being
packed, which is normal and not a sign anything is wrong.</li>
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
<p>Tracking that has not moved for a few days is normal while your order is
being packed, so please do not worry about that on its own. If your parcel is
late beyond the window above, or tracking has not moved for 10 days after you
received it, email <a href="mailto:{email}">{email}</a> and we will chase it.
If it is lost we will replace or refund it.</p>
<h3>Wrong address</h3>
<p>Please check your address at checkout. If you spot a mistake, email us
immediately, because we can usually correct it before dispatch. Once shipped, a
parcel sent to an address you supplied cannot be recovered.</p>
<h3>Questions</h3>
<p>Email <a href="mailto:{email}">{email}</a>, or write to {address}.</p>"""

TERMS = """<p>These terms are a legal agreement between you and Wagvive. They
cover your use of this website and any order you place with us. By using the
site or placing an order you accept them.</p>

<div style="border:2px solid #3A3026; padding:14px 16px; margin:18px 0;">
<p><strong>PLEASE READ THIS NOTICE CAREFULLY.</strong> These terms contain a
<strong>binding arbitration agreement</strong> and a <strong>class action
waiver</strong>. They affect how disputes between us are resolved. Unless you
opt out within 30 days as described in the Dispute Resolution section, you and
Wagvive agree that disputes will be resolved by individual arbitration, and
<strong>you give up the right to a jury trial and the right to participate in a
class action</strong>. See the section titled "Dispute resolution and binding
arbitration" for the full terms and for how to opt out.</p>
</div>

<p><strong>Who we are:</strong> {address}. Contact:
<a href="mailto:{email}">{email}</a>.</p>

<h3>Who can order</h3>
<p>You must be at least 18 and able to enter a binding contract. By ordering you
confirm that you are. If you are ordering on behalf of a business, you confirm
you are authorized to bind it.</p>

<h3>Orders</h3>
<p>An order is an offer to buy. A contract is formed when we email you to confirm
dispatch. We may decline or cancel an order, in whole or in part, for any lawful
reason, including if an item is out of stock, if there was a pricing or
description error, if we suspect fraud or resale, or if we cannot deliver to your
address. If we cancel an order you have paid for, we refund you in full.</p>

<h3>Pricing and errors</h3>
<p>Prices are in US dollars and exclude sales tax, which is calculated at
checkout where applicable. We try hard to keep prices, descriptions and
availability accurate, but the site may contain typographical errors,
inaccuracies or omissions. <strong>We reserve the right to correct any error and
to change or update information at any time without notice, including after you
have submitted an order.</strong> If an item is listed at an obviously incorrect
price we will contact you before charging you, and you may cancel.</p>

<h3>Shipping and returns</h3>
<p>Our Shipping Policy and Refund Policy form part of these terms. If we cannot
ship within the time we stated, you may cancel for a full refund.</p>

<h3>Products, supervision and assumption of risk</h3>
<p>Our products are pet accessories for general use. <strong>They are not
veterinary devices, they are not safety equipment, and nothing on this site is
veterinary or medical advice.</strong> If your dog has a medical or behavioral
condition, talk to your vet.</p>
<p>You acknowledge and accept the following, which are ordinary facts of dog
ownership rather than defects:</p>
<ul>
<li><strong>Supervision is required.</strong> Supervise your dog with any new
product. No pet product is indestructible and none is a substitute for
supervision.</li>
<li><strong>Inspect and replace.</strong> Check products regularly and stop using
and discard anything that is damaged, worn, or coming apart. Damaged toys can
present a choking or ingestion hazard.</li>
<li><strong>Chewing habits vary.</strong> Toys are not rated for destructive or
power chewers unless expressly stated. Choose products appropriate to your dog's
size, strength and habits.</li>
<li><strong>Fit is your choice.</strong> Sized products carry a fit guide taken
from actual measurements. Selecting the right size is your responsibility, and
we will help if you ask before ordering.</li>
<li><strong>Individual reactions vary.</strong> Dogs differ in sensitivity and
tolerance. Discontinue use if your dog reacts badly to any product.</li>
</ul>
<p>To the fullest extent the law allows, you assume the risks described above.</p>

<h3>Images and descriptions</h3>
<p>We show supplier photography alongside our own descriptions. Colors can vary
slightly between screens, and sizes are given so you can check the fit before
buying.</p>

<h3>California residents</h3>
<p>Please see our <a href="/pages/proposition-65">Proposition 65 notice</a>.</p>

<h3>Our content</h3>
<p>The text, photography, logos and design on this site belong to us or our
licensors and are protected by copyright and trademark law. You may browse,
share links, and print pages for your own personal, non-commercial use. You may
not copy, reproduce, scrape, republish or use our content commercially, or use
the Wagvive name or logo, without our written permission.</p>

<h3>Anything you send us</h3>
<p>If you send us a review, photo, comment or creator application, you keep
ownership of it, and you grant us a non-exclusive, royalty-free, worldwide,
perpetual, sublicensable license to use, reproduce, adapt and display it to
operate and promote the store. You confirm you own or control the rights to
anything you send, that it does not include anyone else's copyrighted work or
likeness without permission, and that it is not unlawful or misleading. We may
remove any submission for any reason.</p>
<p><strong>Copyright complaints.</strong> If you believe material on this site
infringes your copyright, email <a href="mailto:{email}">{email}</a> with the
work concerned, the location on our site, your contact details, and a statement
that you have a good faith belief the use is unauthorized. We will act on
properly made notices, including removing material and terminating repeat
infringers.</p>

<h3>Acceptable use</h3>
<p>Keep your account details secure; you are responsible for activity under your
account. Do not use this site fraudulently, do not attempt to interfere with it
or with anyone else's use of it, do not attempt to gain unauthorized access, and
do not scrape, data-mine, resell or systematically copy its contents. We may
suspend or terminate access, and cancel orders, if you do.</p>

<h3>Links to other sites</h3>
<p>Where we link to another site, we do not control it and are not responsible
for its content, products or privacy practices.</p>

<h3>Warranties</h3>
<p>We will supply your order with reasonable care and skill, and everything we
say about a product is our honest description of it. <strong>BEYOND THAT, AND TO
THE FULLEST EXTENT PERMITTED BY LAW, THE SITE AND THE PRODUCTS ARE PROVIDED "AS
IS" AND "AS AVAILABLE", AND WE DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED,
INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE, TITLE AND NON-INFRINGEMENT.</strong> We do not warrant that the site
will be uninterrupted or error free. Some states do not allow the exclusion of
implied warranties, so parts of this may not apply to you.</p>

<h3>Limitation of liability</h3>
<p>We are responsible for foreseeable loss caused by our breaking these terms.
<strong>TO THE FULLEST EXTENT PERMITTED BY LAW, WE ARE NOT LIABLE FOR INDIRECT,
INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY OR PUNITIVE DAMAGES, OR FOR LOST
PROFITS, LOST DATA, OR BUSINESS LOSSES, EVEN IF WE HAVE BEEN ADVISED OF THE
POSSIBILITY. OUR TOTAL LIABILITY ARISING OUT OF OR RELATING TO ANY ORDER OR YOUR
USE OF THE SITE IS LIMITED TO THE GREATER OF THE AMOUNT YOU PAID FOR THE ORDER
GIVING RISE TO THE CLAIM, OR ONE HUNDRED US DOLLARS.</strong></p>
<p>Nothing in these terms limits liability that cannot legally be limited,
including liability for death or personal injury caused by our negligence, or for
fraud or fraudulent misrepresentation. Some states do not allow certain
limitations, so parts of this may not apply to you.</p>

<h3>Indemnification</h3>
<p>You agree to indemnify and hold harmless Wagvive and its officers, employees
and agents from any claim, loss, liability or reasonable cost arising out of your
misuse of this site, your breach of these terms, or your violation of any law or
the rights of a third party.</p>

<h3>Events outside our control</h3>
<p>We are not liable for delay or failure caused by events outside our reasonable
control, including extreme weather, carrier failure, strikes, epidemic, war,
government action, customs delay, or supplier or platform outage. If one happens
we will tell you, and you may cancel any order that has not shipped.</p>

<h3>Dispute resolution and binding arbitration</h3>
<p><strong>Please read this section carefully. It affects your legal rights,
including your right to file a lawsuit in court and to have a jury decide your
claim.</strong></p>

<p><strong>1. Informal resolution first.</strong> Most problems can be sorted out
quickly. Before starting arbitration, you agree to email
<a href="mailto:{email}">{email}</a> describing the dispute and the resolution
you want, and to give us <strong>60 days</strong> to resolve it. We agree to do
the same before bringing a claim against you. This step is a condition of
starting arbitration, and the time limit for bringing a claim pauses while it
runs.</p>

<p><strong>2. Agreement to arbitrate.</strong> If we cannot resolve it, you and
Wagvive agree that any dispute, claim or controversy <strong>arising out of or
relating to these terms, your purchases from us, or your use of this
site</strong> will be resolved by <strong>binding individual arbitration</strong>
rather than in court, except as stated in paragraph 3. This agreement is governed
by the Federal Arbitration Act.</p>

<p><strong>3. Exceptions.</strong> Either of us may bring an individual claim in
<strong>small claims court</strong> if it qualifies. Either of us may also ask a
court for an injunction or other equitable relief to protect intellectual
property or to stop unauthorized use of the site. Nothing here prevents you from
reporting a matter to a government agency.</p>

<p><strong>4. Class action and jury waiver.</strong>
<strong>ARBITRATION WILL BE ON AN INDIVIDUAL BASIS ONLY. YOU AND WAGVIVE WAIVE
THE RIGHT TO A JURY TRIAL AND THE RIGHT TO BRING OR PARTICIPATE IN ANY CLASS,
COLLECTIVE, CONSOLIDATED OR REPRESENTATIVE ACTION.</strong> The arbitrator may
not consolidate more than one person's claims or preside over any form of
class proceeding. If this paragraph is found unenforceable as to a particular
claim, then that claim alone is severed from arbitration and proceeds in court,
and the rest of this section still applies to all other claims.</p>

<p><strong>5. How arbitration works.</strong> Arbitration is administered by the
<strong>American Arbitration Association</strong> under its Consumer Arbitration
Rules, available at adr.org. The arbitrator is bound by these terms. Filing and
arbitrator fees are governed by the AAA consumer fee schedule, which caps what a
consumer pays. Arbitration will be held in the county where you live, or by
telephone or video, or on documents alone, at your choice. The arbitrator may
award any relief a court could award to you individually, and the award may be
entered as a judgment in any court with jurisdiction.</p>

<p><strong>6. Coordinated filings.</strong> If 25 or more similar arbitration
demands are filed against us by or with the assistance of the same law firm or
coordinated group, the AAA will administer them in batches of no more than 50,
with a single arbitrator per batch and a single set of filing fees per batch, and
the time limit for bringing a claim pauses for all claims in the queue until
their batch is resolved. This is intended to keep costs proportionate for
everyone, not to delay any individual claim.</p>

<p><strong>7. Who decides what.</strong> The arbitrator decides all issues,
including the scope, interpretation and enforceability of this arbitration
agreement, <strong>except</strong> that a court decides any challenge to the
class action waiver in paragraph 4.</p>

<p><strong>8. Your right to opt out.</strong> <strong>You can opt out of this
arbitration agreement.</strong> Email <a href="mailto:{email}">{email}</a> with
the subject line "Arbitration opt-out" within <strong>30 days</strong> of your
first purchase, including your name and the email address on your order. Opting
out costs you nothing, does not affect your order, your returns, or anything
else in these terms, and we will not treat you differently for it. If you opt
out, disputes are resolved in court as described under Governing law.</p>

<p><strong>9. Survival.</strong> This section survives the end of your
relationship with us.</p>

<h3>Time limit for claims</h3>
<p>To the fullest extent permitted by law, any claim arising out of or relating
to these terms or your purchases must be brought within <strong>one year</strong>
after it arises, or it is permanently barred. Some states do not allow this
limit, so it may not apply to you.</p>

<h3>Governing law and venue</h3>
<p>These terms are governed by the laws of the State of New York, without regard
to its conflict of law rules. For any dispute not subject to arbitration, you and
Wagvive agree to the exclusive jurisdiction of the state and federal courts
located in New York County, New York, and waive any objection to that venue.
Nothing here deprives you of the protection of mandatory consumer laws of the
state where you live.</p>

<h3>Electronic communications</h3>
<p>By using the site you agree that we may communicate with you electronically,
and that emails and on-site notices satisfy any legal requirement that a
communication be in writing. You consent to the use of electronic records and
signatures. Marketing email is separate and always optional: every marketing
message has an unsubscribe link, and unsubscribing never affects order
updates.</p>

<h3>Changes to these terms</h3>
<p>We may update these terms. The version in force for an order is the one
published when you place it. Material changes take effect for future orders, and
continuing to use the site after a change means you accept the updated terms.</p>

<h3>General</h3>
<p>If any part of these terms is found unenforceable, the rest still applies, and
the unenforceable part is limited to the minimum extent necessary. Our not
enforcing a term is not a waiver of it. You may not assign these terms; we may
assign them if our business is sold, and your rights are unaffected. These terms,
with the policies they refer to, are the entire agreement between us and replace
any earlier understanding. Sections covering content, acceptable use, warranties,
liability, indemnification, arbitration, time limits and governing law survive
termination. Headings are for convenience only. There are no third-party
beneficiaries. Notices to us go to <a href="mailto:{email}">{email}</a> or
{address}; notices to you go to the email on your order.</p>

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
    # The delivery numbers come from config/delivery_promise.py, never from a
    # literal typed here. That module carries the reasoning and the sample the
    # numbers were derived from; a literal in this file would drift from it the
    # way "1 to 3 business days" drifted from a dispatch step measured at 4.9,
    # 8.8 and 11 days.
    return (body.replace('{email}', SUPPORT_EMAIL)
                .replace('{address}', BUSINESS_ADDRESS)
                .replace('{free}', str(FREE_THRESHOLD))
                .replace('{window}', delivery_promise.WINDOW)
                .replace('{dispatch}', delivery_promise.DISPATCH_WINDOW))


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

    global BUSINESS_ADDRESS
    BUSINESS_ADDRESS = fetch_business_address()
    print(f'business address from Shopify: {BUSINESS_ADDRESS}\n')

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
