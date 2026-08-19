---
name: cj-api-points-quota
description: "CJ has a daily API points budget, not just the documented 1 req/sec throttle; a heavy session can exhaust it, and every existing retry loop in this repo mistakes that for missing data"
metadata:
  type: project
---

**Found 2026-08-18**, building a script to add ten products to `price_book.json`
after a pricing review. `config/cj_api.py` already handles CJ's documented
throttle (1 request/second, HTTP 429, exponential backoff). It has no concept
of the OTHER limit: a daily points budget.

## What actually happened

CJ returns this as a normal 200 response, not an HTTP error:

```json
{"result": false, "code": 16900500,
 "message": "Insufficient API points. Used today: 104890, Remaining: 0, Required: 10. ...",
 "data": null}
```

`cj_api.call()` doesn't inspect `result` or `code` - it just returns the parsed
JSON. Every script that calls it does `.get('data') or {}`, which reads that
exhausted-quota response identically to a genuine "nothing found." A retry loop
built to survive CJ's well-known habit of returning an empty answer for no
reason (see `docs/knowledge/wagvive-*` and the guard scripts) retried this
condition 4 times per SKU across dozens of SKUs, could not ever succeed, and
produced a CONFIDENT, WRONG number: the Glow Skeleton Suit reported "worst
margin today 53.4%" from the ONE variant (of four) that happened to resolve
before the wall was hit, when the real worst-variant margin, computed earlier
the same session with a complete read, was 27.8%. Trusting that number would
have written a floor into `price_book.json` almost twice as generous as reality
- exactly the kind of quiet miscalibration this repo's floor system exists to
prevent.

## How the quota actually works (per CJ's own points documentation)

- Daily total = 50,000 base points + order-conversion points (`$1 of the last
  3 months' transactions = 100 points`).
- Most product-data endpoints (`/product/query` and similar) cost **10 points
  per call**. Broader listing endpoints cost more; endpoints not listed cost 0.
- Replenishment is **continuous, not a fixed daily reset**: CJ restores
  `daily total / 1440` points every minute. A busy day empties the bucket
  faster than the trickle refills it.

This session hit `Used today: 104890, Remaining: 0` after a normal, heavy day
of work: several full-catalogue cost/freight sweeps for a pricing review, on
top of whatever the 6-hourly scheduled job (`sync_inventory.py`,
`guard_unshippable.py`, `margin_guard.py`, all CJ-heavy) already spent.
**Retrying a couple of hours later worked** - a single cheap probe call
succeeded, confirming the trickle-back model rather than a fixed reset. But the
budget was thin enough that day that even ONE more full 10-product pass
re-exhausted it within a few minutes; getting all ten products booked took
four separate `--apply` runs spaced minutes apart, each one permanently
banking whatever it resolved before hitting the wall again (see "resumability"
below). **A dry run and an `--apply` run cost the SAME CJ calls for the same
data** - running one right before the other (to "check the plan first") just
pays for the same information twice and was directly why the quota died a
second time this session. If the numbers are already trusted, skip straight to
`--apply`.

## The operational risk this creates — CONFIRMED, it happened the next day

**The scheduled job depends on CJ too.** If the quota is exhausted when
`scheduled-ops.yml` next fires, `sync_inventory.py --apply`,
`fix_locations.py --apply` and `guard_unshippable.py --apply` will all be
querying CJ into the same wall. None of them currently distinguish
"quota exhausted" from "CJ returned nothing," so a run in this state risks the
exact failure mode `guard_unshippable.py`'s own docstring warns against:
treating an unanswerable SKU as a finding instead of as UNKNOWN.

**2026-08-19: this is no longer hypothetical.** `Scheduled store operations`
failed and emailed the owner. `margin_guard.py` was the step that failed, and
the breach it reported was fiction:

* `best_freight()` had **no retry at all**. One transient empty response was
  enough to fall through to `freight_floor.resolve([])`, which substitutes the
  $11.00 no-quote fallback.
* The Pumpkin Hoodie 9XL reads **29.3%** margin on its real $7.10 quote and
  **4.2%** on that fallback, against a 21.3% floor. Instant "breach."
* `main()` set an `estimated` flag on every freight result and then **never
  read it**, and its one guard, `if not fr:`, was dead code, because
  `best_freight()` always returns a dict.

A full `margin_guard.py` run the following morning, with CJ healthy, returned
`258 variants checked, 0 breaches, All variants clear their floors` — proving
no price was ever actually wrong.

Fixed in `margin_guard.py`:

1. `best_freight()` retries three times before believing CJ has nothing, and
   returns `answered` alongside `estimated`. These are different questions:
   **empty after retries** = CJ did not answer, unknowable, treat as UNRESOLVED;
   **`$0`/placeholder** = CJ answered with missing data, a stable documented
   condition (the US-warehoused Ball Launcher does it every call), so the
   fallback stands and the variant is still judged.
2. Quota exhaustion raises `CJUnavailable` immediately rather than being
   retried into — it cannot succeed and retrying every remaining variant costs
   ~36 minutes, which would blow the workflow's 50 minute timeout and turn a
   clean diagnosis into an opaque timeout.
3. `OUTAGE_STREAK` (15 unanswered in a row) aborts the sweep for generic
   outages that do not announce themselves.
4. `MIN_COVERAGE` (80%) fails the job as **"COULD NOT VERIFY"** if too few
   variants got a real answer. This closes the hole the other fixes would
   otherwise open: treating unanswered as UNKNOWN is right, but without a
   coverage floor a total outage would make every variant UNKNOWN and the job
   would exit 0 having checked nothing. The message says explicitly that it is
   a coverage problem, not a margin problem — they need opposite responses.

Verified by simulation: with CJ mocked as fully quota-exhausted the job now
exits 1 in **0.6 seconds** with "COULD NOT VERIFY … This is NOT a margin
breach", instead of grinding for 36 minutes and reporting invented breaches.

**Cadence was also halved, 6-hourly to 12-hourly**, partly for this: the job
makes ~300 CJ calls per run and was one of the largest consumers on the
account, so it was contributing to the very exhaustion that broke it.

## How to apply

- **Recognise the signal**: `result: False` and `code: 16900500` (or the
  literal string "Insufficient API points" in `message`) with `data: None`,
  delivered as an ordinary 200 response CJ's own retry-for-429 logic will never
  catch.
- **Stop, don't retry.** Retrying into an exhausted quota cannot succeed and
  burns the retry budget that would otherwise catch CJ's genuine transient
  empty-answer behaviour. `config/book_fall_lineup.py`'s `cj_query()` wrapper
  raises `QuotaExhausted` immediately on this signal so the run aborts with a
  clear message instead of finishing and printing plausible-looking numbers
  built on partial data.
- **Don't trust a partial result as a worst case** - UNLESS enough of the
  weight/cost tier that actually produces the worst margin resolved anyway.
  In practice apparel variants of the same SIZE share cost and freight across
  colours, so if even one colour of the heaviest size resolves, the true worst
  case is still captured even when most other variants of that product timed
  out. Confirmed by cross-checking every number this session's partial runs
  produced against fully-resolved runs computed hours earlier: all matched
  exactly. Still, treat a run with many `unresolved` variants as lower
  confidence than a clean one, and re-verify against a complete read when the
  quota allows it.
- **Make the caller resumable, not just safe.** The real fix that got all ten
  products booked despite a thin, repeatedly-exhausted budget was restructuring
  `book_fall_lineup.py` so a `QuotaExhausted` mid-run does not discard already-
  resolved entries: it books whatever succeeded and stops, and because every
  entry point already skips `if str(p['id']) in book`, the NEXT run only pays
  for what is still missing. Four short, cheap runs (banking 4, then 2, then 3,
  then the last 1 product) finished what one long run repeatedly could not.
- **Recovery is gradual, not a fixed time.** Points trickle back roughly once a
  minute; there is no single "wait until midnight" moment, but a real recovery
  IS available within a couple of hours of lighter usage, not just "tomorrow."

## One more real bug this surfaced, unrelated to CJ

While cleaning up around this, found that `config/add_fall_lineup.py` and
`config/add_fall_wave2.py`'s `finish()` steps had been writing floor entries
into `price_book.json` keyed by **product HANDLE**
(`book.setdefault(spec['handle'], {})['floor_margin_pct'] = ...`) instead of by
**numeric product ID**, which is what every reader
(`margin_guard.py`'s `BOOK_FLOOR`, `calibrate_floors.py`) actually looks up by.
Ten handle-keyed stub entries - containing only `floor_margin_pct`, no title,
price or variants - sat in the book for 8 months, completely inert: every
lookup by `str(product['id'])` missed them, so all ten fall/wave2 products ran
on `margin_guard.DEFAULT_FLOOR` (25%) the entire time despite the code visibly
"setting" a real floor at launch. This is the SAME root cause this whole
pricing review exists to fix, just with a code bug behind it rather than a
missing step. Fixed in both scripts (now keys by `str(p['id'])` and writes the
full entry shape), and the ten dead stubs were removed from `price_book.json`
once the real, numeric-ID-keyed entries existed to replace them.

## Still open

`cj_api.call()` itself does not yet distinguish the quota-exhaustion condition
from any other response shape - every OTHER script in this repo that calls it
(`margin_guard.py`, `guard_unshippable.py`, `sync_inventory.py`,
`calibrate_floors.py`, and more) has the same blind spot `book_fall_lineup.py`
had before this was found. Hardening `cj_api.call()` itself to raise on this
signal, once, rather than fixing each caller individually, is flagged as a
follow-up task rather than done here - it touches the module every CJ-facing
script imports.
