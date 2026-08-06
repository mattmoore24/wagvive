# Shopify Messaging: authoring automation emails as code

Learned by building the abandoned checkout flow on 2026-08-05. Almost none of
this is in Shopify's documentation, and every item below cost a failed attempt.

## The headline: you CAN paste HTML into automation emails

An earlier note in `docs/marketing/email-flows-2026-08.md` said Claude could not
build these because there is no Admin API. **The API part is true. The
conclusion was wrong.**

The Messaging email editor has a **Custom Liquid block**. Add one, and it takes
raw HTML with Liquid. So every marketing email can be authored in this repo,
reviewed, version controlled, and pasted in.

Path: Messaging › Automations › Create automation › pick a template ›
**Edit email** › add a **Custom Liquid** block.

## Required variables

The editor states these and rejects a save without them:

| Variable | Notes |
|---|---|
| `{{ unsubscribe_link }}` | **Renders a COMPLETE `<a>...</a>` element, not a URL.** |
| `{{ open_tracking_block }}` | Open tracking pixel. Put it at the very end. |

**The unsubscribe trap.** Writing
`<a href="{{ unsubscribe_link }}">Unsubscribe</a>` nests an anchor inside an
anchor. The browser closes the inner one early and the leftover attributes
render as visible text in the email:

```
Unsubscribe" style="color:#8A7B6B; text-decoration:underline;">Unsubscribe
```

Output it bare. `{{ unsubscribe_url }}` is the variant that returns a plain URL
if link styling is ever needed, but test it for empties: a silently empty href
is a CAN-SPAM failure, not a cosmetic one.

## Do NOT rebuild the page wrapper

The Custom Liquid block sits **inside** Shopify's own email container, which
already supplies the page background, the centering and the content width.

Building a second page frame inside it overflows the right edge: an outer
100% table with 12px side padding wrapping a card pinned to `width:600px` is
624px of content inside a roughly 600px container.

**Correct shape for a block:**

```html
<div style="display:none; ...">Preview text</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       border="0" style="width:100%; background-color:#F7F2E9; border-radius:14px;">
  ... rows ...
</table>
{{ open_tracking_block }}
```

No `<!doctype>`, no `<html>`, no `<head>`, no `<body>`, no fixed widths, and no
page background: the container paints it.

## Shopify adds its own Footer block

Every automation email gets a Footer block carrying the postal address, the
unsubscribe line and a copyright. So:

- **Do not print the address or unsubscribe in your Liquid.** They render twice.
- **Restyle it.** It defaults to a black background, which is wrong against the
  cream. Set background `#EFE7DA`, text `#8A7B6B`. It resets to black on every
  newly added email step.
- It is the better source for compliance anyway: Shopify maintains it, and it
  tracks the address in settings automatically.

## Liquid objects that work

| Object | Use |
|---|---|
| `{{ abandoned_checkout.url }}` | The per-checkout recovery link. **Never hand-write this**; a static URL sends people to an empty cart. |
| `{{ abandoned_checkout.line_items }}` | First five items. Each has `product_title`, `variant_title`, `quantity`, `image_url`. |
| `{{ abandoned_checkout.remaining_products_count }}` | Count beyond the first five. |
| `{{ shop.address.summary }}` | Full formatted address from settings. **Verified live.** Auto-updates when the address changes, so never hardcode. |
| `{{ shop.name }}`, `{{ shop.url }}` | As expected. |
| `{{ customer.* }}` | `first_name`, `email`, `orders_count`, `total_spent`, `tags` and more. |

**`variant_title` is the literal string `Default Title`** on single-variant
products, not empty. So this guard fails:

```liquid
{% if item.variant_title %}          {# renders "Default Title" #}
```

Use:

```liquid
{% if item.variant_title and item.variant_title != 'Default Title' %}
```

## Multi-step flows: the exit-condition trap

Shopify puts the exit condition on the **first** email only. Steps you add do
**not** inherit it. On every added email, add a Condition before it:

| Flow | Condition |
|---|---|
| Abandoned checkout | *Checkout completed, is false* |
| Welcome | *Customer has not placed an order* |
| Post-purchase | none, it is triggered by a real order |

Miss it and you email people who already bought.

## Shopify Flow does not help here

Installing Flow looked like a route to scripting this. It is not, for two
independent reasons:

1. **`.flow` files are hash-signed.** Export format is `<hash>:{JSON}`, and
   Shopify's developer forum confirms the algorithm is proprietary, so a
   hand-written file will not import.
2. **Flow does not author email content.** Its "Send marketing email" action
   opens the same Messaging editor. Flow orchestrates triggers, waits and
   conditions only.

Flow is still worth keeping for the ad guardrails and inventory alerts.

## Automations are invisible to the API

`marketingActivities` and `marketingEvents` both return 0 records for these.
There is no create mutation and no read visibility. **The only verification is
the admin UI or an actual send.** Budget for that when planning any audit.

## Driving the admin in a browser

The Messaging app renders in an embedded iframe that the accessibility tree
cannot see into, so `find` and `read_page` return nothing useful and clicks go
by coordinate. Two workarounds that matter:

- Plain `screenshot` intermittently returns a magnified partial view or times
  out with "renderer may be frozen". **`zoom` with the full viewport region
  returns the true rendering.**
- Foregrounding the tab fixes the OUTER admin frame's accessibility tree but
  not the embedded app.

Reliable enough to inspect and verify. Not reliable enough to author copy into.
