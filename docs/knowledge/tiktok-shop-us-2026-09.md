# TikTok Shop US, re-verified 2026-09-11 against TikTok's own pages

**Bottom line.** The China-shipped catalogue cannot be sold on TikTok Shop US.
That is TikTok's rule, not a pricing or effort choice. The only route to the
full catalogue is holding stock in a US warehouse. TikTok as an ADS channel to
wagvive.com (pixel, Events API, catalog ads) is fully open and needs no TikTok
Shop.

This replaces the 2026-08 verdict in `docs/marketing-plan-2026-08.md` §3.1,
whose sources were three blogs. That verdict's CONCLUSION survives; its reasons
now rest on primary pages, and one of them (the "1 Feb 2026 whitelist") could
not be found on any TikTok-owned page and is the wrong rule for Wagvive anyway.

Every source below is `seller-us.tiktok.com/university/essay?knowledge_id=...`
unless stated. Dates are each page's own "last updated".

## Why the China catalogue is out

| Rule | Source |
|---|---|
| "U.S.-based sellers cannot use international third-party suppliers or consolidation services." | Best Practices for Order Fulfillment, 6179821974439723, 09/09/2026 |
| "We are unable to update tracking for Cross-Border orders as they are not permitted on our US platform at this time." Seller Shipping is "only applicable to US local to local (Domestic) logistics services". | Seller Shipping: Overview and Services, 8308896260065025, 08/12/2026 |
| "Only U.S. based businesses and warehouse address(es) are supported." No P.O. boxes. | TikTok for Shopify onboarding guide, 6184952698373890, 07/31/2026 |
| TikTok Shipping is "currently only for US domestic warehouses". | What is TikTok Shipping?, 1830506744514347, 09/08/2026 |
| Orders must be **In Transit within 2 business days** (first carrier scan, not label), **Delivered within 6 business days** (handling included), and are **auto-cancelled at 5 business days** without tracking. | Fulfillment Policy, 3995852763301633, 09/03/2026 |
| Late Dispatch Rate: enforcement above 10%. On-Time Delivery at least 80%. Valid Tracking at least 95%. Seller-fault cancellations at most 2.5%. Breaches bring rating deductions, order limits, extended settlement, suspension. | Fulfillment Policy; metric pages 08/06/2026; AHR requirements |

Against CJ China's measured 5 to 11 business days of handling and 10 to 16
door to door, that is roughly 100% late dispatch, near-0% on-time delivery and
seller-fault auto-cancellations: the shop would be restricted within weeks.

## Rules that bite even a US-warehouse shop

- **Default shipping mode for new US sellers is TikTok Shipping.** Its labels
  are created in Seller Center, "NOT in the Shopify Order Admin or other third
  party shipping services". CJ's normal flow (read the Shopify order, ship on
  its own carrier, write tracking back) only fits Seller Shipping, which "may
  only be available to select sellers". (onboarding 07/31/2026; Customer Order
  Shipping Requirements 6837879804970754, 09/03/2026)
- **New shop probation**: Beginner tier is 50 orders a day and 100 products;
  no Custom Handling Time until graduation. (3238037484062465, 08/10/2026)
- **Return address** must be owned, authorised and business-affiliated, from
  5 Aug 2026; unauthorised addresses are an enforcement issue. (Policy Pulse
  6747273381791534, 09/10/2026)
- **Payout**: new shops are paid 31 days after DELIVERY. (Finance,
  1167036928444174)
- **Fraudulent-shipping rule** bans fulfilling from "another online retailer".
  Aimed at retail arbitrage; a dropship supplier is most plausibly outside it,
  but no page says so. Unresolved.

## Listing rules that the current catalogue fails

- **Main image must have a pure white background** (Product Listing Policy,
  3196690250417921, 09/01/2026). Wagvive's house style is cream `#F7F2E9`, so
  every main image needs a white-background version for TikTok.
- **Titles 25 to 200 characters.** Several fail, e.g. "Wagvive Talk Button"
  (19).
- **GTIN/UPC** required "for most categories"; no primary page lists an
  exemption. Unresolved.
- **Kits cannot go on TikTok Shop.** Shopify Bundles "must use the Online Store
  or Headless storefronts", and TikTok prohibits "combining multiple standalone
  products ... in a single product listing".

## Category and product qualification

- **Pet Supplies is category-gated**, not invite-only: one qualification,
  reviewed in about 6 days. (Restricted Products 3238037484275457; Pet Supplies
  Requirements 5166793187346222, both 09/01/2026)
- "Relaxants & Anxiety Relief" sits under **invite-only** Pet Healthcare, and
  claims to treat or prevent anything are banned. Whether the calming vest falls
  there is untested.
- **Electronics** (LED collar, LED clippers, grinder, trimmer, ball launcher,
  heartbeat plush, LED dispenser) need a Certificate of Compliance under 2 years
  old OR a MANUFACTURER invoice under 365 days, plus a photo of the safety mark.
  (1418345612003114, 08/26/2026)
- **Lithium-battery items** are product-level Dangerous Goods: an SDS AND a
  UN38.3 test report. (2297870046414638, 09/01/2026)

## Money

- **Referral fee 6%** on every Pet Supplies subcategory, on customer payment +
  platform discount - tax. (5988482086864682, 05/14/2026)
- It "encompasses all TikTok Shop fees, with the exception of shipping and tax
  fees", so it REPLACES Shopify Payments rather than stacking: net +1.2 to +2.6
  points on Wagvive's prices. (5982454398175018)
- Creator commission is optional, 1% to 80%, only on creator-driven orders.
  At 20% plus Smart Promotion the take is about 29.5% of price.
- Refunds keep a 20% Refund Administration Fee, capped at $5 per SKU.
- A TikTok-only price is possible with price sync OFF, but that switch is
  store-wide, so every Shopify reprice must then be repeated by hand. Fair
  Pricing Policy limits how far prices may differ.
- Whether Shopify's 2% Basic-plan third-party fee applies to TikTok Shop orders
  is unresolved.

## What IS open: TikTok ads to wagvive.com

- Shopify's free **TikTok** app (TikTok Inc.) sets up the pixel and Events API
  **without TikTok Shop**. (ads.tiktok.com/help/article/shopify-set-up-guide)
- **Catalog ads** to the website: "You don't need to set up a TikTok Shop when
  you choose a Catalog as your product source"; needs at least 4 in-stock,
  approved products. Manual catalog campaigns are exempt from the January 2026
  rule that other new campaigns must be linked to a TikTok account.
- Ad policy has NO numeric delivery deadline, only that products "reach buyers
  as promised". Pet products are allowed; shock collars and ultrasonic
  repellers are not.
- Using your own profile as the ad identity needs a **TikTok Business
  Account**; a personal account can be switched in the app.
- Budgets: campaign daily over $50, ad group over $20; TikTok recommends $30 a
  day per ad group. Learning phase settles after about 25 results or 7 days.
- Shopify's pixel setting defaults to "Optimized" (13 Jan 2026) and can pause a
  pixel with no signal. Set TikTok's to **Always on** under Settings > Customer
  events before running ads.
- Bio link: TikTok's indexed FAQ says verified Business accounts can post a
  website link; general accounts need 1,000 followers. Body not fetchable.
