#!/usr/bin/env python3
"""Generate every customer-facing Shopify notification in the Wagvive brand.

Shopify has NO API for notification templates - they are admin-UI only. So this
builds the HTML for each one and writes it to config/email-templates/, ready to
paste into Settings > Notifications > <template> > Edit code.

Why a generator instead of 17 hand-written files: Shopify gives each notification
its own standalone template with no shared layout, so the header/footer/palette
would drift apart the moment one is edited. Here the shell lives in ONE place and
every template is stamped from it.

Email constraints baked into the shell (learned the hard way, see notes in
config/email-templates/order-confirmation.liquid):
  * table layout + fully inline CSS - Outlook drops <style> blocks and flex/grid
  * 600px single column, images with explicit width and absolute src
  * forced light color-scheme - dark-mode clients invert backgrounds unpredictably
  * every template stays far under Gmail's ~102KB clipping threshold

Run:  python config/build_email_templates.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'config', 'email-templates')
WORDMARK = ('https://cdn.shopify.com/s/files/1/0994/5114/2433/'
            't/1/assets/email-wordmark.png')

CREAM_PAGE = '#EFE7DA'
CREAM_CARD = '#F7F2E9'
INK = '#3A3026'
MUTED = '#6B5F51'
FAINT = '#8A7B6B'
HAIR = '#E2D8C8'
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
SERIF = "Georgia,'Times New Roman',serif"


def button(href, label):
    return f'''      <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
        <tr><td align="center" bgcolor="{INK}" style="border-radius:999px;">
          <a href="{href}" style="display:inline-block; padding:14px 34px; font-family:{SANS}; font-size:15px; font-weight:600; color:{CREAM_CARD}; text-decoration:none; border-radius:999px;">{label}</a>
        </td></tr>
      </table>'''


def note(html):
    """Soft cream panel used for delivery promises, tracking, warnings."""
    return f'''    <tr><td style="padding:22px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{CREAM_PAGE}; border-radius:10px;">
        <tr><td align="center" style="padding:16px 20px; font-family:{SANS}; font-size:14px; line-height:21px; color:{INK};">
{html}
        </td></tr>
      </table>
    </td></tr>'''


def items_block(loop_source, title_path, heading='In this order'):
    """Line-item table. loop_source/title_path differ between order and
    fulfillment templates, which expose different objects."""
    img = f'{{{{ {title_path} | img_url: \'compact_cropped\' }}}}'
    return f'''    <tr><td style="padding:26px 32px 0 32px;">
      <p style="margin:0 0 12px 0; font-family:{SANS}; font-size:12px; letter-spacing:0.08em; text-transform:uppercase; color:{FAINT};">{heading}</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        {{% for line in {loop_source} %}}
        <tr>
          <td width="64" valign="top" style="padding:10px 14px 10px 0;">
            {{% if {title_path}.image %}}
              <img src="{img}" width="64" height="64" alt="{{{{ {title_path}.title | escape }}}}" style="display:block; border:0; width:64px; height:64px; border-radius:8px; background-color:{CREAM_PAGE};">
            {{% endif %}}
          </td>
          <td valign="top" style="padding:10px 0; font-family:{SANS};">
            <div style="font-size:15px; line-height:21px; color:{INK}; font-weight:600;">{{{{ {title_path}.title }}}}</div>
            {{% if {title_path}.variant.title != 'Default Title' %}}<div style="font-size:13px; line-height:19px; color:{MUTED};">{{{{ {title_path}.variant.title }}}}</div>{{% endif %}}
            <div style="font-size:13px; line-height:19px; color:{FAINT};">Qty {{{{ line.quantity }}}}</div>
          </td>
        </tr>
        {{% endfor %}}
      </table>
    </td></tr>'''


def shell(title, preheader, heading, subcopy, body, show_order_name=True):
    order_line = ''
    if show_order_name:
        order_line = (f'      <p style="margin:16px 0 0 0; font-family:{SANS}; font-size:13px; '
                      f'line-height:20px; color:{FAINT}; letter-spacing:0.04em; '
                      f'text-transform:uppercase;">Order {{{{ order_name }}}}</p>')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{title}</title>
</head>
<body style="margin:0; padding:0; width:100%; background-color:{CREAM_PAGE}; -webkit-font-smoothing:antialiased;">

<div style="display:none; font-size:1px; color:{CREAM_PAGE}; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden;">{preheader}</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{CREAM_PAGE};">
<tr><td align="center" style="padding:28px 12px 40px 12px;">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px; max-width:600px; background-color:{CREAM_CARD}; border-radius:14px; overflow:hidden;">

    <tr><td align="center" style="padding:34px 32px 6px 32px;">
      <a href="{{{{ shop.url }}}}" style="text-decoration:none;">
        <img src="{WORDMARK}" width="180" alt="Wagvive" style="display:block; border:0; width:180px; max-width:180px; height:auto;">
      </a>
    </td></tr>

    <tr><td align="center" style="padding:14px 32px 0 32px;">
      <h1 style="margin:0; font-family:{SERIF}; font-size:27px; line-height:34px; font-weight:400; color:{INK};">{heading}</h1>
      <p style="margin:10px 0 0 0; font-family:{SANS}; font-size:15px; line-height:24px; color:{MUTED};">{subcopy}</p>
{order_line}
    </td></tr>

{body}

    <tr><td style="padding:26px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid {HAIR};">
        <tr><td style="padding:20px 0 0 0; font-family:{SANS}; font-size:14px; line-height:22px; color:{MUTED};">
          Questions? Reply to this email or write to <a href="mailto:hello@wagvive.com" style="color:{INK}; font-weight:600; text-decoration:underline;">hello@wagvive.com</a> and a real person will get back to you.
        </td></tr>
      </table>
    </td></tr>

    <tr><td align="center" style="padding:26px 32px 34px 32px;">
      <p style="margin:0; font-family:{SANS}; font-size:12px; line-height:19px; color:{FAINT};">
        <a href="{{{{ shop.url }}}}" style="color:{FAINT}; text-decoration:none;">wagvive.com</a> &nbsp;·&nbsp;
        <a href="{{{{ shop.url }}}}/policies/refund-policy" style="color:{FAINT}; text-decoration:none;">Returns</a> &nbsp;·&nbsp;
        <a href="{{{{ shop.url }}}}/pages/faq" style="color:{FAINT}; text-decoration:none;">FAQ</a>
      </p>
      <p style="margin:8px 0 0 0; font-family:{SANS}; font-size:12px; line-height:19px; color:#A2957F;">Wagvive · Dog gear worth keeping</p>
    </td></tr>

  </table>
</td></tr>
</table>
</body>
</html>
'''


def cta(href, label, pad='26px 32px 0 32px'):
    return f'''    <tr><td align="center" style="padding:{pad};">
{button(href, label)}
    </td></tr>'''


FULFIL_ITEMS = items_block('fulfillment.fulfillment_line_items', 'line.line_item', 'In this shipment')
ORDER_ITEMS = items_block('subtotal_line_items', 'line')

# Merchant's typed note. Required verbatim by Shopify in the invoice templates;
# wrapped in an {% if %} so nothing renders when no note was written.
CUSTOM_MESSAGE = f'''    {{% if custom_message != blank %}}
    <tr><td style="padding:22px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{CREAM_PAGE}; border-radius:10px;">
        <tr><td style="padding:18px 22px; font-family:{SANS}; font-size:15px; line-height:23px; color:{INK};">{{{{ custom_message }}}}</td></tr>
      </table>
    </td></tr>
    {{% endif %}}'''

TRACK_PANEL = f'''    <tr><td style="padding:24px 32px 0 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{CREAM_PAGE}; border-radius:10px;">
        <tr><td align="center" style="padding:22px 20px;">
          {{% if fulfillment.tracking_number %}}
          <p style="margin:0 0 4px 0; font-family:{SANS}; font-size:12px; letter-spacing:0.08em; text-transform:uppercase; color:{FAINT};">Tracking number</p>
          <p style="margin:0 0 16px 0; font-family:{SANS}; font-size:17px; line-height:24px; font-weight:600; color:{INK}; word-break:break-all;">{{{{ fulfillment.tracking_number }}}}</p>
          {{% endif %}}
          {{% if fulfillment.tracking_url %}}
{button('{{ fulfillment.tracking_url }}', 'Track your package')}
          {{% else %}}
{button('{{ order_status_url }}', 'View your order')}
          {{% endif %}}
          {{% if fulfillment.tracking_company %}}
          <p style="margin:14px 0 0 0; font-family:{SANS}; font-size:13px; line-height:19px; color:{MUTED};">Carrier: {{{{ fulfillment.tracking_company }}}}</p>
          {{% endif %}}
        </td></tr>
      </table>
    </td></tr>'''

TEMPLATES = {
 # ---------- shipping lifecycle ----------
 'shipping-update': dict(
   title='Your Wagvive shipment was updated', show_order_name=True,
   preheader='There is an update on your Wagvive shipment.',
   heading='A quick shipping update.',
   subcopy='The carrier has new information about your parcel. The latest tracking is below.',
   body=TRACK_PANEL + FULFIL_ITEMS),
 'out-for-delivery': dict(
   title='Out for delivery', show_order_name=True,
   preheader='Your Wagvive order is out for delivery today.',
   heading='Out for delivery.',
   subcopy='Your order is on the last leg of its trip and should arrive today.',
   body=TRACK_PANEL + FULFIL_ITEMS),
 'delivered': dict(
   title='Your Wagvive order was delivered', show_order_name=True,
   preheader='Your Wagvive order has been delivered.',
   heading='It has arrived.',
   subcopy='The carrier marked your order as delivered. We hope the tail wagging has already started.',
   body=note(f'<strong style="font-weight:600;">Something not right?</strong><br><span style="color:{MUTED};">Tell us within 30 days and we will make it right.</span>')
        + FULFIL_ITEMS + cta('{{ shop.url }}', 'Shop more')),
 # ---------- order lifecycle ----------
 'order-canceled': dict(
   title='Your Wagvive order was canceled', show_order_name=True,
   preheader='Your Wagvive order has been canceled.',
   heading='Your order was canceled.',
   subcopy='This order has been canceled and will not ship. If a payment was taken, the refund is on its way back to your original payment method.',
   body=ORDER_ITEMS + note(f'<span style="color:{MUTED};">Refunds usually appear within 5 to 10 business days, depending on your bank.</span>')),
 'order-refund': dict(
   title='Your Wagvive refund', show_order_name=True,
   preheader='A refund has been issued for your Wagvive order.',
   heading='Your refund is on the way.',
   subcopy='We have issued a refund to your original payment method.',
   body=note('<strong style="font-weight:600;">Refund total: {{ amount | money }}</strong><br>'
             f'<span style="color:{MUTED};">It usually appears within 5 to 10 business days, depending on your bank.</span>')
        + cta('{{ order_status_url }}', 'View your order')),
 # NOTE: Shopify's template validator REQUIRES {{ custom_message }} in the order
 # invoice and draft order invoice - saving is rejected with "Body is missing the
 # {{ custom_message }} drop" without it. It carries the note a merchant types when
 # sending an invoice from the order page, so it must render before the line items.
 'order-invoice': dict(
   title='Invoice for your Wagvive order', show_order_name=True,
   preheader='Here is the invoice for your Wagvive order.',
   heading='Your invoice.',
   subcopy='Here are the details for your order. You can complete payment using the button below.',
   body=CUSTOM_MESSAGE + ORDER_ITEMS + cta('{{ order_status_url }}', 'Complete payment')),
 'draft-order-invoice': dict(
   title='Your Wagvive invoice', show_order_name=False,
   preheader='Here is your Wagvive invoice.',
   heading='Your invoice.',
   subcopy='Here are the details we put together for you. Use the button below to complete your order.',
   body=CUSTOM_MESSAGE + ORDER_ITEMS + cta('{{ invoice_url }}', 'Complete your order')),
 'order-edited': dict(
   title='Your Wagvive order was updated', show_order_name=True,
   preheader='Your Wagvive order has been updated.',
   heading='Your order changed.',
   subcopy='We updated your order. The current contents are below, and any balance owed or refunded is handled automatically.',
   body=ORDER_ITEMS + cta('{{ order_status_url }}', 'View your order')),
 'abandoned-checkout': dict(
   title='You left something behind', show_order_name=False,
   preheader='Your cart is still waiting at Wagvive.',
   heading='You left something behind.',
   subcopy='Your cart is still saved. Pick up where you left off whenever you are ready.',
   body=items_block('line_items', 'line', 'Still in your cart')
        + cta('{{ url }}', 'Return to cart')
        + note(f'<strong style="font-weight:600;">Free US shipping over $60.</strong><br><span style="color:{MUTED};">Everything arrives in 5 to 12 business days.</span>')),
 'payment-error': dict(
   title='Payment issue with your Wagvive order', show_order_name=True,
   preheader='We could not process payment for your Wagvive order.',
   heading='We could not take payment.',
   subcopy='Something went wrong charging your payment method, so your order is on hold. Updating your details will release it.',
   body=cta('{{ order_status_url }}', 'Update payment method')),
 'pending-payment-success': dict(
   title='Payment received', show_order_name=True,
   preheader='Your payment cleared and your Wagvive order is confirmed.',
   heading='Payment received.',
   subcopy='Your payment has cleared and your order is confirmed. We are getting it ready now.',
   body=note(f'<strong style="font-weight:600;">Arrives in 5 to 12 business days.</strong><br><span style="color:{MUTED};">Tracking lands in your inbox as soon as it ships.</span>')
        + cta('{{ order_status_url }}', 'View your order')),
 'pending-payment-error': dict(
   title='Payment issue with your Wagvive order', show_order_name=True,
   preheader='There was a problem confirming payment for your Wagvive order.',
   heading='There was a payment problem.',
   subcopy='We could not confirm your payment, so your order has not been placed. You can try again below.',
   body=cta('{{ order_status_url }}', 'Try again')),
 # ---------- account ----------
 'customer-account-welcome': dict(
   title='Welcome to Wagvive', show_order_name=False,
   preheader='Your Wagvive account is ready.',
   heading='Welcome to Wagvive.',
   subcopy='Your account is ready. Checkout will be faster from here, and your orders live in one place.',
   body=cta('{{ shop.url }}/account', 'View your account')
        + note(f'<strong style="font-weight:600;">Free US shipping over $60.</strong><br><span style="color:{MUTED};">Every order arrives in 5 to 12 business days.</span>')),
 'customer-account-invite': dict(
   title='Activate your Wagvive account', show_order_name=False,
   preheader='Activate your Wagvive account.',
   heading='Activate your account.',
   subcopy='You are one click away from a Wagvive account, which keeps your orders and addresses handy for next time.',
   body=cta('{{ url }}', 'Activate account')),
 'customer-password-reset': dict(
   title='Reset your Wagvive password', show_order_name=False,
   preheader='Reset your Wagvive password.',
   heading='Reset your password.',
   subcopy='We received a request to reset your password. If that was not you, you can safely ignore this email.',
   body=cta('{{ url }}', 'Reset password')),
 'contact-customer': dict(
   title='A message from Wagvive', show_order_name=False,
   preheader='A message from the Wagvive team.',
   heading='A note from Wagvive.',
   subcopy='{{ custom_message }}',
   body=''),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, cfg in TEMPLATES.items():
        html = shell(cfg['title'], cfg['preheader'], cfg['heading'],
                     cfg['subcopy'], cfg['body'], cfg['show_order_name'])
        path = os.path.join(OUT, f'{name}.liquid')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(html)
        print(f'{name:28} {len(html):6} bytes')
    print(f'\n{len(TEMPLATES)} templates -> config/email-templates/')


if __name__ == '__main__':
    main()
