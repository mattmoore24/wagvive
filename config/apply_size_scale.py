#!/usr/bin/env python3
"""Migrate the whole catalogue onto the canonical XS-XL scale in config/size_scale.py.

ORDER MATTERS AND IS NOT NEGOTIABLE:

  1. DELETE the retired variants FIRST, while they still carry their supplier
     size names. Renaming first would make the retire list unmatchable.
  2. RENAME the survivors' size option values second. A rename is a per-variant
     PUT of option1/option2; Shopify recomputes product.options[].values from
     the variants, so there is no separate options call and no window where the
     two disagree.

WHAT IS DELIBERATELY *NOT* TOUCHED:

  * SKUs. CJ pairing is keyed on the variant SKU, so a rename cannot break it
    and a survivor keeps its pairing untouched. Only the DELETED variants lose
    their pairing, which is the intent.
  * variant.image_id. Renaming does not disturb it, and the deleted variants'
    images stay on the product for the survivors that share them. The verify
    pass re-checks every survivor still has its art, because a variant silently
    losing image_id is invisible on the storefront (it falls back to the lead
    image) and has bitten this repo before.
  * Kit bundle composition. Bundles reference component VARIANT IDS, not option
    strings, so renaming a component's size leaves every bundle intact.
    `size_scale` was checked to confirm no kit-consumed component variant is in
    any retire list; this script re-asserts that at runtime and refuses to run
    if that ever stops being true.

    python config/apply_size_scale.py            # show the plan
    python config/apply_size_scale.py --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
from size_scale import MAP, FURNITURE, KIT_RENAME          # noqa: E402
from kit_colorways import SIZE_MAP                          # noqa: E402

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])
SHOP = env.get('SHOPIFY_PUBLIC_DOMAIN', 'wagvive.com')

KIT_HANDLES = ['calm-comfort-kit', 'grooming-essentials-kit', 'new-puppy-kit',
               'travel-kit']
COMPONENT_HANDLE = {'Paw Print Fleece Blanket': 'wagvive-paw-print-fleece-blanket',
                    'Quick-Dry Bath Robe': 'wagvive-quick-dry-bath-robe',
                    'Paw Washing Cup': 'wagvive-paw-washing-cup',
                    'Cooling Comfort Pad': 'wagvive-cooling-comfort-pad'}


def api(path, method='GET', payload=None, tries=6):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data, method=method,
        headers={'X-Shopify-Access-Token': TOKEN,
                 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
            time.sleep(0.55)
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f'{method} {path}: {e.code} {body}')
        except Exception:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def get(handle):
    ps = api(f'products.json?handle={handle}&status=active')['products']
    return ps[0] if ps else None


def size_index(product):
    for i, o in enumerate(product['options']):
        if o['name'].lower() == 'size':
            return i
    return None


def guard_kits():
    """Refuse to run if any kit-consumed component size is on a retire list."""
    bad = []
    for _, comps in SIZE_MAP.items():
        for comp, val in comps.items():
            h = COMPONENT_HANDLE[comp]
            if val in MAP.get(h, {}).get('retire', []):
                bad.append(f'{comp} {val}')
    return bad


def rename(title, variants, key, mapping):
    """Rename option values in TWO PASSES, via a temporary name.

    A one-pass rename deadlocks on any mapping that SHIFTS along the scale.
    The Quick-Dry Bath Robe is XS->S, S->M, M->L: renaming XS to S while a real
    S still exists returns
    422 "The variant 'Blue / S' already exists", and the run dies half done -
    which is exactly what happened on the first attempt here.

    Two passes with a temp prefix make the operation order-independent: nothing
    can collide with `__TMP_x` because no real size is ever named that. The
    passes are separated per product, so a product is never left holding temp
    names if a later product fails.
    """
    todo = [(v, v.get(key), mapping[v.get(key)]) for v in variants
            if mapping.get(v.get(key)) and mapping[v.get(key)] != v.get(key)]
    if not todo:
        print(f'  {title[:40]:42} already correct')
        return 0
    for v, _old, new in todo:
        api(f"variants/{v['id']}.json", 'PUT',
            {'variant': {'id': v['id'], key: f'__TMP_{new}'}})
    for v, _old, new in todo:
        api(f"variants/{v['id']}.json", 'PUT',
            {'variant': {'id': v['id'], key: new}})
    print(f'  {title[:40]:42} renamed {len(todo)}')
    return len(todo)


def plan_product(handle, mapping):
    p = get(handle)
    if not p:
        return None
    i = size_index(p)
    key = f'option{i + 1}'
    keep, retire, orphan = [], [], []
    for v in p['variants']:
        val = v.get(key)
        if val in mapping['retire']:
            retire.append(v)
        elif val in mapping['keep']:
            keep.append(v)
        else:
            orphan.append(v)
    return dict(product=p, key=key, keep=keep, retire=retire, orphan=orphan)


def main():
    apply = '--apply' in sys.argv

    bad = guard_kits()
    if bad:
        print('REFUSING: these kit components are on a retire list:', bad)
        return 1

    plans = {}
    print(f"{'product':44}{'keep':>6}{'retire':>8}{'orphan':>8}")
    total_ret = 0
    for handle, mapping in MAP.items():
        pl = plan_product(handle, mapping)
        if not pl:
            print(f'  ! {handle} not found')
            return 1
        plans[handle] = pl
        total_ret += len(pl['retire'])
        flag = '  <-- ORPHANS, STOPPING' if pl['orphan'] else ''
        print(f"{pl['product']['title'][:42]:44}{len(pl['keep']):>6}"
              f"{len(pl['retire']):>8}{len(pl['orphan']):>8}{flag}")
        if pl['orphan']:
            vals = sorted({v.get(pl['key']) for v in pl['orphan']})
            print(f'    unmapped size values: {vals}')
            return 1

    print(f'\n{total_ret} variant(s) to retire, then rename survivors.')
    print(f'{len(FURNITURE)} product(s) to move OFF the dog scale onto '
          f'furniture names.')
    print(f'{len(KIT_HANDLES)} kit(s) to rename {list(KIT_RENAME)} -> '
          f'{list(KIT_RENAME.values())}.')
    if not apply:
        print('\nDry run. Use --apply.')
        return 0

    # ---- 1. delete retired variants
    print('\n--- retiring variants ---')
    for handle, pl in plans.items():
        for v in pl['retire']:
            api(f"variants/{v['id']}.json", 'DELETE')
        if pl['retire']:
            print(f"  {pl['product']['title'][:40]:42} removed {len(pl['retire'])}")

    # ---- 2. rename survivors onto the canonical scale
    print('\n--- renaming size values ---')
    for handle, pl in plans.items():
        rename(pl['product']['title'], pl['keep'], pl['key'], MAP[handle]['keep'])

    # ---- 3. furniture-sized product off the dog scale
    print('\n--- furniture sizing ---')
    for handle, mapping in FURNITURE.items():
        p = get(handle)
        i = size_index(p)
        key = f'option{i + 1}'
        rename(p['title'], p['variants'], key, mapping)

    # ---- 4. kits onto S/M/L
    print('\n--- kit sizes ---')
    for handle in KIT_HANDLES:
        p = get(handle)
        i = size_index(p)
        if i is None:
            continue
        key = f'option{i + 1}'
        rename(p['title'], p['variants'], key, KIT_RENAME)

    print('\nWrites done. Run --verify (or apply_size_scale.py --verify) next.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
