#!/usr/bin/env python3
"""The CJ product (SPU) a variant SKU belongs to. No imports, no side effects.

For its first 54 products every CJ variant SKU in this store was an 11
character SPU plus a short suffix (CJGD189483115OL is SPU CJGD1894831), so the
whole repo wrote `sku[:11]`. CJ also issues LONGER SPUs whose variants carry a
hyphen: the Padded Hot Dog Costume (2026-09-14) is SPU CJJJCWGD00035 with
variants CJJJCWGD00035-8, CJJJCWGD00035-Size18 and so on. `sku[:11]` turns
those into "CJJJCWGD000", which is no product at all, so the margin guard,
the shipping guard, the carrier lookup and the CJ audit would each have
silently skipped or mis-read that product.

Kept in its own module because freight_floor deliberately loads cj_api lazily
(cj_api reads the credentials file at import), and this must be usable
everywhere, including there.
"""


def spu(sku):
    """'CJJJCWGD00035-Size6' -> 'CJJJCWGD00035'; 'CJGD189483115OL' -> 'CJGD1894831'."""
    sku = str(sku or '')
    if '-' in sku:
        return sku.split('-', 1)[0]
    return sku[:11]


if __name__ == '__main__':
    for s, want in [('CJJJCWGD00035-Size6', 'CJJJCWGD00035'),
                    ('CJJJCWGD00035-8', 'CJJJCWGD00035'),
                    ('CJGD189483115OL', 'CJGD1894831'),
                    ('CJYD233200804DW', 'CJYD2332008'), ('', '')]:
        assert spu(s) == want, (s, spu(s), want)
    print('ok')
