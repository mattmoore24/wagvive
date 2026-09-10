#!/usr/bin/env python3
"""Swap the component still-life inside a KIT's gallery when composition changes.

A kit gallery is built as: position 1 the flatlay of everything, then one still
of each component in order, then the per-colorway covers wired to the variants.
When a component is swapped out, the kit page keeps showing a photo of a product
that is no longer in the box. After the 2026-08-17 change the Toy Kit page still
showed the Watermelon Rope Frisbee and the Dog Enrichment Kit still showed the
Bouncy Egg Squeaker, both of which CJ cannot ship.

Not the same job as replace_product_image.py. That one retouches a photo of the
SAME product, so it deliberately preserves alt text. Here the subject itself
changes, so carrying the old alt over would caption a plush "Watermelon Rope
Frisbee": wrong for screen readers, and wrong for the audits that key off alt.

The source image is the component's OWN live product photo rather than anything
generated, so the kit page shows the item the customer actually receives.

Order of operations: upload first, verify, then delete. A failure leaves the kit
with one extra photo, which is recoverable; deleting first could leave a gap.

    python config/swap_kit_component_shot.py            # show the plan
    python config/swap_kit_component_shot.py --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# kit handle -> (alt of the stale shot, source product handle, source image alt)
# The source image is picked to match the kit's FIRST colorway, which is the
# convention the rest of each gallery already follows.
#
# `stale_alt: None` means the component was ADDED with nothing removed, so
# there is no stale shot to replace and the still is appended to the end of the
# component block instead. Without this the Travel Kit could not be fixed at
# all: it gained the 3-in-1 Travel Bowl on 2026-09-08 and its gallery has been
# advertising five pieces while the box holds six.
SWAPS = {
    'toy-kit': {
        'stale_alt': 'Wagvive Watermelon Rope Frisbee',
        'source_handle': 'wagvive-woodland-rope-limb-plush',
        'source_alt': 'Wagvive Woodland Rope-Limb Plush, Rabbit',
        'new_alt': 'Wagvive Woodland Rope-Limb Plush',
    },
    'dog-enrichment-kit': {
        'stale_alt': 'Wagvive Bouncy Egg Squeaker',
        'source_handle': 'wagvive-dental-chew-stick',
        'source_alt': 'Wagvive Dental Chew Stick - Green',
        'new_alt': 'Wagvive Dental Chew Stick',
    },
    # 2026-09-09: the Calming Thunder Wrap is delisted at CJ and archived. The
    # kit page was still showing a photo of it, and the wrap was a folded
    # blanket while the replacement is a worn vest, so this is a real change of
    # subject and the alt must change with it.
    'calm-comfort-kit': {
        'stale_alt': 'Wagvive Calming Thunder Wrap',
        'source_handle': 'wagvive-calming-hooded-anxiety-vest',
        'source_alt': 'Wagvive Calming Hooded Anxiety Vest, Dark Grey',
        'new_alt': 'Wagvive Calming Hooded Anxiety Vest',
    },
    'travel-kit': {
        'stale_alt': None,                      # added, nothing removed
        'source_handle': 'wagvive-3-in-1-travel-bowl',
        'source_alt': 'Wagvive 3-in-1 Travel Bowl, Blue',
        'new_alt': 'Wagvive 3-in-1 Travel Bowl',
    },
}


def rest(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/{path}', data=data,
        method=method, headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode()
            out = json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path}: {e.code} {e.read().decode()[:400]}')
    time.sleep(0.55)
    return out


def products():
    return rest('products.json?limit=250&status=active')['products']


def main():
    apply = '--apply' in sys.argv
    cat = {p['handle']: p for p in products()}
    problems = []

    for kit_handle, spec in SWAPS.items():
        kit = cat.get(kit_handle)
        src = cat.get(spec['source_handle'])
        print('=' * 72)
        print(kit['title'] if kit else f'MISSING KIT {kit_handle}')
        print('=' * 72)
        if not kit or not src:
            problems.append(kit_handle)
            print('  !! kit or source product not found')
            continue

        stale = next((i for i in kit['images']
                      if spec['stale_alt']
                      and (i.get('alt') or '') == spec['stale_alt']), None)
        already = next((i for i in kit['images']
                        if (i.get('alt') or '') == spec['new_alt']), None)
        if already:
            print(f"  nothing to do: {spec['new_alt']!r} already present")
            continue
        if not stale and spec['stale_alt']:
            print(f"  nothing to do: no image alt {spec['stale_alt']!r}")
            continue

        source = next((i for i in src['images']
                       if (i.get('alt') or '') == spec['source_alt']), None)
        if not source:
            problems.append(kit_handle)
            print(f"  !! source image alt {spec['source_alt']!r} not found on "
                  f"{spec['source_handle']}")
            continue

        if stale:
            pos = stale['position']
            print(f"  position {pos}")
            print(f"    - {stale['src'].split('/')[-1].split('?')[0]}  "
                  f"alt={spec['stale_alt']!r}")
        else:
            # Append to the END of the component block, which is everything
            # after position 1 that is not a "<kit title> - <colorway>" cover.
            # Appending blindly at the end would put a component still AFTER
            # the colorway covers and break the gallery's reading order.
            prefix = f"{kit['title']} - "
            comp_pos = [i['position'] for i in kit['images']
                        if i['position'] > 1
                        and not (i.get('alt') or '').startswith(prefix)]
            pos = (max(comp_pos) if comp_pos else 1) + 1
            print(f"  appending at position {pos} (nothing to replace)")
        print(f"    + {source['src'].split('/')[-1].split('?')[0]}  "
              f"alt={spec['new_alt']!r}   (from {src['title']})")
        if stale and stale.get('variant_ids'):
            print(f"    !! stale image is wired to {len(stale['variant_ids'])} "
                  f"variant(s); they would be orphaned")
            problems.append(kit_handle)
            continue
        if not apply:
            continue

        # 1. upload the new shot at the stale one's position
        created = rest(f"products/{kit['id']}/images.json", 'POST', {
            'image': {'src': source['src'], 'alt': spec['new_alt'],
                      'position': pos}})['image']
        print(f"    uploaded image {created['id']}")

        # 2. prove it landed before removing anything
        fresh = rest(f"products/{kit['id']}/images/{created['id']}.json")['image']
        if (fresh.get('alt') or '') != spec['new_alt']:
            problems.append(kit_handle)
            print('    !! upload did not take the alt; leaving the old image')
            continue

        # 3. now the old one can go, if there was one
        if stale:
            rest(f"products/{kit['id']}/images/{stale['id']}.json", 'DELETE')
            print(f"    deleted image {stale['id']}")

    # verify against the live product, not the writes above
    print('\n' + '=' * 72)
    cat = {p['handle']: p for p in products()}
    for kit_handle, spec in SWAPS.items():
        kit = cat.get(kit_handle)
        if not kit:
            continue
        alts = [(i['position'], i.get('alt') or '') for i in kit['images']]
        has_stale = any(a == spec['stale_alt'] for _, a in alts)
        has_new = any(a == spec['new_alt'] for _, a in alts)
        state = ('STILL STALE' if has_stale else
                 'ok' if has_new else 'MISSING NEW SHOT')
        if has_stale or not has_new:
            problems.append(kit_handle)
        print(f"{kit['title']:24} {state}")
        for p_, a in sorted(alts):
            print(f"    pos{p_}  {a}")

    if problems:
        print(f'\n{len(set(problems))} kit(s) not right: {sorted(set(problems))}')
        return 1
    if not apply:
        print('\nPlan only. Use --apply to swap.')
        return 0
    print('\nBoth kit galleries show only components that are in the box.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
