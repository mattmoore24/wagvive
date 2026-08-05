# Wagvive marketing plan, 2026-08

A launch plan for a store with one test order, no tracking installed, and a few
hundred dollars. It is built backwards from our own unit economics rather than
from channel best practice, because at this budget the economics rule out most
of what the best practice would tell us to do.

**Read section 1 first.** Everything else follows from it.

---

## 1. The number that decides everything

An ad channel is not good or bad in the abstract. It is affordable or it is
not, and that is decided by **contribution**: the cash left from an order after
goods, duty, freight, returns allowance and the payment fee.

Breakeven cost per click is `contribution x conversion rate`. Run
`python config/marketing/cac_ceiling.py` for the live table. As of 2026-08-04:

| Offer | Price | Contribution | Max CAC (70%) | Conversion needed at $0.35 (Pinterest) | at $0.90 (Meta) | at $1.10 (Shopping) | at $3.00 (Search) |
|---|---|---|---|---|---|---|---|
| Calm & Comfort Kit | $109 | **$43.06** | $30.14 | 0.8% | 2.1% | 2.6% | 7.0% |
| Travel Kit | $85 | $32.36 | $22.65 | 1.1% | 2.8% | 3.4% | 9.3% |
| New Puppy Kit | $54 | $30.61 | $21.43 | 1.1% | 2.9% | 3.6% | 9.8% |
| Grooming Essentials Kit | $70 | $29.77 | $20.84 | 1.2% | 3.0% | 3.7% | 10.1% |
| Toy Kit | $49 | $26.19 | $18.33 | 1.3% | 3.4% | 4.2% | 11.5% |
| Dog Enrichment Kit | $46 | $16.76 | $11.73 | 2.1% | 5.4% | 6.6% | 17.9% |
| **Average single product** | ~$17 | **$4.71** | $3.30 | 7.4% | **19.1%** | 23.4% | 63.7% |

Median pet-ecommerce conversion is about 2.6%. A brand new store with no
reviews realistically starts at **0.5% to 1.5%** on cold traffic.

### Three conclusions, and they are not negotiable

**Never advertise a single product to cold traffic.** The average single needs
19% conversion to break even on a $0.90 Meta click. Nothing converts at that.
Singles exist to fill baskets, to lift orders over the $60 free-shipping
threshold, and to be bought again. They are a retention and AOV product, not an
acquisition product.

**Kits are the only paid-acquisition product**, and even they are tight.
At a realistic 1% starting conversion rate, our best offer supports a **$0.43
click**. That is below Meta's typical pet CPC and far below Google Search.
Only Pinterest sits under it out of the box.

**Google Search at $3.00 a click is unaffordable** for anything except our own
brand name, where the conversion rate is high and the volume is nearly zero.

### What $300 actually buys

| Channel | Clicks for $300 | Orders at 1% | Orders at 2% |
|---|---|---|---|
| Pinterest ($0.35) | 857 | 8.6 | 17.1 |
| Meta low ($0.50) | 600 | 6.0 | 12.0 |
| Meta typical ($0.90) | 333 | 3.3 | 6.7 |
| Google Shopping ($1.10) | 273 | 2.7 | 5.5 |
| Google Search ($3.00) | 100 | 1.0 | 2.0 |

**$300 is not a growth budget. It is a learning budget.** It buys between 1 and
17 orders. Treat it as the cost of finding one working combination of offer,
audience and creative, not as a channel that will pay for itself immediately.
The plan is therefore sequenced so that free and owned channels carry the store
while paid money is spent on learning.

---

## 2. Where we actually stand

Verified on the live store, 2026-08-04:

| | |
|---|---|
| Orders all time | **1** (the #1001 test order) |
| Customers | 1, zero repeat |
| GA4 | **not installed** |
| Meta pixel / CAPI | **not installed** |
| Pinterest tag | not installed |
| Sales channels live | Online Store, Shop, POS |
| Google Merchant Center | not connected |
| Email list | empty, signup form exists in the footer |
| Product feed readiness | 42/42 missing GTIN, 36/42 titles lead with the brand |

We are at zero. That is not a problem, but it means **there is no data to
optimise against yet**, and any plan that starts with "scale the winners" is
fantasy. The first job is to build the instruments.

---

## 3. Channel verdicts

### 3.1 TikTok Shop: not viable yet, and this is a real finding

The plan asked for TikTok Shop. On the current fulfillment model it does not
work, for three independent reasons:

1. **Overseas direct shipping is restricted.** TikTok Shop US does not permit
   a US-positioned seller to ship directly from overseas; from 1 February 2026
   cross-border direct shipping runs through a whitelist of approved logistics
   providers only. Our CJ parcels ship direct from China on carriers chosen per
   order by margin, which is exactly the pattern the rule targets.
2. **The delivery deadline is shorter than our promise.** TikTok expects orders
   in transit within about 2 business days and delivered inside roughly 6
   business days. We publish 1 to 3 days of processing plus 5 to 12 days of
   delivery. We would breach the service standard on most orders and accumulate
   the penalties that follow.
3. **The economics do not survive the take rate.** The 6% referral fee is the
   headline, but stacking creator commissions of 10 to 20%, fulfillment and
   returns, the realistic all-in platform take approaches 30% of the selling
   price. Our kits run 36 to 56% contribution; a 30% take leaves single digits
   before any ad spend.

**Verdict: do not open TikTok Shop.** Revisit only if the store moves to a US
3PL, which the earlier sourcing study already priced at $10 to $14 an order
plus a $500 monthly minimum, and which only makes sense at volume we do not
have. Task #60 should be closed as "not viable on current fulfillment" rather
than left open as if it were a to-do.

**TikTok as a content and ads channel to our own site remains fully open**, and
is in the plan below. That is a different thing from TikTok Shop.

### 3.2 Google Merchant Center free listings: do this first

The only channel with a zero cost per click. Free listings surface products in
the Shopping tab, Search, Images and YouTube, and merchants commonly report
them driving 20 to 30% of total Google traffic. The same feed powers paid
Shopping later, so the work is not throwaway.

Two blockers, both found by `config/marketing/feed_health.py`:

- **All 42 products lack a GTIN.** We resell CJ goods with no manufacturer
  barcode. Leaving the barcode field blank causes "missing identifier"
  disapprovals. The fix is to declare in the Google channel that these products
  have no GTIN, not to invent one.
- **36 of 42 titles lead with "Wagvive".** Google's Shopping match is heavily
  title-weighted and nobody searches our brand. Feed titles must describe the
  product the way a shopper types it. `feed_health.py --titles` holds a written
  feed title for all 42 products, for example:

  | On site | In the feed |
  |---|---|
  | Wagvive Cooling Comfort Pad | Dog Cooling Mat, Pressure Activated Gel Pad for Crates and Beds |
  | Wagvive Calming Thunder Wrap | Dog Anxiety Vest, Calming Compression Wrap for Thunderstorms and Fireworks |
  | Calm & Comfort Kit | Dog Anxiety Calming Kit, Heartbeat Toy Compression Wrap and Cooling Mat |

  **Override in the feed only, never on the storefront.** The on-site titles
  are part of the brand; the feed titles are for a matching algorithm.

### 3.3 Google Ads: Standard Shopping only, and only later

Performance Max is the default recommendation everywhere and it is wrong for
us. PMax needs roughly 30 to 50 conversions a month to learn; under about
$3,000 a month it spends on irrelevant queries because it has no signal.
Standard Shopping gives search-term visibility, negative keywords and per
product bids, which is what a $300 budget needs.

Even then, Google Shopping's $1.10 pet CPC needs 2.6% conversion on our best
kit. That is above where a new store starts. **Google Ads is phase 3, not phase
1**, and it starts with a single Standard Shopping campaign restricted to kits.

Brand search is the exception: a tiny campaign on "wagvive" costs almost
nothing and stops competitors bidding on our name. Worth $1 a day once there is
any brand awareness at all, not before.

### 3.4 Meta: the scale channel, but not at this budget

Meta is where pet products work best long term. Pet delivers among the highest
category ROAS on Meta and the creative format suits the products. But Meta's
optimiser needs about 25 conversions a week for Advantage+ to leave the
learning phase, and Meta's own guidance is roughly $50 a day minimum, $100 to
be comfortable. Our whole budget is a few hundred dollars.

Spending $300 on Meta now means never leaving the learning phase, paying the 20
to 50% learning-phase CPA premium the whole time, and finishing with data too
thin to conclude anything.

**Meta enters when there is either $1,500+ a month to commit or a proven
0.5%+ site conversion rate from other channels**, whichever comes first. What
we do now instead is install the pixel and Conversions API immediately, so that
by the time we spend money the pixel already has months of view, cart and
purchase history to learn from. That is free and it compounds.

### 3.5 Pinterest: the one paid channel affordable today

Pinterest has the cheapest qualified shopping clicks of the major platforms
(about $0.35 in this category), users arrive in planning-and-buying mode rather
than being interrupted, and a single pin keeps working for 12 to 24 months,
which behaves more like SEO than like advertising. Our catalogue is unusually
well suited: every product is already shot on the same cream background in a
consistent frame, which is exactly the aesthetic that performs there.

At $0.35 a click our best kit breaks even at **0.8% conversion**, the only
sub-1% figure in the whole table. Pinterest is where the first paid dollar
goes.

### 3.6 Email: the highest return work available, and it is free

Flows are 5% of sends and about 41% of email revenue, at roughly 18 times the
revenue per recipient of campaigns. Welcome plus abandoned cart alone typically
drive 25 to 30% of email revenue. Email and SMS together reach 38 to 45% of
total revenue for strong operators.

We have a signup form and an empty list. Shopify's built-in automations are
adequate under about $500K of revenue, so **there is no reason to pay for
Klaviyo yet.**

Five flows, in build order:

1. **Welcome, 3 emails.** Offer, brand story, best-seller kit.
2. **Abandoned checkout, 3 emails.** Highest-value flow in ecommerce.
3. **Browse abandonment, 1 email.**
4. **Post-purchase, 2 emails.** Care instructions, then a review request at
   day 21, which is after our 5 to 12 day delivery window plus use time.
5. **Winback at 60 days.** Pet is a repeat category; this is where singles
   finally earn their keep.

### 3.7 Organic social and creators: how we get creative without a budget

We cannot pay $150 to $900 per UGC video at this budget. Two routes that cost
product rather than cash:

- **Seeding.** Send a kit to micro-creators (5,000 to 25,000 followers, 4 to 7%
  engagement) in exchange for content rights, no fee. Cost per placement is our
  goods and freight, which on the New Puppy Kit is **$19.74**, cheaper than a
  single UGC video and it comes with distribution attached.
- **Our own Runway pipeline.** We already generate consistent product imagery.
  The same masters can drive short vertical video for TikTok, Reels and
  Pinterest at zero marginal cost. See section 6.

The Creator programme page now carries the FTC disclosure requirements, so
seeding can start without a compliance problem.

### 3.8 SEO and content: slow, free, compounding

Product pages already have real descriptions and size guides. The gap is
non-transactional content that captures the questions people ask before they
buy: crate training at night, first week with a puppy, dogs and fireworks,
matted coat rescue. Each maps onto a kit. This is the cheapest long-term
acquisition we have and Claude can draft it at zero cost.

### 3.9 Deliberately not doing yet

| Channel | Why not |
|---|---|
| Amazon | Fees plus our delivery window; would need a US 3PL. |
| Google Search non-brand | $3.00 CPC needs 7% conversion on our best offer. |
| Performance Max | No conversion signal to feed it. |
| Paid influencers | $150 to $900 a video is most of the budget for one asset. |
| SMS marketing | TCPA needs separate express written consent; not worth the setup until the email list exists. |
| Klaviyo | Shopify's native flows are sufficient under $500K. |

---

## 4. The phased plan

### Phase 0: instruments and free channels. Cost $0. Weeks 1 to 2

Nothing paid happens until this is done, because spending before measurement is
how a small budget disappears without producing knowledge.

| # | Task | Who |
|---|---|---|
| 0.1 | Create GA4 property, install via Shopify's Google channel | Owner creates, Claude configures |
| 0.2 | Install Meta pixel + Conversions API, data sharing set to Maximum | Owner connects, Claude verifies |
| 0.3 | Google Merchant Center: connect, verify domain, declare no-GTIN, enable free listings | Owner authorises, Claude prepares feed |
| 0.4 | Apply the 42 feed titles | Claude |
| 0.5 | Build the five email flows | Claude drafts, owner approves |
| 0.6 | Pinterest business account + tag + catalogue | Owner creates, Claude configures |
| 0.7 | UTM convention and link builder | Claude |
| 0.8 | Baseline report: sessions, conversion rate, AOV | Claude, automated weekly |

**Gate to phase 1:** tracking verified end to end with a real test purchase
appearing in GA4, Meta and Pinterest.

### Phase 1: first $150. Weeks 3 to 6

Pinterest only. One campaign, one objective, three creatives, one product:
**the Calm & Comfort Kit**, because it has the highest contribution ($43.06),
the lowest breakeven conversion (0.8%), and the strongest emotional trigger
(storms, fireworks, separation) which is what performs on that platform.

- $5 a day for 30 days.
- Target: 0.8% conversion, meaning roughly 3 to 4 orders. **The goal is not
  profit, it is a conversion rate reading on real traffic.**
- Kill rule: if after $75 the click-through rate is below 0.3% or the site
  conversion rate is 0%, stop and change the creative, not the budget.

### Phase 2: second $150, conditional. Weeks 7 to 10

Only if phase 1 produced a measurable site conversion rate.

- If Pinterest conversion is at or above 1%: double Pinterest to $10 a day.
- If below 1% but traffic quality looks right: fix the landing page first, not
  the ads. At this budget conversion-rate work is cheaper than traffic.
- Start creator seeding: 5 kits to 5 micro-creators, about $100 of goods and
  freight, for content rights plus their own posting.

### Phase 3: scale gate. Month 4+

Only when both are true: **site conversion at or above 1.5%**, and **at least
20 orders of history** so a repeat rate can be estimated.

Then, in order:
1. Google Standard Shopping on kits only, $10 a day, negative keywords from
   day one.
2. Meta, only with $1,500+ a month available, using the pixel history built in
   phase 0.
3. Reinvestment rule: spend up to **70% of trailing 30-day contribution** on
   ads. That number comes from `cac_ceiling.py` and it is what stops a good
   month becoming an over-committed bad one.

---

## 5. What Claude automates

The point of this section is that ongoing marketing work should not depend on
the owner remembering to do it.

### Built and running now

| Script | Does | Cadence |
|---|---|---|
| `config/marketing/cac_ceiling.py` | The affordability table. Recomputes every offer's contribution and max CAC from the live price book. **Run after any repricing.** | On demand, and in the weekly report |
| `config/marketing/feed_health.py` | Checks all 42 products against Merchant Center requirements and holds the written feed titles | Weekly |

### To build in phase 0, once accounts exist

| Script | Does |
|---|---|
| `marketing/ads_report.py` | Pulls spend, clicks, conversions from Pinterest / Google / Meta APIs plus GA4, joins to contribution from `cac_ceiling.py`, and reports **profit per channel**, not ROAS. ROAS lies when margins differ by product. |
| `marketing/ad_guardrail.py` | The automated kill switch (task #62). Flags any campaign whose CAC exceeds 70% of the contribution of what it actually sold. Report-only first, exactly as `margin_guard.py` was. |
| `marketing/weekly_brief.py` | One page every Monday: what happened, what changed, what to do this week, with the numbers. |
| `marketing/content_calendar.py` | Generates the week's organic posts and SEO briefs from the product and kit data. |
| `marketing/review_requests.py` | Day-21 review request per delivered order (task #63). |

All of these run on the existing GitHub Actions schedule, the same mechanism
that already runs inventory sync and the margin guard every 6 hours. Nothing
new has to be learned to operate them.

### What Claude cannot do, and the owner must

Account creation and anything involving identity or payment: Google, Meta,
Pinterest business accounts; payment methods on ad platforms; domain
verification where it requires a login; the NY sales tax registration (task
#57); the CJ conversation about duties (task #64). Claude will prepare
everything up to the point of the login and hand over with exact steps.

---

## 6. Creative pipeline with Runway

We already have a consistent studio look: every product on cream #F7F2E9 with
matched framing, plus approved masters for each SKU. That is a real asset,
because the expensive part of creative is consistency.

**The rule that already applies to stills applies to video: shoot the master
first, then derive.** Never let the model invent the product.

Three formats, all derived from existing masters:

1. **Vertical product motion, 5 to 8 seconds.** Slow push in on the product on
   the brand background. Pinterest, Reels, TikTok. Cheapest to make, works as a
   catalogue ad.
2. **Kit reveal, 10 to 15 seconds.** Components appearing one at a time, ending
   on the assembled kit and the price. This is the ad for the paid campaigns,
   because the kit is what we can afford to advertise.
3. **Problem-and-answer, 15 seconds.** Text-led: the storm, the muddy paws, the
   first night in the crate, resolving to the product. Highest performing
   format in pet, and the one that needs no dog footage we do not own.

Every output gets eyeballed against the CJ reference before use, same rule as
the product photography, because the model still invents plausible-but-wrong
details.

---

## 7. Decision rules

Written down so they are not re-argued every month.

| Situation | Rule |
|---|---|
| Considering advertising a single product | Do not. Kits only. |
| A channel's CPC | Viable only if `CPC / expected CVR < 70% of contribution`. |
| Campaign underperforming after $75 | Change creative or offer. Never raise budget to fix a conversion problem. |
| Site conversion below 1% | Fix the site, not the ads. Traffic is more expensive than CRO at this scale. |
| A month with real profit | Reinvest up to 70% of trailing 30-day contribution. |
| A "great ROAS" report | Check profit per channel in `ads_report.py`. ROAS is meaningless across products with 36% to 56% margins. |
| Prices change | Re-run `cac_ceiling.py`. Every CAC ceiling moves. |
| Tempted by TikTok Shop | Re-read section 3.1. Nothing changes until fulfillment changes. |

---

## 8. Realistic expectations

At a few hundred dollars, honest targets for the first 90 days:

| Metric | Target |
|---|---|
| Orders | 15 to 30 |
| Site conversion rate | 0.5% to 1.5% |
| Email list | 200 to 500 |
| Creator content pieces | 5 to 10 |
| Free listing impressions | 5,000 to 20,000/month |
| Profit | **Around break-even, possibly negative** |

The deliverable of the first 90 days is not profit. It is a **measured
conversion rate, a working measurement stack, an email list, and one channel
proven affordable.** With those, the next few hundred dollars is an investment
rather than a guess. Without them, it is a guess no matter how much is spent.

---

## Sources

Benchmarks used are 2026 figures gathered on 2026-08-04:

- Pet care ecommerce conversion 2.70%, Meta pet ROAS 4.3x, pet CPM $15.95:
  [IRP Commerce pet care market data](https://www.irpcommerce.com/en/gb/ecommercemarketdata.aspx?Market=10),
  [Meta ads benchmarks 2026](https://mhigrowthengine.com/blog/meta-ads-benchmarks-ecommerce-2026/)
- Google Shopping CPC and PMax minimum viable budget:
  [Google Shopping benchmarks](https://owlclaw.com/benchmarks/google-shopping-benchmarks/),
  [PMax vs Standard Shopping](https://blog.adnabu.com/google-ads/performance-max-vs-standard-shopping/)
- Meta learning phase 25 conversions/week, $50 to $100 a day:
  [Advantage+ 2026 guide](https://www.1clickreport.com/blog/advantage-plus-shopping-25-conversions-2026-guide)
- TikTok Shop fees, cross-border shipping rules and fulfillment deadlines:
  [TikTok Shop seller costs 2026](https://www.fastmoss.com/blog/tiktok-shop-seller-costs-in-the-us-2026-fees-creator-commissions-fulfillment-returns-real-profit/),
  [cross-border direct shipping rules](https://chinesellers.substack.com/p/tiktok-shop-us-releases-new-rules),
  [dropshipping policy 2026](https://www.shoplazza.com/blog/tiktok-shop-policy-update)
- Email flow revenue share and benchmarks:
  [Klaviyo ecommerce benchmarks](https://www.klaviyo.com/marketing-resources/ecommerce-benchmarks),
  [Shopify email flows with revenue data](https://www.flypost.agency/blog/shopify-email-flows)
- Google Merchant Center free listings:
  [free listings guide](https://feedops.com/feedops/google-shopping-free-listings/)
- Pinterest CPC and organic longevity:
  [Pinterest statistics 2026](https://www.digitalapplied.com/blog/pinterest-statistics-2026-marketing-data-points)
- UGC and micro-influencer rates:
  [UGC rates 2026](https://influee.co/blog/ugc-price),
  [pet influencer rates](https://brandsforcreators.com/find/pets-influencers)
