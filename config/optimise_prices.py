#!/usr/bin/env python3
"""Price every product to maximise expected contribution, not margin.

A margin target is the wrong objective: 60% of nothing is nothing. This picks
the price that maximises

    (price - variable cost) x share_of_consideration(price)

where the share curve is calibrated on the observed market band for that
product (see demand_model.py) rather than on an assumed elasticity. Variable
cost is goods + duty + freight + returns allowance + payment fee, from
config/pricing.py, using the DEAREST variant a customer can pick so no choice
loses money.

Output marks a product KIT-ONLY when even its best standalone price returns
under 12%. Those are not dropped: freight is a per-parcel charge, so inside a
kit the item costs only its marginal weight, which is usually a tenth of what
shipping it alone costs. See optimise_kits.py.

    python config/optimise_prices.py IN.json [--json OUT.json]
"""
import json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import pricing, demand_model
from market_bands import band

KIT_ONLY_MARGIN = 12.0


def charm(x):
    if x <= 0.99:
        return 0.99
    b = int(x)
    return b - 1 + 0.99 if x < b + 0.99 else b + 0.99


def unit_cost(goods, freight):
    """Everything that does not scale with price."""
    return pricing.landed(goods, freight) + pricing.FLAT


def main():
    rows = json.load(open(sys.argv[1], encoding='utf-8'))
    out = []
    for r in rows:
        b = band(r['title'])
        if not b:
            print(f"  ! no market band: {r['title']}", file=sys.stderr)
            continue
        c = unit_cost(r['cost'], r['freight'])
        # Competitive-from-day-one cap: an unbranded, zero-review store wins on
        # being AT or UNDER the volume price. Outcome goods (anxiety, cooling,
        # dental) tolerate a small premium for presentation; nothing else does.
        ceiling = b['mid'] * (1.15 if b['e'] <= 1.8 else 1.0)
        raw, _ = demand_model.best_price(c, b['low'], b['mid'], b['high'], b['e'],
                                         hi=ceiling)
        rec = charm(raw)
        m = pricing.margin(rec, r['cost'], r['freight']) * 100
        sh = demand_model.share(rec, b['mid'], b['high'], b['e'])
        con = demand_model.contribution(rec, c)
        # same maths at today's price, for a like-for-like comparison
        sh_now = demand_model.share(r['cur'], b['mid'], b['high'], b['e'])
        con_now = demand_model.contribution(r['cur'], c)
        out.append(dict(r, **b, unit_cost=c, rec2=rec, m2=m, share=sh,
                        contrib=con, exp=con * sh,
                        exp_now=con_now * sh_now, share_now=sh_now,
                        kit_only=m < KIT_ONLY_MARGIN))

    out.sort(key=lambda r: -r['exp'])
    print(f"{'product':29}{'cost':>6}{'frt':>6}{'low':>7}{'mid':>7}{'high':>7}"
          f"{'now':>7}{'NEW':>7}{'mgn':>6}{'win%':>6}{'ExpC':>7}{'vs now':>8}")
    for r in out:
        flag = '  KIT' if r['kit_only'] else ''
        d = r['exp'] - r['exp_now']
        print(f"  {r['title'].replace('Wagvive ','')[:27]:29}{r['cost']:>6.2f}"
              f"{r['freight']:>6.2f}{r['low']:>7.2f}{r['mid']:>7.2f}{r['high']:>7.2f}"
              f"{r['cur']:>7.2f}{r['rec2']:>7.2f}{r['m2']:>5.0f}%"
              f"{r['share']*100:>5.0f}%{r['exp']:>7.2f}{d:>+8.2f}{flag}")

    cur = sum(r['cur'] for r in out)
    new = sum(r['rec2'] for r in out)
    e_new = sum(r['exp'] for r in out)
    e_now = sum(r['exp_now'] for r in out)
    print(f"\nprice sum        ${cur:,.2f} -> ${new:,.2f}  ({(new/cur-1)*100:+.0f}%)")
    ms = sorted(r['m2'] for r in out)
    print(f"margin           median {ms[len(ms)//2]:.0f}%  min {ms[0]:.0f}%  max {ms[-1]:.0f}%")
    print(f"expected contribution  {e_now:.1f} -> {e_new:.1f}  "
          f"({(e_new/e_now-1)*100:+.0f}% per shopper reaching the page)")
    sn = sum(r['share_now'] for r in out) / len(out)
    sv = sum(r['share'] for r in out) / len(out)
    print(f"avg win rate     {sn*100:.0f}% -> {sv*100:.0f}%")
    k = [r for r in out if r['kit_only']]
    if k:
        print(f"\nkit-only ({len(k)}), cannot pay their own freight alone:")
        for r in k:
            print(f"   {r['title'].replace('Wagvive ',''):32} best {r['rec2']:>6.2f} "
                  f"= {r['m2']:>4.0f}%   freight ${r['freight']:.2f} on {r['weight']:.0f}g")
    if '--json' in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
