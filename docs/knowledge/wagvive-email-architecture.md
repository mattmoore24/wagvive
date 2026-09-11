---
name: wagvive-email-architecture
description: "How hello@wagvive.com is wired: a Google Workspace mailbox since 2026-09-10, exact live DNS records, and the three cutover traps"
metadata: 
  node_type: memory
  type: project
  modified: 2026-09-10
---

Set up 2026-08-02 as Shopify forwarding; **MIGRATED TO GOOGLE WORKSPACE
2026-09-10.** wagvive.com is a **Shopify-managed domain** (bought through
Shopify; DNS zone hosted by Shopify on Google Cloud DNS, nameservers
`ns-cloud-e1..e4.googledomains.com`). Shopify admin reports these as "Shopify's
default nameservers" - they ARE Shopify's, backed by Google Cloud DNS. All DNS
edits happen in Shopify admin -> Settings -> Domains -> wagvive.com -> DNS
settings. There is NO Admin API mutation for DNS (checked 2026-09-10: 470
mutations, none for DNS), so edits are browser-only.

**Mail flow:** hello@wagvive.com is a real Google Workspace mailbox (the
primary `hello` user). MX delivers straight to Google. The old Shopify
forwarding alias into a dedicated Gmail is no longer in the mail path.

**Records live, verified 2026-09-10 at all four authoritative nameservers:**
- MX 1 `smtp.google.com`
- TXT `@` `v=spf1 include:_spf.google.com ~all` (exactly ONE v=spf1)
- TXT `@` `google-site-verification=...` (Workspace domain verification)
- TXT `_dmarc` `v=DMARC1; p=none`
- TXT `google._domainkey` `v=DKIM1; k=rsa; p=...` (Google's signing key)
- Shopify's DKIM, as CNAMEs: `05n._domainkey`, `05n2._domainkey`, plus
  `mailer05n`, `mailer6qe`, `pdk1._domainkey.mailer6qe`,
  `pdk2._domainkey.mailer6qe`. These sign ORDER CONFIRMATIONS as wagvive.com.
  Never delete them.

**Shopify notifications:** sender email = hello@wagvive.com (shop.json
`customer_email`). Order confirmations authenticate via Shopify's DKIM
selectors above, NOT via SPF, which is why the migration could not break
sending. Ground truth for alignment: Gmail "Show original" on a store
notification should show DKIM: PASS signed-by wagvive.com.

**Three traps hit during the 2026-09-10 cutover:**
1. SPF was DELETED instead of edited, and DMARC went with it. MX and DKIM were
   right, so nothing looked broken. Only `verify_email_dns.py` caught it.
2. The Shopify DNS panel can show STALE records. It listed the old
   hostedemail MX and old SPF while every authoritative nameserver already
   served smtp.google.com. Hard-reload before trusting it; trust the
   nameservers over the panel.
3. The "Add custom record" dialog opens from a background tab, but typing does
   not reach its fields. Keystrokes fall through to Shopify's global shortcuts
   (one run opened an unsaved "Add blog" form). Coordinate clicks work; typing
   needs the tab in the foreground.

**How to apply:** check layers with `python config/verify_email_dns.py`, which
exits 0 only when all six pass. If deliverability drops: MX still Google ->
single SPF -> Shopify CNAME selectors present -> Google DKIM present -> DMARC.
Consider `p=quarantine` only after a few weeks of clean order volume.
See [[shopify-admin-ui-automation-limits]] and [[horizon-theme-json-traps]].
