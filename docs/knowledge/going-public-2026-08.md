# The repo is PUBLIC (2026-08-19): why, what was scrubbed, and the new rules

Owner decision, made to get unlimited GitHub Actions minutes after the
scheduled job's 6-hourly cadence (~2,675 min/month) overran the private-repo
Free allowance (2,000). The owner's reasoning, accepted after audit: the
business data (CJ costs, margins, pricing model) is reconstructable from
public information anyway - CJ prices are visible to any account, and margins
follow from public retail prices. The one hard blocker found was a leaked
credential, which was killed rather than argued about.

## What was found and fixed before flipping

**A live Shopify app `client_secret` was in git history from the initial
commit.** `.claude/settings.local.json` - Claude Code's approved-commands
allowlist - had recorded the full OAuth `curl` from initial setup, embedding
`client_id` 9cfc0047... and its `shpss_` client_secret. The file was tracked in
HEAD, so the secret was in every commit.

Resolution, in order:

1. **Identified which app the secret belonged to.** Critical step:
   `currentAppInstallation` via GraphQL showed the LIVE automation token
   belongs to "Wagvive Ops" (apiKey 779ece...), while the leaked secret
   belonged to "Wagvive Automation" (9cfc0047...) - a setup-era leftover that
   nothing referenced. Shopify cannot rotate admin-created custom app
   credentials (delete-and-recreate is the only option), so if the leaked app
   HAD been the live one this would have meant re-issuing the Admin token and
   updating GitHub Secrets + local .env. It was not.
2. **Owner deleted "Wagvive Automation"** - the leaked secret is permanently
   dead. This, not the scrub, is the security fix.
3. **Full history scrub** with `git filter-repo --replace-text`: the secret,
   the OAuth authorization code, and `wagvive.inbox@gmail.com` replaced across
   all 169 commits. Backup bundle taken first
   (`../wagvive-pre-scrub-backup.bundle`, local only, contains the PRE-scrub
   history - treat it as sensitive).
4. **Force-pushed main**, then verified with a FRESH CLONE - which caught a
   stale remote branch (`claude/project-progress-check-2mb93r`, an Aug 6
   snapshot) still serving the old history. Deleted it; second fresh clone
   verified **zero occurrences across every ref the remote serves**.

## Two residual facts, both acceptable and both verified rather than assumed

* **Old pre-rewrite commits are still fetchable by direct 40-char SHA** until
  GitHub garbage-collects (confirmed live: `git fetch origin <old-sha>`
  succeeds and the secret is in that ancestry). Harmless because the app is
  deleted; GitHub Support can GC on request if wanted.
* The owner's personal Gmail appears in one knowledge doc. It is also the
  public GitHub account email, so no new exposure.

## What did NOT leak, verified across all history

No `shpat_` Admin token, no CJ API key, no AWS/GitHub/OpenAI/Slack keys, no
private keys, no customer or order PII. GitHub Actions secrets live outside
the repo and remain private on a public repo. No workflow has `pull_request`
triggers, so forks cannot reach secrets or trigger runs.

## THE NEW RULES - a public repo changes daily behaviour

1. **Every commit is world-readable the moment it is pushed.** The margin for
   error on secrets is now zero. Secret scanning + push protection are ON
   (Settings -> Code security) and must stay on; push protection blocks a
   detected secret BEFORE it becomes public.
2. **`.claude/settings.local.json` is gitignored and must stay untracked.**
   It records approved Bash commands verbatim, which is how the secret leaked.
   Never commit it, never weaken that ignore rule.
3. **Watch what goes in QA logs and docs.** Costs and margins are accepted as
   public now, but customer names, emails, order details, or anything from the
   Shopify admin about actual PEOPLE must never be committed - that was true
   before, and is now enforced by the whole internet.
4. **The live token is over-scoped. OPEN FOLLOW-UP, deliberately deferred
   2026-08-19.** Wagvive Ops grants **183 scopes**, including `read_all_orders`
   and full customer data, against roughly 29 the automation actually uses
   (`config/verify_scopes.py` lists the real requirement in `NEEDED`, and
   currently reports all four capability groups READY with every endpoint probe
   passing - nothing is broken, it is purely excess privilege).

   **Why it was NOT done at the same time as going public:** the exposure did
   not change. The token was never in the repo and still is not - it lives only
   in gitignored `.env` and GitHub Secrets, both of which stay private on a
   public repo. Going public raised the cost of a FUTURE mistake, not the
   current risk on this token.

   **Why it is not a five minute job.** Wagvive Ops is an admin-created custom
   app, and per Shopify's docs those cannot have credentials or scopes changed
   in place: you must UNINSTALL AND REINSTALL, which issues a NEW access token
   and interrupts requests and webhooks until the new value is in place. So the
   real sequence is: narrow scopes -> reinstall -> new token -> update the
   `SHOPIFY_ADMIN_API_TOKEN` GitHub Secret AND `config/shopify.env` -> re-run
   `config/verify_scopes.py` -> confirm the scheduled job passes. Live
   automation is down in between.

   **When to actually do it:** bundle it with other Shopify admin work so the
   interruption is taken once. The trigger that should force it regardless is
   **real order volume** - `read_all_orders` plus customer scopes on an
   over-broad token is a theoretical liability at 1 test order and a genuine
   one once real customer data exists. Do it BEFORE volume arrives, not after.
5. **Actions minutes are unlimited; CJ points are not.** The scheduled job is
   back at 6-hourly. If cadence pressure ever returns it will come from CJ's
   points budget, and the fix there is deduplicating the two guards' identical
   freight passes (saves 50% of the job's CJ calls), not repo visibility.
