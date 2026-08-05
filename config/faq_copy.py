#!/usr/bin/env python3
"""
FAQ page copy.

Reviewed 2026-08-04. Changes from the previous version:
  * "Are these suitable for senior dogs?" removed. It claimed the range was
    designed around senior dogs, which is no longer the positioning. Replaced
    with a question about who the range suits, which keeps the genuinely
    useful part (the quiet tools suit nervous and older dogs) without making
    it the pitch.
  * "What size dog do these fit?" referenced "the bed", which the store does
    not sell. Rewritten to point at the per-product size guides added on
    2026-08-04.
  * Added: shipping cost, cancellations, heavy chewers, washing. Shipping cost
    and cancellations were both answered on the Shipping & Returns page but
    missing here, which is where people look first.
  * Kit swap answer clarified: colors ARE selectable, products are not
    interchangeable. The old wording read as though nothing could be chosen.

Everything here must stay consistent with the Shipping & Returns page:
1 to 3 business days processing, 5 to 12 business days delivery, free
shipping over $60 and $5.95 below, 30 day returns, cancel before dispatch.

NOT ANSWERED HERE, DELIBERATELY: customs and duties. The margin model assumes
duties are included (DDP) but that is unconfirmed with CJ, tracked as task
#64. Do not add a "no surprise charges" answer until that is settled, because
it would be a promise the business cannot currently verify.
"""

BODY = """<h2>Ordering and delivery</h2>

<h3>How long will my order take?</h3>
<p>Processing takes 1 to 3 business days, then typically 5 to 12 business days
to arrive in the US. You'll get tracking by email the moment it ships. Full
detail on our <a href="/pages/shipping-returns">Shipping &amp; Returns</a>
page.</p>

<h3>What does shipping cost?</h3>
<p>Standard shipping is free on orders over $60. Below that it is a $5.95 flat
rate, however many items you order.</p>

<h3>Why does shipping take longer than Amazon?</h3>
<p>We ship direct from our fulfilment partner rather than paying to hold stock
in a domestic warehouse. That keeps our prices lower. We'd rather be upfront
about the tradeoff than surprise you at checkout.</p>

<h3>Do you ship outside the US?</h3>
<p>Not yet. We're starting in the US so we can keep delivery estimates honest.
Join the list on our homepage and we'll tell you when that changes.</p>

<h3>Can I track my order?</h3>
<p>Yes, a tracking link is emailed as soon as your parcel is dispatched. If an
order contains several items, they may ship separately with their own
tracking.</p>

<h3>Can I cancel or change an order?</h3>
<p>Yes, any time before it is dispatched, for a full refund. Email
<a href="mailto:hello@wagvive.com">hello@wagvive.com</a> with your order number
and we'll sort it. Once tracking has been issued it becomes a return
instead.</p>

<h2>Choosing the right thing</h2>

<h3>Who is this range for?</h3>
<p>Everyday dogs and the people who live with them, at any age. A few things
are worth knowing: the grooming tools were picked to be quiet and low
vibration, which helps with nervous dogs, and several of the comfort items
come in sizes that go from a crate floor up to a large sofa. Nothing here
needs a particular breed or life stage.</p>

<h3>How do I pick the right size?</h3>
<p>Anything sold in sizes has a size guide on its own product page, with the
measurements in inches and centimetres and a note on which dogs each size
suits. As a general rule, for pads and blankets measure your dog from nose to
base of tail while they are lying down and add a few inches. For the bath
robe, go by weight. For the sofa cover, measure the seat area rather than the
dog. When your dog falls between two sizes, choose the larger one.</p>

<h3>Will the toys survive a heavy chewer?</h3>
<p>Mostly no, and we'd rather say so. The plush and rope toys are built for
play, carrying and squeaking, not for a dog who systematically destroys
things. Individual product pages say where a toy is not suited to serious
chewing. The rubber and latex chews hold up better.</p>

<h3>Is the nail grinder loud?</h3>
<p>It's built to be quiet, which is the main reason we picked it. Most dogs
that panic at clippers tolerate a grinder far better. Start it near them
without touching a nail for the first few sessions.</p>

<h3>How often should I use the wipes?</h3>
<p>For teeth, a few times a week beats a perfect daily routine you abandon. For
ears, once a week is plenty for most dogs, though floppy eared breeds and
swimmers often need it more often. If you see persistent redness, discharge or
odour, that's a vet visit, not a wipe.</p>

<h2>Looking after it</h2>

<h3>Can the blankets, pads and covers be washed?</h3>
<p>Yes. The blankets, sofa cover and cooling pad are all machine washable. Wash
cool, and skip the tumble dryer on anything with a waterproof layer so the
backing lasts. Care detail is on each product page.</p>

<h2>Returns and support</h2>

<h3>What if I don't like it?</h3>
<p>You have 30 days from delivery. If it arrived faulty or wrong, we cover
return shipping and replace or refund it. If you simply changed your mind,
return shipping is on you.</p>

<h3>How do I reach a human?</h3>
<p>Email <a href="mailto:hello@wagvive.com">hello@wagvive.com</a>. We reply
within one business day, and it's a person, not a bot.</p>

<h2>The bundles</h2>

<h3>Is the kit actually cheaper?</h3>
<p>Yes. Each kit is priced below the total of buying its four items separately.
The saving is shown on the product page.</p>

<h3>Can I choose the colors in a kit?</h3>
<p>Yes. Each kit lets you pick the color or character of every item in it,
using the dropdowns on the product page. What you can't do is swap one product
for a different one. If you only want part of a kit, buying the individual
items works out simplest.</p>"""
