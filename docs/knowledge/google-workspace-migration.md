# Moving hello@wagvive.com from Shopify forwarding to a real Google Workspace mailbox

**Written 2026-09-01, before any change.** Every "current state" line below was
queried live, not remembered.

## Why this is riskier than it looks

`hello@wagvive.com` is not just a support address. It is the **verified sender
on every transactional email the store sends** - order confirmations, shipping
confirmations, refunds. Break its authentication and order confirmations start
landing in spam, which is worse than having no custom domain at all.

## Current state, verified live 2026-09-01

| Layer | Value | Meaning |
|---|---|---|
| MX | `1 mx.wagvive.com.cust.b.hostedemail.com` | Shopify's forwarding backend (OpenSRS). **There is no mailbox.** |
| SPF | `v=spf1 include:_spf.hostedemail.com ~all` | Authorises the forwarder only |
| DMARC | `v=DMARC1; p=none` | Monitoring only, nothing is rejected |
| DKIM | `_domainkey.wagvive.com` returns **NOERROR, 0 answers** | Empty non-terminal: Shopify's selectors DO exist beneath it. Shopify uses a NON-STANDARD selector name, so probing `shopify1._domainkey` etc. finds nothing and proves nothing. |
| `shop.customer_email` | `hello@wagvive.com` | The effective sender, and it is verified |
| DNS control | Shopify admin -> Settings -> Domains -> wagvive.com -> DNS settings | **Not editable by API.** Introspection confirms zero DNS mutations on the Admin GraphQL schema. |

## The four things that can go wrong

1. **Flipping MX before the mailbox exists.** The moment MX points at Google
   with no Workspace user created, every mail to hello@ hard-bounces. Customers
   replying to an order confirmation get a rejection notice.
2. **Two SPF records.** A domain may publish exactly ONE `v=spf1` TXT record.
   Adding a Google SPF alongside the existing one is not additive - it is a
   permerror, and SPF fails completely. The existing record must be EDITED, not
   joined.
3. **Deleting Shopify's DKIM.** The selectors under `_domainkey.wagvive.com` are
   what make order confirmations pass DMARC. They are unrelated to mailbox
   hosting and must be left completely alone. Adding Google's own DKIM does not
   conflict; DKIM is designed for multiple selectors per domain.
4. **Leaving Shopify email forwarding on.** Once Google holds the MX, the
   forwarding rule is dead weight, and leaving it configured invites a future
   session to "repair" the MX back to hostedemail.

## Order of operations

Steps 1 to 3 change NOTHING about live mail. The cutover is step 4.

**1. Create the Workspace account.** (Owner only - I cannot create accounts or
enter payment details.) Business Starter is about $7/user/month; one user is
enough. Sign up at workspace.google.com with wagvive.com as the domain.

**2. Verify domain ownership.** Google gives a TXT record. Add it in Shopify
admin -> Settings -> Domains -> wagvive.com -> DNS settings. This is additive
and safe. Mail keeps flowing through the existing forwarding.

**3. Create the `hello` user inside Workspace.** The mailbox must exist BEFORE
the MX changes. Do not create it as an alias; make it the primary user.

**4. THE CUTOVER - switch MX.** In Shopify DNS settings, delete the
`mx.wagvive.com.cust.b.hostedemail.com` record and add Google's:

    Type  MX   Host  @   Priority  1   Value  smtp.google.com

(That single record is Google's current recommendation. If the Workspace setup
wizard shows the older five-record ASPMX set, use whichever it gives you -
do not mix the two.)

**5. Update SPF - EDIT the existing record, do not add a second.**

    v=spf1 include:_spf.google.com ~all

The hostedemail include goes because the forwarder is no longer in the path.
Shopify's own sending does not need an SPF include: it aligns via DKIM, which
is why the `_domainkey` selectors matter and SPF does not.

**6. Turn off Shopify email forwarding** for hello@ (Settings -> Domains ->
Email forwarding). Mail is now delivered, not forwarded.

**7. Add Google's DKIM.** Workspace admin -> Apps -> Google Workspace -> Gmail
-> Authenticate email. Generate the key, publish the TXT it gives you at
`google._domainkey.wagvive.com`. Then turn authentication ON in Workspace.

**8. Optional: import the old mail.** The dedicated Gmail holds the store's
history. Workspace admin has a data migration tool, or Gmail's own
"Check mail from other accounts". Do this after the cutover.

## Verification, in this order

Do not declare it done on the wizard's green ticks. Check the live system:

    python config/verify_email_dns.py

That script (added alongside this doc) checks every layer and says which one is
wrong. Then, the two checks DNS cannot do:

* **Receive:** send a mail from an outside address to hello@wagvive.com and
  confirm it arrives in the Workspace inbox.
* **Send, and this is the one that matters:** place a real test order on the
  store. Open the confirmation in Gmail, use **Show original**, and confirm
  `DKIM: PASS` signed-by `wagvive.com` and `DMARC: PASS`. If DKIM shows
  `shopifyemail.com` instead of `wagvive.com`, the sender authentication broke
  and order mail will start getting junked.

## Afterwards

* Remove the "Send mail as" + app-password setup from the old personal Gmail.
  hello@ is a real mailbox now, and leaving a second path that can send as
  hello@ is a deliverability and confusion risk.
* Once a few weeks of real order volume have passed cleanly, consider tightening
  DMARC from `p=none` to `p=quarantine`. Not before: with `p=none` a mistake
  costs nothing, and with `p=quarantine` a mistake sends real order
  confirmations to spam.
* Update `docs/knowledge/wagvive-email-architecture.md`, which currently
  describes the forwarding setup and will be wrong the moment step 4 lands.
