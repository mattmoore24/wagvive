# A CJ product can lose its cheap carriers overnight, and the margin goes with it

**Found 2026-08-31**, after the scheduled `Scheduled store operations` job had failed
14 consecutive times over five days without anyone noticing.

## What happened

`margin_guard.py` failed every run from #94 (2026-08-26 13:25 UTC) onward. Run #93, six
hours earlier, was green. **There was no commit between them** — the last change to the
repo was 2026-08-19. The cause was entirely supplier-side.

The single breaching product was the **Wagvive 3-in-1 Steam Grooming Brush**
(SPU `CJYD2256797`, Shopify `10508797739297`, variants Pink and Red):

| | 2026-08-19 | 2026-08-31 |
|---|---:|---:|
| CJ product cost | $3.51 | $3.51 |
| cheapest promise-compliant freight | **$6.87** | **$8.31** |
| margin at $16.99 | 27.9% | **19.2%** |
| product's `floor_margin_pct` | 19.9% | 19.9% |

Product cost did not move. Freight did, by +21%, and that alone took an 8.7 point bite
out of the margin and pushed it 0.7 points under the floor.

## The actual mechanism: carrier ELIGIBILITY, not carrier PRICING

No carrier raised its rate. CJ **reclassified the product** and its cheap ordinary lines
simply stopped being offered for it. A live quote on 2026-08-31 returned only **9 carrier
options**, and every one inside the 12 business day promise is a restricted line:

```
IN  $ 8.31   5-11   CJPacket Sensitive Pro     <- cheapest compliant, what we now pay
IN  $ 8.62   5-11   CJPacket Liquid US
    $ 9.29  10-23   CJPacket Eub Special Line
    $ 9.32  10-25   Qfulfillment A line
    $10.31   8-20   CJPacket LX Sensitive Plant
IN  $10.40   6-11   CJPacket Sensitive Pro+
IN  $11.12   7-12   CJPacket Fast US
IN  $11.89    4-9   CJPacket Fast Line
    $12.88  20-60   CJPacket Liquid Line
```

Nine options where a healthy product in this catalogue quotes **27**, and the whole
compliant set is Sensitive / Liquid / Fast. This is a *steam* brush with a water
reservoir, so a liquid or sensitive-goods classification is entirely plausible and is
very unlikely to be reversed. Treat the $8.31 as the new permanent basis, not a blip.

## Why this is worth its own note

Every cost-drift story previously written up in this repo is about **reading CJ wrong** —
the `$0.00` quote that means missing data, the two stock row shapes, the empty `stock`
array, the API points quota. This one is different: **CJ answered correctly and the answer
changed.** No amount of defensive parsing would have prevented it. The only defence is
that `margin_guard.py` re-quotes freight live on every run rather than trusting a
checked-in cost, which is exactly why it caught this on the first run after the change.

## How to tell this apart from the failure modes that look identical

Three things distinguish a real supplier move from the noise:

1. **Coverage.** `margin_guard` reported `193 checked, 0 unresolved` — 100%. A quota or
   outage problem shows up as low coverage and the script says `COULD NOT VERIFY`
   explicitly. A full-coverage run with breaches is a real finding.
2. **Persistence.** It failed 14 runs in a row at the same step. Transient CJ flakiness
   does not survive the retries in `best_freight`, and it does not repeat identically for
   five days.
3. **Isolation, checked against the previous run's own log.** Diffing the `thin` list in
   `config/margin_guard_log.json` from 2026-08-19 against a fresh run gave: **94 SKUs in
   common, freight changed on 0 of them.** One product moved and nothing else did. If
   freight had shifted across the board it would have been a carrier-wide repricing or a
   bug in our own code, and the response would have been completely different.

That third check is cheap and worth repeating whenever a cost surprise appears. The log
file is committed, so the previous run is always available via
`git show HEAD:config/margin_guard_log.json`.

## Consequence for pricing

At the new freight the price ladder is:

| price | margin | margin under stress (cost +10%, freight +15%) |
|---:|---:|---:|
| $16.99 | 19.2% | 9.1% |
| $17.14 | 19.9% | 9.9% |
| $17.99 | 23.5% | 14.0% |
| $18.36 | 25.0% | 15.6% |

$17.14 is the arithmetic minimum and is the wrong answer: it clears the floor by 0.0
points and re-breaches on the next small move, putting the job straight back to red.

**The commercial problem this exposes is bigger than the arithmetic.** The observed market
for this product, recorded in `config/reprice_fall_lineup.py`, is **$9.99 to $13.98**
(TIJITY $13.98, Steamy Pet Brush $12.59, generic $9.99). The store already sells it at
$16.99 — above every observed competitor — because $16.99 was never a market price, it was
the price needed to clear 25% margin on the old freight. Raising it further improves the
margin on a product that was already priced out of its market.

So the honest framing is that this product's economics depend on a cheap carrier it no
longer has. Raising the price stops the alarm; it does not make the product competitive.
Re-sourcing it or retiring it is the real decision, and it is the owner's.

## Rule

**When a margin breach appears with full coverage, quote the carrier list before touching
the price.** The number that moved tells you *that* something changed; the carrier list
tells you *what*, and whether it is permanent. A cost rise you can wait out and a carrier
class you have permanently lost call for different responses.
