#!/usr/bin/env python3
"""What Wagvive can afford to pay for a customer. Every ad decision starts here.

An ad channel is not "good" or "bad" in the abstract. It is affordable or it is
not, and that is decided by ONE number per offer: contribution, the cash left
after goods, duty, freight, returns allowance and the payment fee. Spend more
than contribution to win an order and the order loses money no matter how good
the ROAS screenshot looks.

    contribution = price x (1 - card fee) - (landed cost + fixed fee)

Two things fall out of that, and they are the whole marketing strategy:

  1. BREAKEVEN CPC = contribution x conversion rate. At a 1% conversion rate a
     $30 contribution supports a $0.30 click. Pet CPCs run about $0.35 on
     Pinterest, $0.50 to $0.90 on Meta, $1.10 on Google Shopping and $3.00 on
     Google Search. So cold paid traffic is affordable only on the HIGHEST
     contribution offers, and only on the cheapest click sources.

  2. SINGLES CANNOT CARRY PAID TRAFFIC. Average single-product contribution is
     about $4.70, which needs a 4 to 26 percent conversion rate to break even
     depending on channel. Nothing converts at that. Singles exist to fill
     baskets, lift AOV over the free-shipping threshold and drive repeat
     purchase. Kits are the paid-acquisition product.

Run this before changing any budget, and after any repricing:

    python config/marketing/cac_ceiling.py              # full table
    python config/marketing/cac_ceiling.py --json OUT   # for the guardrail
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import pricing

# Observed 2026 US pet-category click costs, for the required-CVR table.
CPC = {'Pinterest': 0.35, 'Meta low': 0.50, 'Meta typical': 0.90,
       'Google Shopping': 1.10, 'Google Search': 3.00}

# Live kit economics: price, worst-case component goods, live basket freight.
# Freight is the LIVE quote from the 2026-08-04 kit rebuild, not the fitted
# curve, because the curve misses carrier-eligibility surcharges.
KITS = {
    'Calm & Comfort Kit': (109.0, 27.18, 28.04),
    'Travel Kit': (85.0, 21.30, 22.86),
    'Grooming Essentials Kit': (70.0, 18.42, 14.69),
    'New Puppy Kit': (54.0, 5.79, 13.95),
    'Toy Kit': (49.0, 6.62, 12.53),
    'Dog Enrichment Kit': (46.0, 9.96, 14.85),
}

# How much of contribution we are willing to spend to buy a FIRST order.
# Under 1.0 the first order is profitable on its own. Over 1.0 is a bet on the
# second order, and must not be taken until repeat rate is measured.
TARGET_PAYBACK = 0.70


def contribution(price, goods, freight):
    return price * (1 - pricing.PCT) - (pricing.landed(goods, freight)
                                        + pricing.FLAT)


def singles():
    """title -> (price, contribution) for every single product."""
    book = json.load(open(os.path.join(ROOT, 'config', 'price_book.json'),
                          encoding='utf-8'))
    recost = {r['title']: r for r in json.load(open(
        os.path.join(ROOT, 'docs', 'qa', 'recost-2026-08-04.json'),
        encoding='utf-8'))}
    out = {}
    for entry in book.values():
        r = recost.get(entry['title'])
        if not r:
            continue
        price = max(entry['variants'].values())
        out[entry['title'].replace('Wagvive ', '')] = (
            price, contribution(price, r['cost'], r['freight']))
    return out


def _assert_prices_current():
    """Refuse to run on stale kit prices.

    THE FIGURES IN `KITS` ARE A 2026-08-04 SNAPSHOT AND THIS SCRIPT SETS AD
    BUDGETS. Every kit except Grooming was repriced on 2026-09-02, and Calm &
    Comfort again on 2026-09-10, so by 2026-09-10 this file still had Calm &
    Comfort at $109 against a live $64 and the Travel Kit at $85 against $63.
    Contribution scales with price, so it was authorising roughly 70% more
    acquisition spend per order than the kits can actually fund - the exact
    failure the module docstring above warns about, committed by the tool meant
    to prevent it.

    Failing loudly is the only safe behaviour here: a silently wrong CAC ceiling
    looks exactly like a right one and is only discovered by losing money.
    """
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from kit_colorways import KITS as LIVE          # the kit source of truth
    drift = []
    for name, (price, _g, _f) in KITS.items():
        live = LIVE.get(name)
        if live is None:
            drift.append(f'{name}: no longer a kit')
        elif abs(float(live['price']) - float(price)) > 0.005:
            drift.append(f'{name}: this file says ${price:.2f}, live is ${float(live["price"]):.2f}')
    if drift:
        print('REFUSING TO RUN: the kit economics in this file are stale.\n')
        for d in drift:
            print('  ! ' + d)
        print('\nPrice alone is not enough to repair it: the goods and freight '
              'figures\nare from the 2026-08-04 rebuild, and the compositions '
              'have changed since\n(the Travel Kit gained the 3-in-1 Travel Bowl, '
              'Calm & Comfort swapped the\nThunder Wrap for the Anxiety Vest).')
        print('\nRe-derive all three columns with:  python config/kit_reprice.py')
        print('then update KITS above, then re-run.')
        return False
    return True


def main():
    if not _assert_prices_current():
        return 1
    rows = []
    for name, (p, g, f) in KITS.items():
        c = contribution(p, g, f)
        rows.append((name, p, c, c * TARGET_PAYBACK))

    print('=== KITS: the paid-acquisition products ===')
    print(f"{'offer':26}{'price':>8}{'contrib':>9}{'max CAC':>9}   "
          + '  '.join(f'{k[:13]:>13}' for k in CPC))
    print(f"{'':26}{'':8}{'':9}{'':9}   "
          + '  '.join(f'{"CVR needed":>13}' for _ in CPC))
    for name, p, c, cac in sorted(rows, key=lambda r: -r[2]):
        cells = '  '.join(f'{cpc / c * 100:12.1f}%' for cpc in CPC.values())
        print(f'  {name:24}{p:>8.2f}{c:>9.2f}{cac:>9.2f}   {cells}')

    sing = singles()
    avg = sum(c for _, c in sing.values()) / len(sing)
    top = sorted(sing.items(), key=lambda kv: -kv[1][1])[:8]
    print(f'\n=== SINGLES: basket fillers, NOT ad targets ===')
    print(f'  {len(sing)} products, average contribution ${avg:.2f}')
    print(f"  {'best single':32}{'price':>8}{'contrib':>9}{'CVR needed @ $0.90':>20}")
    for t, (p, c) in top:
        print(f'    {t:30}{p:>8.2f}{c:>9.2f}{0.90 / c * 100:>19.1f}%')
    print(f'\n  A $0.90 Meta click against the AVERAGE single needs '
          f'{0.90 / avg * 100:.0f}% conversion. Nothing converts at that.')

    best = max(rows, key=lambda r: r[2])
    print(f'\n=== THE RULE ===')
    print(f'  Highest-contribution offer: {best[0]} at ${best[2]:.2f}.')
    print(f'  Never bid above ${best[3]:.2f} CAC on a first order '
          f'({TARGET_PAYBACK:.0%} of contribution).')
    print(f'  A channel is viable only if  CPC / expected CVR  <  that number.')
    print(f'  At a realistic new-store 1.0% CVR that means a ceiling of '
          f'${best[2] * 0.01:.2f} per click.')

    if '--json' in sys.argv:
        out = {'target_payback': TARGET_PAYBACK,
               'kits': {n: {'price': p, 'contribution': round(c, 2),
                            'max_cac': round(cac, 2)} for n, p, c, cac in rows},
               'singles_avg_contribution': round(avg, 2),
               'singles': {t: {'price': p, 'contribution': round(c, 2)}
                           for t, (p, c) in sing.items()}}
        json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'),
                  indent=1)
        print(f'\njson -> {sys.argv[sys.argv.index("--json") + 1]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
