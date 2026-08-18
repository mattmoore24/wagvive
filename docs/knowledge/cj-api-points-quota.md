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
`guard_unshippable.py`, `margin_guard.py`, all CJ-heavy) already spent. Nothing
was misbehaving; the account simply ran out.

## The operational risk this creates

**The scheduled job depends on CJ too.** If the quota is exhausted when
`scheduled-ops.yml` next fires, `sync_inventory.py --apply`,
`fix_locations.py --apply` and `guard_unshippable.py --apply` will all be
querying CJ into the same wall. None of them currently distinguish
"quota exhausted" from "CJ returned nothing," so a run in this state risks the
exact failure mode `guard_unshippable.py`'s own docstring warns against:
treating an unanswerable SKU as a finding instead of as UNKNOWN. Worth checking
the next scheduled run's log if it reports anything unusual rather than
assuming a genuine cost/inventory problem.

## How to apply

- **Recognise the signal**: `result: False` and `code: 16900500` (or the
  literal string "Insufficient API points" in `message`) with `data: None`,
  delivered as an ordinary 200 response CJ's own retry-for-429 logic will never
  catch.
- **Stop, don't retry.** Retrying into an exhausted quota cannot succeed and
  burns the retry budget that would otherwise catch CJ's genuine transient
  empty-answer behaviour. `config/book_fall_lineup.py`'s `cj_query()` wrapper
  raises `QuotaExhausted` immediately on this signal so the whole run aborts
  with a clear message instead of finishing and printing plausible-looking
  numbers built on partial data.
- **Don't trust a partial result as a worst case.** A "worst margin" computed
  from however many variants happened to resolve before the wall was hit is
  not the worst case - it is whatever subset got lucky. Treat any run that hit
  this wall as having produced NO usable number for the products it touched.
- **Recovery is gradual, not a fixed time.** Points trickle back roughly once a
  minute; there is no single "wait until midnight" moment. Practically: wait
  at least an hour of light CJ usage, or resume the next day.

## Still open

`cj_api.call()` itself does not yet distinguish this condition from any other
response shape - every OTHER script in this repo that calls it
(`margin_guard.py`, `guard_unshippable.py`, `sync_inventory.py`,
`calibrate_floors.py`, and more) has the same blind spot `book_fall_lineup.py`
had before this was found. Hardening `cj_api.call()` itself to raise on this
signal, once, rather than fixing each caller individually, is flagged as a
follow-up task rather than done here - it touches the module every CJ-facing
script imports, and the quota is at zero, so it cannot be tested live today.
