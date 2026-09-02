#!/usr/bin/env python3
"""Check every layer of wagvive.com's mail setup and say which one is wrong.

Written for the Google Workspace migration
(docs/knowledge/google-workspace-migration.md), but it is equally the standing
health check for the mail setup afterwards. Run it before the migration to get
a baseline, after each DNS step, and any time order confirmations start landing
in spam.

WHAT IT WILL NOT TELL YOU. DNS can prove records exist; it cannot prove mail
flows. Two checks remain manual and both matter more than anything here:
receive a mail from outside, and place a real test order then read
"Show original" for DKIM: PASS signed-by wagvive.com. See the doc.

THE DKIM CHECK IS NOT A SELECTOR GUESS. Shopify publishes its DKIM under a
non-standard selector, so probing shopify1._domainkey / s1._domainkey / etc.
finds nothing and proves nothing. The real test is whether
`_domainkey.wagvive.com` is an EMPTY NON-TERMINAL: NOERROR with zero answers
means names exist beneath it, i.e. selectors are published. NXDOMAIN means the
domain is not DKIM-authenticated at all.

    python config/verify_email_dns.py
    python config/verify_email_dns.py --expect google    # after the cutover
"""
import json
import os
import sys
import urllib.request

DOMAIN = 'wagvive.com'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def doh(name, rtype):
    """Resolve via DNS-over-HTTPS so the answer does not depend on local DNS."""
    url = f'https://dns.google/resolve?name={name}&type={rtype}'
    req = urllib.request.Request(url, headers={'accept': 'application/dns-json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def answers(name, rtype):
    try:
        d = doh(name, rtype)
        return d.get('Status'), [a.get('data', '') for a in (d.get('Answer') or [])]
    except Exception as exc:
        return None, [f'LOOKUP FAILED: {exc}']


def shop_sender():
    """The address Shopify actually sends from. Only `customer_email` counts:
    it flips after the emailed verification link is clicked, not on Save."""
    env = {}
    path = os.path.join(ROOT, 'config', 'shopify.env')
    if not os.path.exists(path):
        return None, 'no shopify.env'
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k] = v
    try:
        req = urllib.request.Request(
            f"https://{env['SHOPIFY_STORE_DOMAIN']}/admin/api/"
            f"{env['SHOPIFY_API_VERSION']}/shop.json",
            headers={'X-Shopify-Access-Token': env['SHOPIFY_ADMIN_API_TOKEN']})
        with urllib.request.urlopen(req, timeout=60) as r:
            shop = json.loads(r.read().decode())['shop']
        return shop.get('customer_email'), None
    except Exception as exc:
        return None, str(exc)


def main():
    expect = 'google' if '--expect' in sys.argv and 'google' in sys.argv else None
    ok, warn = [], []

    print(f'Mail health for {DOMAIN}\n' + '=' * 62)

    # ---- 1. MX -------------------------------------------------------------
    _, mx = answers(DOMAIN, 'MX')
    mx_txt = ' | '.join(mx) or '(none)'
    google_mx = any('google' in m.lower() for m in mx)
    fwd_mx = any('hostedemail' in m.lower() for m in mx)
    print(f'\n1. MX        {mx_txt}')
    if google_mx:
        print('   -> Google Workspace holds the mail. A real mailbox must exist.')
        ok.append('MX on Google')
    elif fwd_mx:
        print('   -> Shopify forwarding (OpenSRS). NO MAILBOX EXISTS; mail is'
              ' forwarded on.')
        (warn if expect == 'google' else ok).append('MX still on Shopify forwarding')
    elif not mx:
        warn.append('NO MX AT ALL - inbound mail will bounce')
        print('   -> !! no MX record: every mail to this domain bounces')
    else:
        warn.append(f'unrecognised MX: {mx_txt}')

    # ---- 2. SPF ------------------------------------------------------------
    _, txt = answers(DOMAIN, 'TXT')
    spf = [t.strip('"') for t in txt if 'v=spf1' in t]
    print(f'\n2. SPF       {spf or "(none)"}')
    if len(spf) > 1:
        warn.append('MULTIPLE SPF RECORDS - SPF fails completely (permerror)')
        print('   -> !! more than one v=spf1 record. A domain may publish exactly'
              ' ONE.\n      This is a permerror: SPF fails for every message.')
    elif not spf:
        warn.append('no SPF record')
    else:
        rec = spf[0]
        has_google = '_spf.google.com' in rec
        has_fwd = '_spf.hostedemail.com' in rec
        print(f'   -> google={has_google}  hostedemail={has_fwd}')
        if expect == 'google' and not has_google:
            warn.append('SPF does not authorise Google')
        elif expect == 'google' and has_fwd:
            warn.append('SPF still authorises the retired forwarder')
        else:
            ok.append('SPF single and coherent')

    # ---- 3. Shopify DKIM (the empty-non-terminal test) ----------------------
    status, ans = answers(f'_domainkey.{DOMAIN}', 'TXT')
    present = status == 0
    print(f'\n3. DKIM      _domainkey.{DOMAIN} -> '
          f'{"NOERROR" if status == 0 else "NXDOMAIN" if status == 3 else status}, '
          f'{len(ans)} answer(s)')
    if present:
        print('   -> selectors exist beneath it: the domain IS DKIM-authenticated.')
        print('      (Empty non-terminal. Do NOT try to guess the selector name.)')
        ok.append('DKIM selectors present')
    else:
        warn.append('DKIM ABSENT - order confirmations will start being junked')
        print('   -> !! nothing beneath _domainkey. Shopify sender authentication'
              ' is gone.')

    # ---- 4. Google DKIM ----------------------------------------------------
    _, g = answers(f'google._domainkey.{DOMAIN}', 'TXT')
    print(f'\n4. Google DKIM  {"present" if g else "not published yet"}')
    if expect == 'google' and not g:
        warn.append('Google DKIM not published (step 7)')
    elif g:
        ok.append('Google DKIM published')

    # ---- 5. DMARC ----------------------------------------------------------
    _, dm = answers(f'_dmarc.{DOMAIN}', 'TXT')
    print(f'\n5. DMARC     {dm or "(none)"}')
    if dm:
        pol = 'quarantine' if 'quarantine' in dm[0] else \
              'reject' if 'p=reject' in dm[0] else 'none'
        print(f'   -> policy {pol}.'
              + ('  Monitoring only; a mistake costs nothing yet.'
                 if pol == 'none' else
                 '  LIVE ENFORCEMENT: a broken setup sends real order mail to spam.'))
        ok.append(f'DMARC p={pol}')
    else:
        warn.append('no DMARC record')

    # ---- 6. Shopify sender of record ---------------------------------------
    sender, err = shop_sender()
    print(f'\n6. Shopify sender  {sender or "unknown"}'
          + (f'  ({err})' if err else ''))
    if sender and sender.endswith(f'@{DOMAIN}'):
        ok.append('Shopify sends from the domain')
    elif sender:
        warn.append(f'Shopify sends from {sender}, not the domain')

    # ---- verdict -----------------------------------------------------------
    print('\n' + '=' * 62)
    for o in ok:
        print(f'  OK    {o}')
    for w in warn:
        print(f'  WARN  {w}')
    print('\nDNS cannot prove mail flows. Still to do by hand:')
    print('  * send a mail from outside to hello@wagvive.com and confirm arrival')
    print('  * place a test order, open the confirmation, Show original, and')
    print('    confirm DKIM: PASS signed-by wagvive.com (NOT shopifyemail.com)')
    return 1 if warn else 0


if __name__ == '__main__':
    sys.exit(main())
