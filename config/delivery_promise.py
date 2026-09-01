#!/usr/bin/env python3
"""THE delivery promise. One definition, imported everywhere it is stated.

Before this file existed the promise was typed as a literal into more than
thirty places - nine product-creation scripts, two theme templates, four
notification emails, three shop policies, the checkout rate description and a
CI workflow that rewrote it unconditionally on every push. They had already
drifted into two CONTRADICTORY promises on the same product page: a flat
total ("Arrives in 5 to 12 business days") and a compound one ("Dispatched in
1 to 3 business days... 5 to 12 after dispatch", which totals 15). Measured
deliveries of ~10, ~13 and ~14 business days were inside the compound reading
and outside the flat one, so the store was simultaneously keeping and breaking
its own word.

WHY THESE NUMBERS (2026-08-31, from docs/knowledge/cj-delay-diagnosis-2026-08.md):

Three real orders were measured end to end against CJ's tracking API. All
delivered: ~10, ~13 and ~14 business days door to door. The time is NOT lost
in transit, which runs a normal ~6 day air lane. It is lost before the parcel
exists: first carrier scans came 4.9, 8.8 and 11 CALENDAR days after the order.

  DISPATCH_DAYS = 10 business days is the load-bearing number. It is the FTC
  representation (16 CFR 435.2: a merchant must have a reasonable basis for its
  stated shipment time), and it clears all three observed dispatches with
  headroom. The retired "1 to 3 business days" had no reasonable basis and was
  breached on at least two of three orders.

  PROMISE_DAYS = 16 business days door to door. Observed max is ~14 on n=3,
  and CJ quotes no ceiling anywhere for its handling step, so this is an
  extrapolation from a small sample rather than a supplier commitment.
  RE-DERIVE IT after ~20 orders and be willing to widen again.

DO NOT CONFUSE THIS WITH `freight_floor.MAX_DAYS`, which is 12 and should stay
12. That constant is a TRANSIT-ONLY carrier ceiling used to pick a carrier and
to price freight; it has never included CJ's handling step, which is exactly
why `guard_unshippable.py` could certify all 145 variants "inside the promise"
on orders that breached it. Widening MAX_DAYS to match this promise would hand
the extra headroom to CJ to spend on slower, cheaper carriers and reproduce the
same breach at a wider promise. Changing it is a deliberate cost/speed decision
with a margin re-run, never a side effect of a copy edit.

HOUSE STYLE (CLAUDE.md non-negotiable #4): ranges are written with "to", never
a hyphen or dash. "10 to 16 business days", never "10-16".

TAG SHAPE IS LOAD-BEARING. `apply_size_guides.py` anchors on the exact shape
`<p><strong>Arrives in ...</strong></p>` at its `strip_old` lookahead and its
`insert` search, with a silent `html + blk` fallback. Change the NUMBER inside
that shape freely; change the SENTENCE STRUCTURE and the size guide stops being
replaced and starts being duplicated across 15 sized products, with no error.
"""

# --- the numbers ------------------------------------------------------------
DISPATCH_DAYS = 10   # business days to hand the parcel to a carrier (the FTC representation)
PROMISE_DAYS = 16    # business days door to door (what the customer is told)
PROMISE_MIN = 10     # bottom of the published range

# --- the strings ------------------------------------------------------------
WINDOW = f'{PROMISE_MIN} to {PROMISE_DAYS} business days'
DISPATCH_WINDOW = f'within {DISPATCH_DAYS} business days'

# The product-page anchor. KEEP THE TAG SHAPE (see above).
DELIVERY = f'<p><strong>Arrives in {WINDOW}.</strong></p>'

# The honesty line that follows it. Deliberately says "fulfilment partner", not
# "our overseas warehouse": the warehouse is CJ's, not ours, and claiming it as
# ours would be the kind of small untruth this whole exercise exists to remove.
DELIVERY_NOTE = (
    '<p>We ship direct from our overseas fulfilment partner rather than holding '
    'stock in the US, which is how the price stays where it is. Your tracking '
    'link is emailed when the parcel is handed to the carrier, and it can be '
    'quiet for the first week or so while your order is being packed.</p>'
)

# What a product body gets. Both parts, in this order.
DELIVERY_BLOCK = DELIVERY + DELIVERY_NOTE

# Checkout rate descriptions (config/shipping_apply.py).
CHECKOUT_FREE = f'{WINDOW}. Free on orders over $60.'
CHECKOUT_FLAT = f'{WINDOW}.'

# Plain-text form for emails and policies.
PLAIN = f'Arrives in {WINDOW}.'


# --- what a stale claim looks like ------------------------------------------
# Every retired promise this store has published. `audit_claims.py` and
# `fix_size_copy.py`-style verifiers should treat a live match as a failure.
# Kept as data so the next change adds one line rather than editing regexes in
# four files.
RETIRED = [
    '5 to 12 business days', '5-12 business days',
    '5 to 11 business days', '5-11 business days',
    '1 to 3 business days', '1-3 business days',
]


def is_stale(text):
    """Which retired promises appear in this text."""
    return [r for r in RETIRED if r in (text or '')]
