---
name: wagvive-email-architecture
description: "How hello@wagvive.com is wired — Shopify domain forwarding to a dedicated Gmail, sender + DKIM state, and how to verify each layer"
metadata: 
  node_type: memory
  type: project
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-02T18:13:59.831Z
---

Set up 2026-08-02. wagvive.com is a **Shopify-managed domain** (bought through
Shopify; DNS zone hosted by Shopify on Google Cloud DNS — nameservers
`ns-cloud-e*.googledomains.com`, zone TTL 300s). All DNS edits happen in Shopify
admin → Settings → Domains → wagvive.com → DNS settings, NOT any external console.

**Mail flow:** no mailbox exists. `hello@wagvive.com` is a Shopify email-forwarding
alias (Settings → Domains → Email forwarding) delivering to a dedicated Gmail
account the user created for the store (separate from mattmoorefb24@gmail.com; ask
the user for the address if ever needed — not recorded here). Outbound replies use
Gmail "Send mail as" with smtp.gmail.com + app password, so replies show
`Wagvive <hello@wagvive.com>`.

**Records live as of setup:** MX 1 `mx.wagvive.com.cust.b.hostedemail.com`
(OpenSRS/hostedemail = Shopify forwarding backend); SPF
`v=spf1 include:_spf.hostedemail.com ~all`; DMARC `v=DMARC1; p=none`.

**Shopify notifications:** sender email = hello@wagvive.com (verified; shop.json
`customer_email` reflects it — that field is the effective sender and only flips
after the emailed verification link is clicked, not on Save). Domain is
DKIM-authenticated: Shopify publishes selectors under a NON-standard name —
probing shop1/shopify1/s1 etc. finds nothing. **To verify DKIM exists, query
`_domainkey.wagvive.com`: NOERROR/empty non-terminal = selectors present beneath;
NXDOMAIN = not authenticated.** Ground truth for alignment: Gmail "Show original"
on a store notification should show DKIM: PASS signed-by wagvive.com.

**Why:** the store's public copy already referenced hello@wagvive.com, and the
sender switch keeps order emails out of spam (new domains sending "via
shopifyemail.com" get junked).

**How to apply:** if deliverability issues arise, check layers in order:
MX intact → forward target inbox healthy → shop.json customer_email still hello@
→ `_domainkey` existence → DMARC (consider p=quarantine once volume is steady).
See [[horizon-theme-json-traps]] for the related lesson that Shopify CDN serves
mixed stale/fresh renders for minutes after changes — same patience applies to
DNS TTL 300 propagation.
