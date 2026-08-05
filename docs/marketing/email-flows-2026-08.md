# The five email flows

Phase 0.5 of `docs/marketing-plan-2026-08.md`. Drafted 2026-08-05, **not yet
built**. Copy is ready to paste; the build itself is admin-UI work.

Why this is worth doing before any paid traffic: flows are about 5% of sends and
41% of email revenue, at roughly 18 times the per-recipient value of campaigns.
They cost nothing, and they have to exist *before* the first Pinterest visitor
arrives rather than after. Abandoned checkout works from order one regardless of
how small the list is.

Shopify's native automations are used throughout. Klaviyo is not justified under
about $500K of revenue and would be a monthly cost against a $300 total budget.

---

## Two things to settle before building

### 1. The welcome offer: use 10%, and here is the corrected reasoning

**I got this wrong first time and then checked it properly. The correction is
below and it changes the recommendation.**

The marketing plan calls for "one welcome code at 10 to 15%". My first pass ran
that through `cac_ceiling.py` and reported that a blanket code sends four
singles negative at 10% and nine at 15%. That is what the script says, and the
script is not wrong, but **it is the wrong model for this question**.

`cac_ceiling.py` computes contribution as `price x (1 - fee) - landed - flat`.
It deliberately ignores the **$5.95 the customer pays for shipping on any order
under $60**, because for its actual purpose, deciding what a cold ad click can
cost, shipping revenue is not something an ad buys. For a discount question it
matters, because it is real money arriving on exactly the orders a discount
touches.

Rerun with shipping revenue counted, on a one-item order shipped alone:

| Welcome code | Contribution as `cac_ceiling` models it | With the $5.95 actually collected |
|---|---|---|
| none | $4.71 average, 0 negative | $10.48 average, 0 negative |
| 10% off everything | $3.02 average, **4 negative** | **$8.80 average, 0 negative** |
| 15% off everything | $2.18 average, **9 negative** | **$7.96 average, 0 negative** |

**Nothing goes negative at either rate.** The margin-protection argument for
restricting the code does not survive contact with the real order total. Scratch
it.

What does survive is one hard constraint and one soft preference.

**Hard: do not use 15%.** It drops the Grooming Essentials Kit from $70 to
**$59.50**, under the $60 free-shipping threshold. The customer either loses
free shipping at the final step, which is where carts die, or we absorb $5.95
and turn a 15% discount into an effective 24% one. At 10% the same kit lands at
$63.00 and stays safe. That is the whole reason to pick 10% over 15%, and it is
a better reason than the one I gave first.

**Soft: whether to restrict it to kits at all.**

| | Unrestricted 10% | Kits only, 10% |
|---|---|---|
| Anything lose money? | No | No |
| Checkout friction | None | "Code not valid for these items" on a single-item basket, which is a conversion killer at the worst moment |
| AOV | Lower | Higher |
| Strategy | Neutral | Reinforces that kits are the offer |

**Revised recommendation: 10% off the whole order, one use per customer, no
minimum, no collection restriction.** The welcome flow's job is to convert a
first order at all. Telling a new subscriber their code does not apply, at the
payment step, costs more than the AOV it protects. Nothing loses money either
way, so the simpler one wins.

If you would rather push AOV and keep the kits-only discipline, the restricted
version is defensible and every kit clears comfortably:

| Kit | Full | With 10% | Contribution | Over $60? |
|---|---|---|---|---|
| Calm & Comfort | $109.00 | $98.10 | $32.48 | yes |
| Travel | $85.00 | $76.50 | $24.11 | yes |
| Grooming Essentials | $70.00 | $63.00 | $22.98 | yes |
| New Puppy | $54.00 | $48.60 | $25.37 | under either way |
| Toy | $49.00 | $44.10 | $21.43 | under either way |
| Dog Enrichment | $46.00 | $41.40 | $12.29 | under either way |

**Tell me which and I will create it.** Either way the copy in flow 1 needs one
word changed: "10% off any Wagvive kit" becomes "10% off your first order" if
you go unrestricted.

**One interaction to know about.** The live automatic discount *"Any 3 toys, 15%
off"* has `combinesWith.orderDiscounts = true`, so an order-level welcome code
**stacks** with it. A 3-toy basket would take 15% then another 10%, about 23.5%
off. I checked all 455 possible 3-toy baskets at that stacked rate: the worst
still returns **$13.07** of contribution. It is safe, just worth knowing it can
happen rather than discovering it in a report.

### 2. The abandoned checkout duplicate, and what I can actually confirm

There are **two separate systems** in Shopify that both send an abandoned
checkout email, and they do not know about each other.

| | System A, live today | System B, flow 2 below |
|---|---|---|
| Where it lives | Settings › Notifications › Abandoned checkout | Marketing › Automations |
| What it is | One email, one send, fixed template | A sequence with delays and branching |
| Its on/off switch | Settings › Checkout › Abandoned checkouts | The automation's own toggle |
| Our template | `config/email-templates/abandoned-checkout.liquid`, brand-matched | Built in the section editor from the copy below |
| Default timing | 10 hours after abandonment | 1h, 24h, 72h as drafted |

**What I have verified:** the branded template exists in the repo, and
`docs/HANDOFF.md` records that all 18 notification templates were installed. So
system A's template is in place.

**What I cannot verify from here, and neither can any API:** whether system A is
actually *sending*. The Settings › Checkout › Abandoned checkouts toggle is not
exposed in the Admin API at all. I checked.

**What is most likely:** Shopify enables abandoned checkout emails by default on
new stores, at 10 hours. Nothing in the repo records anyone turning it off. So
assume it is on until you look.

**Why it matters:** switch on flow 2 with system A still sending and every
abandoning customer gets our first recovery email twice, once at 1 hour and once
at 10 hours, in two different designs. That is not a small cosmetic problem. It
is the single most valuable email we send, arriving twice, looking like a shop
that cannot count.

**What to do, in this order:**

1. Open **Settings › Checkout**, scroll to Abandoned checkouts, and tell me what
   it currently says. Thirty seconds, and it settles the question.
2. Set it to **"Don't automatically send"**.
3. Then build and enable flow 2.

The template stays installed and does no harm switched off. If you ever want to
go back to the single email, the toggle is all that changes.

---

## Facts every email must stay inside

Checked against the live store on 2026-08-05, not from memory.

| | |
|---|---|
| Delivery promise | 1 to 3 business days to dispatch, then 5 to 12 business days |
| Free shipping | over $60, otherwise $5.95 |
| Returns | 30 days from delivery. Faulty or wrong: we pay return shipping. Changed your mind: customer pays return postage. |
| Support address | hello@wagvive.com, the only address that ever appears |
| Reviews | **none yet.** No email may imply otherwise. |
| Style | US spelling, no em or en dashes, no hyphenated day ranges, plain language |

The no-reviews point is a real constraint on the copy, not a formality. Every
welcome sequence template on the internet leans on social proof at email three.
We do not have any, so email three earns its place a different way, on the
specificity of the kit contents.

---

## Flow 1. Welcome, 3 emails

**Trigger:** customer subscribes (footer form).
**Goal:** first order, and set the expectation that we sell kits.

### 1.1, immediate

**Subject:** Your 10% is inside
**Alt subject to test:** Welcome to Wagvive. Here is your 10%
**Preview:** Good for any kit, and it does not expire quietly.

> Thanks for joining.
>
> Here is 10% off any Wagvive kit. Use **WELCOME10** at checkout.
>
> A quick word on how we put things together. Most dog gear is sold one piece at
> a time, which means you find out at home that the brush is wrong for the coat,
> or the mat does not fit the crate. We build kits instead, so the things that
> get used together arrive together and are chosen to work together.
>
> Six kits, from $46. Free shipping over $60.
>
> [Shop the kits]
>
> Questions about any of it, just reply. It reaches a person at
> hello@wagvive.com.

**CTA link:** `/collections/bundles-kits` with UTM
`?utm_source=email&utm_medium=email&utm_campaign=welcome_1`

### 1.2, two days later

**Subject:** Why we do not sell a 47 piece grooming set
**Preview:** Short version: you would use four of them.

> There is a particular kind of dog product that exists only because it looks
> good in a photo. The 47 piece grooming set. The toy bundle padded out with
> things no dog has ever chosen.
>
> We went the other way. Every kit is four or five items, and each one has to
> earn its place by being the thing you actually reach for.
>
> The Grooming Essentials Kit is the self-cleaning slicker brush, the quiet nail
> grinder, the finger toothbrush, the paw washing cup and the quick-dry bath
> robe. Wash, dry, brush, nails, teeth. That is the whole routine and nothing
> else.
>
> The New Puppy Kit is five things the first month genuinely needs, not the
> twelve a checklist tells you to buy: something to chew that is not your shoes,
> something to sleep on, something to cuddle, the waste bag dispenser you will
> use twice a day, and a finger toothbrush to start the habit early.
>
> Your 10% is still good. **WELCOME10**
>
> [See what is in each kit]

**CTA link:** `/collections/bundles-kits`, campaign `welcome_2`

### 1.3, five days after signup

**Subject:** The one for thunder season
**Preview:** Heartbeat toy, compression wrap, cooling mat, fleece.
**Send rule:** skip if they have ordered.

> If your dog is the one who finds the bathtub during a storm, this is the kit
> that was built for them.
>
> **The Calm & Comfort Kit, $109**
>
> - A heartbeat plush sloth that mimics a resting dog, for crates and first
>   nights
> - A compression wrap, the same principle as a weighted blanket
> - A cooling mat, because panting dogs overheat before they settle
> - A paw print fleece blanket that carries your scent from the sofa to the crate
> - A big squeak plush, for the part of the evening where the answer is
>   distraction rather than calm
>
> Storms, fireworks, car trips, the first week alone in a new house. It is the
> same problem each time and it responds to the same five things.
>
> With **WELCOME10** that is $98.10, and shipping is free.
>
> [See the Calm & Comfort Kit]
>
> If a different kit fits better, they are all here. And if you would rather we
> stopped emailing, the unsubscribe link is at the bottom and we will not take
> it personally.

**CTA link:** `/products/calm-comfort-kit`, campaign `welcome_3`

---

## Flow 2. Abandoned checkout, 3 emails

**Trigger:** checkout started, not completed.
**Turn off the Settings › Checkout email first. See above.**
**Goal:** recover the order. Highest value flow in ecommerce.

The sequence deliberately does not lead with a discount. Discounting at email
one trains people to abandon, and it gives away margin on customers who were
coming back anyway.

### 2.1, one hour later

**Subject:** You left something behind
**Preview:** Still saved, still in stock.

> Your basket is still here.
>
> [Basket contents, Shopify inserts these]
>
> [Finish checking out]
>
> Nothing is reserved, so if it is a kit that is moving we would not leave it
> too long. Any questions before you buy, reply to this and it reaches
> hello@wagvive.com.

### 2.2, twenty four hours later

**Subject:** Anything we can answer?
**Preview:** Shipping, sizing and returns, in one place.

> Still thinking it over. That is fair, so here are the three things people
> usually want to know before a first order with a shop they have not used.

> **When does it arrive?** We dispatch in 1 to 3 business days and delivery
> takes 5 to 12 business days after that. Tracking is emailed as soon as it
> ships. We do not pretend to be two day shipping, because we are not.
>
> **What if it is wrong?** 30 days from delivery. If it is faulty, damaged or
> not what you ordered, we pay the return shipping and you choose a replacement
> or a refund. Changed your mind is fine too, return postage is on you in that
> case.
>
> **What if the size is off?** Every sized product has a fit guide on its page,
> written from the actual measurements rather than small, medium and large.
> If you are between sizes, reply and tell us the breed and weight and we will
> tell you which one.
>
> [Finish checking out]

### 2.3, seventy two hours later

**Subject:** Last reminder, then we will stop
**Preview:** Your basket, and 10% if it helps.
**Send rule:** include the code only if the customer has not already used one.

> This is the last one about this basket, promise.
>
> If price was the sticking point, **WELCOME10** takes 10% off any kit.
>
> [Finish checking out]
>
> And if you decided against it, that is genuinely fine. If something on the
> site was confusing or a question went unanswered, we would rather hear it than
> not. hello@wagvive.com

---

## Flow 3. Browse abandonment, 1 email

**Trigger:** viewed a product, did not add to cart.
**Delay:** 4 hours.
**Goal:** bring back a warm visitor without being creepy about it.

One email only. Two feels like surveillance for something they merely looked at.

**Subject:** Still thinking about the [product]?
**Preview:** Here is what is in it, in case that helps.

> You had a look at **[product]** earlier.
>
> [Product image, title, price]
>
> If it was the details you wanted, they are all on the page: what is included,
> the measurements, and who it suits.
>
> [Take another look]
>
> If it was not quite right, the six kits are here and they cover fairly
> different problems: grooming, travel, a new puppy, enrichment, toys, and
> anxiety.
>
> [See all six kits]

---

## Flow 4. Post-purchase, 2 emails

**Trigger:** order fulfilled.
**Goal:** reduce returns and support load, then earn the first reviews.

This flow matters more than usual for us, because our delivery window is long
and the gap between paying and receiving is where anxiety and refund requests
live.

### 4.1, one day after fulfillment

**Subject:** On its way, and how to get the most from it
**Preview:** Tracking, timing, and a few things worth knowing.

> Your order is on the move. Tracking is in your shipping confirmation.
>
> **Timing.** 5 to 12 business days from dispatch. Tracking can look quiet for
> the first few days while the parcel moves between carriers. That is normal and
> not a lost parcel.
>
> **When it lands.** Introduce anything new gradually. A few short, calm
> sessions beat one long one, and that goes double for grooming tools and for
> anything a dog is expected to wear.
>
> Anything at all, reply to this. hello@wagvive.com

### 4.2, day 21

**Subject:** How is it going?
**Preview:** Two minutes, and it genuinely helps a new shop.

> Your order should have arrived and had a couple of weeks of real use, which is
> about when you know whether something works.
>
> Would you leave a short review? We are new, we have no reviews yet, and
> yours would be one of the first. That is worth more to a shop this size than
> anything we could pay for.
>
> [Leave a review]
>
> And if something did not work out, please tell us before you tell the review
> form. We would rather fix it. hello@wagvive.com

**Note:** this email needs the reviews app installed first. Judge.me free tier,
in the still-open list. Until then, build the flow but leave 4.2 unpublished.

---

## Flow 5. Winback, 60 days

**Trigger:** 60 days after delivery, no second order.
**Goal:** the repeat purchase. This is where singles finally earn their keep.

Pet is a genuine repeat category, and this is the one flow where advertising
singles is correct. The rule against it applies to **cold paid traffic**, where
a $4.71 average contribution cannot carry a click. To a customer who has already
bought, the click costs nothing and the single is pure basket.

**Subject:** Running low on anything?
**Preview:** The things that get used up, and what pairs with what you bought.

> It has been a couple of months since your order. If the wipes are running low
> or a toy has finally lost, here is the short list of what customers add after
> a first kit.
>
> [3 to 4 product blocks, chosen to complement the kit they bought]
>
> Free shipping over $60, same as before.
>
> [Shop everything]

**Pairing table for whoever builds it:**

**Every suggestion below is checked against the live kit composition. None of
them is already inside the kit the customer bought.** That check is the whole
point of the table: suggesting someone re-buy a thing they already own reads as
a shop that does not know what it sold them.

| They bought | Suggest | Why |
|---|---|---|
| Grooming Essentials Kit | Dematting comb $13.99, dental and ear wipes $13.99, pet hair remover mitt $10.99 | The three grooming jobs the kit does not cover: mats, mouth, and the fur on your sofa |
| New Puppy Kit | Talk button $16.99, dental duck chew $10.99, slow feeder bowl $13.99 | A puppy that is past the first month is ready to communicate, chew harder and eat slower |
| Toy Kit | Screaming chicken $12.99, squirrel squeaky plush $15.99, woodland rope-limb plush $12.99 | Rotation. Five toys is about six weeks before boredom |
| Travel Kit | LED waste bag dispenser $10.99, dematting comb $13.99, waterproof sofa cover $31.99 | What the car and the trail create: mess, mats, and a back seat that needs protecting |
| Calm & Comfort Kit | Waterproof snuggle blanket $23.99, heartbeat plush for a second room, talk button $16.99 | Anxiety work is per room, not per house |
| Dog Enrichment Kit | Crinkle plush buddy $11.99, jingle plush ball $12.99, watermelon rope frisbee $10.99 | The kit is all food puzzles. This adds the play half |

---

## How to build these

All five live in **Shopify admin › Marketing › Automations**. Shopify ships a
template for each one, so none of this is built from scratch.

| Flow | Shopify template to start from | Timing to set |
|---|---|---|
| 1. Welcome | Welcome new subscriber | 0h, then 2 days, then 5 days |
| 2. Abandoned checkout | Abandoned checkout | 1h, 24h, 72h |
| 3. Browse abandonment | Abandoned product browse | 4h |
| 4. Post-purchase | Post-purchase upsell, repurposed | 1 day after fulfillment, then day 21 |
| 5. Winback | Win back customers | 60 days |

Order to build them in, by value: **2, 1, 4, 3, 5.** Abandoned checkout recovers
money that is already most of the way to the till; everything else creates
demand from scratch.

Per flow: Create automation → pick the template → set the delays → open each
email → paste the subject, preview text and body → set the button link with its
UTM → **send yourself a test** → turn it on.

The editor is section based, not raw HTML, so the copy above goes in as text
blocks and the buttons as button blocks. It will inherit the store's email
branding, which is already the cream and ink palette.

**Two things I cannot do from any device**, because there is no Admin API for
marketing automations: create the automations, and turn off the old abandoned
checkout notification. Both are UI, and admin settings screens do not render in
a background tab, so they need you in a foreground window.

**What I can do once you say go:** create the WELCOME10 discount code with the
Bundles & Kits restriction and the one-per-customer limit, and verify it applies
correctly to each of the six kits and to nothing else.
