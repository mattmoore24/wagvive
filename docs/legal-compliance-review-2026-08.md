# Legal and compliance review, 2026-08-04

Full review of the store's policies and customer-facing legal surfaces, with
what was fixed, what the owner still has to decide, and what does not apply yet
but will if the store grows.

**This is not legal advice.** It is a careful non-lawyer review against
published regulator guidance, done so that the obvious gaps are closed and the
genuinely uncertain ones are visible rather than invisible. The items in
section 4 are worth a lawyer's hour before scaling ad spend.

Business as reviewed: Wagvive, 333 Pearl St, New York, NY 10038. US-only
shipping. Dropshipped pet accessories fulfilled by CJ from overseas.
No subscriptions, no user accounts required, no children's products.

---

## 1. What was wrong, and is now fixed

### 1.1 The Shipping Policy contradicted the checkout (most serious)

The published Shipping Policy said **"Free standard shipping on orders over
$50."** The live delivery profile has charged free shipping over **$60** since
the threshold was raised. Every customer between $50 and $60 was told one thing
by the policy and charged $5.95 at checkout.

This is the worst category of error on the list, because a price representation
that does not match what is charged is a deception exposure under Section 5 of
the FTC Act, not merely a support annoyance.

Fixed, and made structurally hard to repeat: `config/write_policies.py` now
imports `config/shipping_rates.py` and **refuses to publish** if the two
disagree. The same number can no longer drift in two files.

### 1.2 No cancellation right written down (FTC Mail Order Rule)

The FTC's Mail, Internet, or Telephone Order Merchandise Rule (16 CFR Part 435)
requires a seller who cannot ship within the time it stated, or within 30 days
if it stated none, to seek the buyer's consent to the delay and, if consent is
not given, to **refund promptly**. Civil penalties are per violation.

Our stated window is 1 to 3 business days of processing plus 5 to 12 business
days of delivery, which is comfortably inside 30 days, so the rule's default
never bites. But the buyer's right to cancel a delayed order was not written
anywhere. It is now in both the Shipping Policy and the Refund Policy.

### 1.3 Terms of Service was missing every clause that does work

The old Terms were twelve short paragraphs. Missing entirely: governing law and
venue, disclaimer of implied warranties, limitation of liability, indemnity,
intellectual property, user-content terms and licence, acceptable use, age and
capacity, links to third-party sites, force majeure, severability, entire
agreement, assignment, and consent to electronic communications.

All added, in the same plain voice, with the two that matter most made
conspicuous as the UCC expects: the **as-is warranty disclaimer** and the
**liability cap at the amount paid for the order**. Governing law is New York,
venue New York County.

### 1.4 The footer had no links at all

The live footer contained an email signup and nothing else. A Footer menu with
twelve items existed in admin and had never been wired to a block, so every
policy link, the contact page, and the state-privacy opt-out link rendered
nowhere on the storefront.

That is a compliance problem (an opt-out link that cannot be found is not
conspicuous), a trust problem, and a plain navigation problem. Rebuilt with
three columns (Shop, Help, Company) plus a business-identity line. The theme
appends its own policy row automatically, so no policy column is added by hand,
which would render every policy link twice.

### 1.5 No Proposition 65 notice

California requires a clear and reasonable warning **before** exposing a person
in California to any of roughly 900 listed chemicals. Imported goods are not
Prop 65 compliant by default; suppliers only ensure it when asked to. Our range
is imported plastics, silicone and textiles, and we hold neither test reports
nor supplier certificates.

A notice now exists at `/pages/proposition-65`, is linked from the footer and
the Terms, and is written to be honest about what a warning does and does not
mean. **See section 3.1: this is the weaker form of compliance and there is a
decision to make.**

### 1.6 The Creator programme had no disclosure requirement

Under the FTC Endorsement Guides (16 CFR Part 255) an endorser must disclose a
material connection, and the **advertiser is exposed for failing to instruct and
monitor** its affiliates. The page asked for applications and said nothing about
disclosure at all.

Rewritten with explicit requirements: disclose in the post itself and not only
in a bio, say it out loud and on screen in video, do not claim a product treats
or prevents any condition, use only material you own, and we review and end
partnerships that do not comply. It also no longer pitches "senior pet care",
which stopped being the positioning when the Senior Dog Kit was retired.

### 1.7 No accessibility statement

Ecommerce sites are 69 to 77 percent of US digital accessibility lawsuits,
Shopify stores are roughly a third of platform-specific ones, and about 64
percent of defendants are businesses under $25M revenue. A statement is not a
defence, but a named contact and a stated standard are the first things a demand
letter looks for, and it is how a real user reports a real barrier.

Added at `/pages/accessibility`: WCAG 2.1 AA as the target, an honest admission
that the theme and third-party tools can regress, a contact route, and an offer
to complete any order over email.

### 1.8 British spelling on a US store

23 product option names read "Colour", the swatch label on every product page.
Also "fulfilment" in the Shipping Policy, the FAQ and the Shipping & Returns
page, plus "odour" and "centre" in product copy. All corrected, and the source
scripts that would recreate them were fixed too.

---

## 2. Checked and already fine

| Area | Finding |
|---|---|
| Privacy Policy | Shopify's auto-managed policy, current, covers collection, use, disclosure, state rights, GPC. 16,931 characters. No changes needed. |
| State privacy opt-out | `/pages/data-sharing-opt-out` exists, honours Global Privacy Control, now linked in the footer. |
| Refund policy | Already strong: 30 days, we pay return shipping on our errors, no restocking fee, statutory rights preserved. Added exchanges and the delay-cancellation right. |
| Product health claims | Scanned all 36 products for medical, curative and guarantee language. **No medical claims found.** Copy is descriptive and experiential ("light, even pressure has a naturally calming effect", "lift plaque and freshen breath"), which is category-normal and defensible. Nothing claims to treat, prevent or cure. |
| Transactional email | Order and shipping notifications are transactional, so CAN-SPAM's advertising rules do not apply to them. Sender is verified and DKIM-signed. |
| Support address | hello@wagvive.com is the only customer-facing address across every surface. |
| Subscriptions and auto-renewal | None sold, so ROSCA and state auto-renewal laws do not apply. |
| Children's products | None. CPSIA lead and phthalate limits for children's products do not apply to pet accessories. |
| Sales tax | NY registration is still outstanding, tracked separately as task #57. That is a filing the owner must do personally. |

---

## 3. Decisions the owner needs to make

### 3.1 Proposition 65: how far to go

Three options, in increasing cost and decreasing risk:

1. **Where we are now.** A site-wide notice page linked from the footer and the
   Terms. Cheap, honest, and better than nothing, but Prop 65 expects the
   warning to be given before purchase of the affected product, so a linked
   page is the weakest form. Realistically this is what most small importers do.
2. **Ask CJ for compliance certificates** per SPU. Free, slow, and the answer is
   often unusable, but it costs only a support ticket and it is the natural
   companion to the DDP question already open as task #64.
3. **Lab test the highest-risk items** (anything vinyl, PVC, painted, or with a
   soft plasticised feel) and warn only where needed. Roughly $150 to $400 per
   item at a Chinese lab. Only worth it once volume justifies it.

**Recommendation:** do (2) now as part of the same CJ conversation as task #64,
keep (1) in place regardless, and revisit (3) when a single product's monthly
volume makes it worth the money.

### 3.2 Arbitration clause: deliberately not added

Many US ecommerce Terms include mandatory arbitration with a class-action
waiver. It is a genuine shield, but it has to be drafted carefully to be
enforceable, it needs a conspicuous acceptance flow, and a badly drafted one is
worse than none. I have written a clean informal-resolution-then-New-York-courts
clause instead. If the store scales, this is the first thing to have a lawyer
add.

### 3.3 Duties and customs: still unresolved

Nothing in any policy says anything about customs, duties or import charges.
That silence is deliberate. The margin model assumes duties are included (DDP)
but this is **unconfirmed with CJ** (task #64). A "no surprise charges" promise
the business cannot verify would be worse than saying nothing. Resolve task #64,
then say plainly whichever is true.

### 3.4 Business entity

Policies name "Wagvive" and a New York address. If the business is not yet an
LLC or corporation, the owner is personally liable for everything above.
Forming an entity is the single highest-value legal step available and it is
cheap in New York relative to the protection.

---

## 4. Does not apply yet, but will

None of these bind the store today. They are listed with their trigger so the
first one to become relevant is not a surprise.

| Law | Trigger | Status |
|---|---|---|
| **CCPA / CPRA** (California) | Over $26.625M revenue, OR buying/selling/sharing the personal information of 100,000+ California consumers a year, OR 50%+ of revenue from selling personal information | Not met. But we already publish the policy and honour GPC, so the practical work is done. The 100,000 threshold counts trackable website visitors, not just customers, so **advertising at scale is what would trip this first.** |
| Other state privacy laws (Virginia, Colorado, Connecticut, Texas, Oregon, Montana and others) | Similar volume thresholds, typically 100,000 consumers, some 25,000 with sale of data | Not met. Same practical position as CCPA. |
| **CAN-SPAM** | Any commercial (marketing) email | **Applies the moment marketing email starts.** Every marketing message needs honest headers, a working unsubscribe honoured within 10 business days, and a physical postal address. Maximum penalty is over $53,000 per non-compliant email. The postal address is now published in the Contact policy and the footer. |
| **TCPA** | Any marketing SMS | Applies the moment SMS marketing starts. Requires prior express written consent, which means a separate opt-in, not a pre-ticked box bundled with email. |
| FTC Endorsement Guides | Any paid creator or affiliate | Applies as soon as the first creator posts. Requirements now stated on the programme page. |
| European Accessibility Act | Selling into the EU | We ship US only, so it does not apply. It would from the first EU order. |
| Textile labelling (16 CFR 303) | Household textiles for human use | Pet blankets and robes are not human household textiles, so it does not apply. |

---

## 5. What changed, file by file

| File | Change |
|---|---|
| `config/write_policies.py` | Rewrote Shipping, Refund, Terms, Contact. Added the shipping-threshold cross-check that refuses to publish on a mismatch. Added the business postal address. |
| `config/compliance_pages.py` | **New.** Creates `/pages/proposition-65` and `/pages/accessibility`, rewrites the Creator programme page with FTC disclosure requirements, repairs British spelling and stale figures on other pages. |
| `config/build_footer.py` | **New.** Builds the footer menus and wires them into the footer section. Verifies through the section-rendering API rather than the cached homepage. |
| `config/americanize_colour.py` | **New.** Renamed 23 product option names and swept every customer-facing surface. |
| `config/fix_home_faq.py` | **New.** Replaced the stale senior-dog FAQ row. |
| Live store | 4 policies rewritten, 2 pages created, 3 pages repaired, 3 footer menus created, 23 product options renamed. |

---

## 6. One thing to know about verifying theme changes

The homepage HTML cache served **pre-change renders for over seven minutes**
after the footer write, alternating between two different old versions across
edge nodes. A cache-busting query parameter did not help, because the parameter
is not part of the cache key.

The reliable check is the **section rendering API**:

```bash
curl -s "https://wagvive.com/?sections=sections--27042989867297__footer_m9NzUG"
```

It re-renders server side and returns the truth immediately. `build_footer.py`
now verifies this way. This generalises to any theme section, and it is the
counterpart to the `?nocache=` advice already in CLAUDE.md, which works for
policy and page writes but **not** for cached section HTML.
