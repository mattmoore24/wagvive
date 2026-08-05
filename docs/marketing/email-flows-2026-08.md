# The five email flows

Phase 0.5 of `docs/marketing-plan-2026-08.md`.

**Status: the welcome code `WELCOME10` is LIVE. The five automations are NOT,
and Claude cannot build them from any device.** Shopify exposes no Admin API for
marketing automations, confirmed against the schema and the docs: `marketingEvents`
is a read-only reporting query and there is no create mutation. So the copy below
is paste-ready and the click path is exact, but a person has to be in the admin.

Why this is worth doing before any paid traffic: flows are about 5% of sends and
41% of email revenue, at roughly 18 times the per-recipient value of campaigns.
They cost nothing, and they have to exist *before* the first Pinterest visitor
arrives rather than after. Abandoned checkout works from order one regardless of
how small the list is.

Shopify's native automations are used throughout. Klaviyo is not justified under
about $500K of revenue and would be a monthly cost against a $300 total budget.

---

## Decisions, settled 2026-08-05

### The welcome code is LIVE

**`WELCOME10`, 10% off the entire order, minimum $45, one use per customer, no
expiry.** Created and verified on the live store.

| Field | Value |
|---|---|
| Code | `WELCOME10` |
| Title in admin | Welcome 10% (email signup) |
| Discount class | `ORDER` (10% off the whole order, not per product) |
| Applies to | Everything. No collection or product restriction. |
| Limit | One use per customer. No cap on total redemptions. |
| Minimum spend | **$45.00** |
| Starts / ends | 2026-08-05 / never |
| Combines with | Order, product and shipping discounts all `true` |
| Status | ACTIVE, 0 uses |
| Live summary | `10% off entire order • Minimum purchase of $45.00 • One use per customer` |
| ID | `gid://shopify/DiscountCodeNode/1678979858721` |

**Verified end to end with four draft orders**, not from the create response.
All four were deleted afterwards; the store has zero draft orders and the code
shows zero uses.

| Test | Result | Meaning |
|---|---|---|
| Calm & Comfort Kit, $109 | $98.10, $10.90 off, shipping $0.00 | Applies, and the kit stays over the $60 free-shipping line |
| Three toys, $34.97 | $31.48, exactly 10% | Applied before the minimum was added |
| **Dog Enrichment Kit, $46** | **$41.40, $4.60 off** | The cheapest kit still qualifies. This was the boundary case. |
| **Calming Thunder Wrap, $31.99** | **$31.99, $0.00 off** | A single below $45 gets nothing, which is the point |

**Why 10%, and why a $45 minimum rather than a kits-only restriction.**

The rate is 10% because **15% drops the Grooming Essentials Kit to $59.50, under
the $60 free-shipping threshold**, where the customer loses free shipping at the
payment step. 10% keeps it at $63.00. An earlier argument of mine, that a
blanket code sends singles negative, was wrong: it came from `cac_ceiling.py`
excluding the $5.95 the customer pays for shipping under $60, and counted
properly nothing goes negative at either rate.

The **$45 minimum** does the job a kits-only restriction was meant to do, without
the cost of one:

- **All six kits qualify.** The cheapest, Dog Enrichment, is $46.
- **No single qualifies.** The most expensive single is $33.99, so a one-item
  order never carries the discount.
- **No kit crosses the $60 line** when discounted. Checked all six.
- The customer sees "spend $45", which is **actionable**, rather than "not valid
  for these items", which is a dead end at the worst moment.

What it costs, if every first order uses it: about **$6.68 per order, 20% of
average kit contribution**. For comparison, paid acquisition at the plan's own
phase 1 assumptions ($0.35 CPC, 0.8% conversion) is **$43.75 per order**, and is
paid whether or not anyone buys. The discount is roughly six times cheaper and
only costs anything when an order happens.

**The risk to watch is incrementality, not margin.** The code also reaches people
who would have bought anyway, and that is unmeasurable at one order and no
analytics. Trigger for review: **if coded orders exceed about 75% of all orders**,
it has stopped being an acquisition tool and become a permanent 10% price cut, at
which point the honest move is to lower prices officially or retire it. This
belongs in `marketing/weekly_brief.py` when that gets built.

**One thing the draft-order test could not prove.** Draft orders do not evaluate
automatic discounts, so the three-toy basket showed only WELCOME10's 10%, not the
live *"Any 3 toys, 15% off"*. On the `combinesWith` flags they should stack at a
real checkout, giving about 23.5%, and I checked all 455 possible three-toy
baskets at that rate: the worst still returns $13.07 of contribution. It is safe
either way, but **the real confirmation is the phase 0 gate test purchase**, so
watch for it there.

### The abandoned checkout conflict is resolved

Owner confirmed on 2026-08-05 that **Settings › Checkout › Abandoned checkouts is
switched off** and no marketing automations are live. So flow 2 can be built and
enabled without the duplicate-send problem.

The branded `abandoned-checkout.liquid` template stays installed under Settings ›
Notifications and does nothing while the setting is off. If you ever want to
revert to the single email, that toggle is the only thing that changes.

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
**Preview:** Every kit qualifies, and it does not expire quietly.

> Thanks for joining.
>
> Here is 10% off your first order over $45. Use **WELCOME10** at checkout.
>
> Every kit qualifies.
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
> Your 10% is still good on any kit. **WELCOME10**
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
> If price was the sticking point, **WELCOME10** takes 10% off orders over $45.
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

## Building all five: the complete guide

**Claude cannot do this part.** Shopify has no Admin API for marketing
automations. `marketingEvents` is a read-only reporting query; there is no
create mutation, and the setup screens do not render in a background tab. This
is the same category as Settings › Notifications, which is why the 18
notification templates were also installed by hand.

Everything that could be removed from the job has been: copy is written, delays
are decided, traps are marked, and the discount it depends on is live and tested.

**Total time: about 45 minutes for all five.** Build order is by value, so if you
stop after one you have stopped in the right place.

### Prerequisites, both already true

- `WELCOME10` is live with a $45 minimum. Flows 1 and 2 reference it.
- Settings › Checkout › Abandoned checkouts is **off**, so flow 2 will not
  duplicate.

### The one trap that applies to every flow

Shopify's templates put an exit condition on the **first** email only. Steps you
add do **not** inherit it. On every added email, add a **Condition** before it:

| Flow | Condition to add before emails 2 and 3 |
|---|---|
| 1. Welcome | *Customer has not placed an order* |
| 2. Abandoned checkout | *Checkout completed, is false* |
| 4. Post-purchase | none needed, it is triggered by a real order |

Miss it and you email people who already bought, which is worse than not sending.

### Flow 2, abandoned checkout. Build this first

Recovers money already most of the way to the till, and it is the only flow that
works with an empty list because it triggers on a checkout, not a subscriber.

1. Marketing › Automations › **Create automation** › **Abandoned checkout**.
2. First **Wait**: **1 hour**. Open the email, paste 2.1. Button: **Return to
   checkout**, which the template already wires to the per-checkout recovery URL.
   Never hand-write that link.
3. **Add step** › Wait › **23 hours**. Add Condition *Checkout completed is
   false*. Add step › Send email, paste 2.2.
4. **Add step** › Wait › **48 hours**. Add the same Condition. Send email, paste
   2.3.
5. Send yourself a test on each. Turn it on.

### Flow 1, welcome. Build this second

1. Create automation › **Welcome new subscriber**. Trigger is the footer signup,
   which is already live.
2. Email 1 immediately, paste 1.1.
3. Wait **2 days**, Condition *has not placed an order*, email 1.2.
4. Wait **3 days** (5 from signup), same Condition, email 1.3.
5. Test, turn on.

### Flow 4, post-purchase. Build this third

1. Create automation › **Order fulfilled** as the trigger.
2. Wait **1 day**, paste 4.1.
3. Wait **20 days** (day 21), paste 4.2. **Leave this second email unpublished
   until a reviews app exists**, because its button has nowhere to point.
4. Test, turn on.

### Flow 3, browse abandonment. Fourth

1. Create automation › **Abandoned product browse**.
2. Wait **4 hours**, paste flow 3. One email only.
3. Test, turn on.

### Flow 5, winback. Last

1. Create automation › **Win back customers** (or a **Customer has not ordered
   in X days** trigger).
2. Set to **60 days** since last order.
3. Paste flow 5. Populate the product blocks from the pairing table, which is
   checked against live kit composition so nothing suggests an item the customer
   already owns.
4. Test, turn on.

### When all five are on

Send yourself one real test purchase end to end. That is the phase 0 gate
anyway, and it is the only way to confirm two things this session could not:
that `WELCOME10` stacks with the *"Any 3 toys, 15% off"* automatic discount as
the `combinesWith` flags say it should, and that the abandoned checkout sequence
fires exactly once per abandonment.
