# Knowledge base

Working notes accumulated while building Wagvive. `CLAUDE.md` in the repo root is
the short, binding version — this folder is the long-form detail behind it, kept
here so a session on any device has the full history rather than the summary.

| File | What it covers |
|---|---|
| `cj-shopify-connection-procedure.md` | How to pair a product with CJ, the Angular quirks, the sync-button closure trap, carrier selection |
| `cj-inventory-sync-model.md` | The two-location problem, why CJ's webhook alone is not enough, how stock is actually kept accurate |
| `wagvive-cost-model.md` | What the 50% floor includes, and the three ways CJ freight data lies |
| `wagvive-sourcing-rules.md` | Product selection criteria, weight/freight constraints, what has been rejected and why |
| `wagvive-placeholder-product-art.md` | The Runway re-shoot pipeline and the failure modes to check every generated image against |
| `horizon-theme-json-traps.md` | Theme JSON gotchas — placeholder cards, handles vs gids, where homepage SEO actually lives |
| `wagvive-email-architecture.md` | hello@ forwarding, sender verification, DKIM, how to verify each layer |
| `shopify-admin-ui-automation-limits.md` | What has no API, the background-tab wall, rate limits |

These are point-in-time notes. If one contradicts the live system, the live
system wins — verify before acting on a detail that matters.
