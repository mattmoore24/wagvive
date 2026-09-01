#!/usr/bin/env python3
"""The FTC delay option notice. It did not exist in any form before 2026-09-01.

WHY THIS IS NOT OPTIONAL. Under the FTC Mail, Internet, or Telephone Order
Merchandise Rule (16 CFR 435.2(b)), when a seller cannot ship inside the time
it stated, it must send the buyer a notice BEFORE the original date passes,
by a means at least as fast as the order was taken, at no cost to the buyer,
that gives:

  * a REVISED DEFINITE date (not "soon", not "we are working on it"),
  * the OPTION TO CANCEL for a prompt full refund, and
  * for a first delay of 30 days or less, it may treat silence as consent -
    but ONLY if it says so.

Wagvive missed its stated shipping representation on at least two of its
three real orders and sent no notice at all. That is an independent violation
of 435.2(b), separate from the missed date, and it is the one entirely within
the store's control.

HOW IT IS SENT. Shopify has no "delay" notification trigger, so there is no
template to install. The notice goes out through Orders -> the order ->
Contact customer, which renders `config/email-templates/contact-customer.liquid`
around a `{{ custom_message }}`. This module produces that message.

WHAT TRIGGERS IT. `config/track_watch.py` alarm condition A: fulfilled N days
ago, CJ route feed empty, order still UNSHIPPED. It fires at 6 business days,
deliberately inside the 10 business day dispatch representation, which leaves
four business days to send this before the representation lapses.

    python config/delay_notice.py --order 1004 --days 10
"""
import argparse
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise as DP  # noqa: E402

SUPPORT = 'hello@wagvive.com'


def business_days_from(start, n):
    d, added = start, 0
    while added < n:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d


def notice(order_name, revised_date, first_delay=True):
    """The plain-text message to paste into Shopify's Contact customer box.

    Deliberately plain text: it is rendered inside contact-customer.liquid,
    which supplies the branding. Deliberately free of blame and of any
    reference to the supplier, because the customer's contract is with us.
    """
    revised = revised_date.strftime('%A %-d %B %Y') if os.name != 'nt' else \
        revised_date.strftime('%A %d %B %Y').replace(' 0', ' ')
    consent = (
        'If we do not hear from you before it ships, we will take it that you '
        'are happy to wait.' if first_delay else
        'We cannot ship this without your agreement to the new date, so please '
        'reply either way. If we do not hear from you, we will cancel and '
        'refund you in full.')
    return (
        f'Your order {order_name} is running late, and we would rather tell '
        f'you than let you wonder.\n\n'
        f'We now expect it to ship by {revised}. Everything in the order is '
        f'still coming, and nothing has gone wrong with your payment.\n\n'
        f'You have a choice, and both options are completely fine with us:\n\n'
        f'  1. Wait for the new date above. {consent}\n'
        f'  2. Cancel for a full refund. Reply to this email with the word '
        f'CANCEL and we will refund you in full, back to your original '
        f'payment method. There is no form to fill in and nothing to return, '
        f'because it has not shipped.\n\n'
        f'Either way you will not be charged anything extra, and you do not '
        f'need to do anything today unless you want to cancel.\n\n'
        f'If it is easier to just ask a question, reply here or write to '
        f'{SUPPORT} and a person will answer.\n\n'
        f'Sorry for the wait.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--order', required=True, help='order name, e.g. 1004')
    ap.add_argument('--days', type=int, default=DP.DISPATCH_DAYS,
                    help='business days from today for the revised ship date')
    ap.add_argument('--repeat', action='store_true',
                    help='second or later delay: silence is NOT consent')
    a = ap.parse_args()

    name = a.order if a.order.startswith('#') else f'#{a.order}'
    revised = business_days_from(datetime.date.today(), a.days)
    print('=' * 68)
    print(f'Paste into Shopify -> Orders -> {name} -> Contact customer')
    print('=' * 68)
    print()
    print(notice(name, revised, first_delay=not a.repeat))
    print()
    print('=' * 68)
    print(f'Revised ship date: {revised}  ({a.days} business days from today)')
    print('Send this BEFORE the original stated date passes, or it does not')
    print('satisfy 16 CFR 435.2(b).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
