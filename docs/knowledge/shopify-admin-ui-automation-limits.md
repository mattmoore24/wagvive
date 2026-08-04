---
name: shopify-admin-ui-automation-limits
description: "Which Shopify admin surfaces can and cannot be driven by automation, and the background-tab wall that blocks the rest"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 07b37851-ac47-448b-b4a5-0b479e8e1101
  modified: 2026-08-03T00:47:58.969Z
---

Learned 2026-08-02 while trying to edit Wagvive's notification templates.

**Notification email templates have NO API.** Not REST, not GraphQL. Probed the
2026-07 schema: the only notification-adjacent mutations are
`customerSendAccountInviteEmail`, `giftCardSendNotificationToCustomer` and
friends — nothing that reads or writes a template body. `shop.brand` does not
exist on this API version either, so brand assets can't be set programmatically.
Templates are admin-UI only: Settings → Notifications → <template> → Edit code.

**The background-tab wall.** `admin.shopify.com/store/*/settings/*` is
same-origin and has no iframes (unlike `online_store/preferences`, which is a
cross-origin `online-store-web.shopifyapps.com` iframe and unscriptable). So
settings pages *look* automatable — but the React route content **never mounts
while the tab is hidden**: `document.body.innerText.length` stays ~330 (chrome
only, no page content) no matter how long you wait, while `document.title`
updates correctly. Nav `<a href>`s exist; the settings panel does not.
`claude-in-chrome` has tabs_create/close/context but **no tabs_select**, so
there is no way to foreground a tab — only the user can. Anything requiring
rendered admin settings content therefore needs the user to bring the tab up and
keep it visible.

**What DOES work headlessly** for this store: everything through the Admin API —
products, variants, images, media, collections, policies (except auto-managed
ones, see below), theme assets and templates, inventory, discounts, orders,
fulfillments. Prefer the API every time; reach for the browser only when no API
exists.

**Auto-managed policies** reject `shopPolicyUpdate` with "Automatic management
for Privacy Policy must be turned off". Fix via `privacyFeaturesDisable(
featuresToDisable:[PRIVACY_POLICY])` — enum also has COOKIE_BANNER and
DATA_SALE_OPT_OUT_PAGE, leave those on. Side effect: that policy stops receiving
Shopify's automatic legal updates.

**Rate limit that bites long scripts:** REST is 2 calls/sec and answers 429.
`config/fix_locations.py` walks every variant and died silently on this —
made worse because the shell pipeline `python … | tail -12` returned exit 0 and
swallowed the traceback. **Never pipe a long-running script through `tail`
when you need its exit status.** All catalogue-walking scripts now carry
`time.sleep(0.55)` per call plus 429 backoff.

See [[horizon-theme-json-traps]] for the storefront-side equivalents and
[[cj-inventory-sync-model]] for the inventory location rules.
