# Wagvive notification templates — install guide

All 17 templates live in this folder. Shopify has **no API** for notification
templates, so each is installed by hand:

> Shopify admin → **Settings → Notifications → Customer notifications** →
> click the template → **Edit code** → select all in the HTML box → paste → **Save**

Then hit **Send test email** on that template; it arrives at the hello@ inbox.

Everything below is already brand-matched (cream/ink palette, Wagvive wordmark,
hello@wagvive.com support line) and validated: balanced Liquid, balanced tables,
no `<style>` blocks, every variable checked against Shopify's schema for that
specific template, all well under Gmail's 102KB clipping limit.

---

## Tier 1 — fires on normal orders (do these first)

| # | Shopify notification | File |
|---|---|---|
| 1 | Order confirmation | `order-confirmation.liquid` |
| 2 | Shipping confirmation | `shipping-confirmation.liquid` |
| 3 | Shipping update | `shipping-update.liquid` |
| 4 | Out for delivery | `out-for-delivery.liquid` |
| 5 | Delivered | `delivered.liquid` |

These five cover the entire happy path a customer sees. Numbers 3–5 fire from
carrier scans, so with CJPacket they will go out on most orders.

## Tier 2 — money and recovery (high value, fires occasionally)

| # | Shopify notification | File |
|---|---|---|
| 6 | Abandoned checkout | `abandoned-checkout.liquid` |
| 7 | Order refund | `order-refund.liquid` |
| 8 | Order canceled | `order-canceled.liquid` |
| 9 | Order invoice | `order-invoice.liquid` |
| 10 | Order edited | `order-edited.liquid` |
| 10b | Draft order invoice | `draft-order-invoice.liquid` |

Abandoned checkout is the one with direct revenue attached — Shopify sends it
automatically to customers who reach checkout and leave. Worth doing early.

## Tier 3 — payment edge cases

| # | Shopify notification | File |
|---|---|---|
| 11 | Payment error | `payment-error.liquid` |
| 12 | Pending payment success | `pending-payment-success.liquid` |
| 13 | Pending payment error | `pending-payment-error.liquid` |

## Tier 4 — customer accounts

| # | Shopify notification | File |
|---|---|---|
| 14 | Customer account welcome | `customer-account-welcome.liquid` |
| 15 | Customer account invite | `customer-account-invite.liquid` |
| 16 | Customer account password reset | `customer-password-reset.liquid` |
| 17 | Contact customer | `contact-customer.liquid` |

Accounts are set to **optional** on this store, so 14–16 only fire if a customer
chooses to make one. `contact-customer` is the template used when you email a
customer directly from an order page — worth branding since it is one-to-one.

---

## Not included, and why

* **POS / exchange receipts** — no retail location.
* **Local pickup / local delivery** — shipping only.
* **B2B / company invites** — B2B is off.
* **Gift card created** — no gift cards on the store (`has_gift_cards: false`).
* **Fulfillment request / staff order notifications** — these go to you and CJ,
  not customers, so brand styling adds nothing.

Enable any of these later and the matching template can be generated from
`config/build_email_templates.py`.

## If you ever need to change the look

Do **not** hand-edit 17 files — the shared shell lives in
`config/build_email_templates.py`. Change the palette, wordmark, footer or
support copy there, re-run `python config/build_email_templates.py`, and every
template regenerates consistently. That is the whole reason it is a generator:
Shopify gives each notification a standalone template with no shared layout, so
hand-editing guarantees drift.

## Required drops (why a template can refuse to save)

Shopify validates that certain templates contain specific variables and rejects
the save with e.g. *"Body is missing the `{{ custom_message }}` drop"*. These are
already present in the files here:

| Template | Must contain |
|---|---|
| Order invoice, Draft order invoice, Contact customer | `{{ custom_message }}` |
| Customer account invite, Password reset, Abandoned checkout | `{{ url }}` |
| Order refund | `{{ amount }}` |

If you hit that error on any template, it means the drop is missing — tell me
which template and I'll add it at the generator rather than patching one file.

## Rollback

Every template has **Revert to default** in the same editor. Nothing here is
destructive or one-way.
