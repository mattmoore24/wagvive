#!/usr/bin/env python3
"""Give the footer actual links. It had none.

The live footer contained an email signup and nothing else: no shop links, no
contact, no policies, and no "Your Privacy Choices". The Footer navigation menu
existed in admin with twelve items and was simply never wired to a block, so
every one of those links rendered nowhere.

That is three problems at once:
  * Trust. A store with no visible policy links reads as temporary, and policy
    links are one of the few trust signals that reliably move conversion.
  * Compliance. The state-privacy opt-out link has to be conspicuous, and
    "somewhere in checkout" is not conspicuous. Same for the new accessibility
    and Proposition 65 notices, which are worthless if unreachable.
  * Navigation. Shipping & Returns, Contact and the FAQ were reachable only
    from the header or by guessing URLs.

Structure written here: three menu columns (Shop, Help, Company) plus a legal
row of policy links, all inside the existing footer section, above the email
signup. Menus are referenced by handle so they stay editable in admin.

    python config/build_footer.py            # show the plan
    python config/build_footer.py --apply    # write + verify live
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = 187585560865
GROUP = 'sections/footer-group.json'
SECTION = 'footer_m9NzUG'
FG = '{{ settings.color_palette.foreground }}'

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = (env['SHOPIFY_STORE_DOMAIN'],
                          env['SHOPIFY_ADMIN_API_TOKEN'],
                          env['SHOPIFY_API_VERSION'])

# handle -> (title, [(label, url)])
MENUS = {
    'footer-shop': ('Shop', [
        ('All products', '/collections/all'),
        ('Bundles & Kits', '/collections/bundles-kits'),
        ('Toys & Play', '/collections/toys-play'),
        ('Grooming', '/collections/grooming'),
        ('Comfort & Health', '/collections/comfort-health'),
        ('Calming & Enrichment', '/collections/calming-enrichment'),
        ('Travel & Outdoor', '/collections/travel-outdoor'),
    ]),
    'footer-help': ('Help', [
        ('Shipping & Returns', '/pages/shipping-returns'),
        ('FAQ', '/pages/faq'),
        ('Contact us', '/pages/contact'),
        ('Accessibility', '/pages/accessibility'),
    ]),
    'footer-company': ('Company', [
        ('About Wagvive', '/pages/about'),
        ('Creator & Affiliate Program', '/pages/creator-affiliate-program'),
        ('Your Privacy Choices', '/pages/data-sharing-opt-out'),
        ('California Proposition 65', '/pages/proposition-65'),
    ]),
}
# Deliberately NO "Legal" column: the theme already appends Privacy, Terms,
# Refund, Shipping and Contact Information automatically at the foot of the
# page, and a second copy renders every policy link twice. The links that are
# NOT auto-appended, and therefore have to be placed by hand, are Your Privacy
# Choices, Proposition 65 and Accessibility, which live in Help and Company.


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:400])
    return out


MENU_CREATE = '''mutation($title:String!,$handle:String!,$items:[MenuItemCreateInput!]!){
  menuCreate(title:$title, handle:$handle, items:$items){
    menu{ id handle } userErrors{ field message } } }'''
MENU_UPDATE = '''mutation($id:ID!,$title:String!,$handle:String!,$items:[MenuItemUpdateInput!]!){
  menuUpdate(id:$id, title:$title, handle:$handle, items:$items){
    menu{ id handle } userErrors{ field message } } }'''


def get_asset(key):
    q = urllib.parse.urlencode({'asset[key]': key})
    return api('GET', f'themes/{THEME}/assets.json?{q}')['asset']['value']


def put_asset(key, value):
    return api('PUT', f'themes/{THEME}/assets.json',
               {'asset': {'key': key, 'value': value}})


def text_block(html, preset='rte', size=None):
    b = {'type': 'text', 'settings': {
        'text': html, 'width': '100%', 'max_width': 'normal',
        'alignment': 'left', 'type_preset': preset,
        'font': 'var(--font-body--family)', 'line_height': 'normal',
        'letter_spacing': 'normal', 'case': 'none', 'wrap': 'pretty',
        'text_color': FG, 'background': False, 'background_color': '#00000026',
        'corner_radius': 0, 'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}
    if size:
        b['settings']['font_size'] = size
    return b


def menu_block(handle, heading):
    return {'type': 'menu', 'settings': {
        'menu': handle, 'heading': heading, 'menu_spacing': 8,
        'show_as_accordion': False, 'accordion_icon': 'caret',
        'accordion_dividers': False, 'text_color': FG,
        'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}


def group(blocks, order, direction='row', gap=48, width='fill'):
    return {'type': 'group', 'settings': {
        'content_direction': direction, 'vertical_on_mobile': True,
        'horizontal_alignment': 'flex-start', 'vertical_alignment': 'flex-start',
        'align_baseline': False,
        'horizontal_alignment_flex_direction_column': 'flex-start',
        'vertical_alignment_flex_direction_column': 'flex-start',
        'gap': gap, 'width': width, 'custom_width': 100,
        'width_mobile': 'fill', 'custom_width_mobile': 100,
        'height': 'fit', 'custom_height': 100, 'background_media': 'none',
        'video_position': 'cover', 'background_image_position': 'cover',
        'border': 'none', 'border_width': 1, 'border_opacity': 100,
        'border_radius': 0, 'toggle_overlay': False,
        'overlay_color': '#00000026', 'overlay_style': 'solid',
        'gradient_direction': 'to top', 'open_in_new_tab': False,
        'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 0, 'padding-inline-end': 0},
        'blocks': blocks, 'block_order': order}


LEGAL_LINE = (
    '<p>&copy; Wagvive. Wagvive, 333 Pearl St, New York, NY 10038, United '
    'States. Questions: <a href="mailto:hello@wagvive.com">hello@wagvive.com</a>'
    '</p>')


def ensure_menus(apply):
    live = {m['handle']: m for m in
            gql('{menus(first:30){nodes{id handle title}}}')['data']['menus']['nodes']}
    for handle, (title, items) in MENUS.items():
        payload = [{'title': t, 'type': 'HTTP', 'url': u} for t, u in items]
        state = 'update' if handle in live else 'create'
        print(f'  {state:6} menu /{handle:18} {len(items)} items')
        if not apply:
            continue
        if handle in live:
            r = gql(MENU_UPDATE, {'id': live[handle]['id'], 'title': title,
                                  'handle': handle, 'items': payload})
            errs = r['data']['menuUpdate']['userErrors']
        else:
            r = gql(MENU_CREATE, {'title': title, 'handle': handle,
                                  'items': payload})
            errs = r['data']['menuCreate']['userErrors']
        if errs:
            print(f'    ERRORS: {json.dumps(errs)[:200]}')
            return False
        time.sleep(0.4)
    return True


def main():
    apply = '--apply' in sys.argv
    print('--- menus ---')
    if not ensure_menus(apply):
        return 1

    doc = json.loads(get_asset(GROUP))
    sec = doc['sections'][SECTION]
    existing_order = list(sec.get('block_order') or [])
    print(f'\n--- footer section ---\n  existing blocks: {existing_order}')

    cols = {f'menu_{h.replace("-", "_")}': menu_block(h, MENUS[h][0])
            for h in MENUS}
    links_row = group(cols, list(cols), direction='row', gap=40)
    legal_row = group({'legal_text': text_block(LEGAL_LINE, 'rte', '0.85rem')},
                      ['legal_text'], direction='column', gap=4)

    sec['blocks']['wv_links'] = links_row
    sec['blocks']['wv_legal'] = legal_row
    # links first, then the existing signup group, then the legal line
    keep = [b for b in existing_order if b not in ('wv_links', 'wv_legal')]
    sec['block_order'] = ['wv_links'] + keep + ['wv_legal']
    print(f'  new order:       {sec["block_order"]}')
    for h, (title, items) in MENUS.items():
        print(f'    {title:8} ' + ', '.join(t for t, _ in items))

    body = json.dumps(doc, ensure_ascii=False, indent=1)
    for bad in ('—', '–'):
        if bad in body:
            print(f'REFUSING: footer JSON contains {bad!r}')
            return 1

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    put_asset(GROUP, body)
    fresh = json.loads(get_asset(GROUP))['sections'][SECTION]
    if 'wv_links' not in (fresh.get('block_order') or []):
        print('ADMIN VERIFY FAILED: block not present after write')
        return 1
    print('\nadmin asset verified')

    # Verify through the SECTION RENDERING API, not the homepage HTML. The
    # full-page cache served pre-change renders for over seven minutes after a
    # write here, alternating between two old versions across edge nodes, so it
    # cannot distinguish "not deployed" from "not flushed yet".
    # /?sections=<id> re-renders server side and shows the truth immediately.
    want = ['/pages/shipping-returns', '/pages/contact', '/pages/accessibility',
            '/pages/proposition-65', '/pages/data-sharing-opt-out',
            '/collections/bundles-kits', '/pages/about']
    section_id = f'sections--27042989867297__{SECTION}'
    for attempt in range(6):
        try:
            req = urllib.request.Request(
                f'https://wagvive.com/?sections={section_id}'
                f'&cb={int(time.time())}{attempt}',
                headers={'User-Agent': 'Mozilla/5.0'})
            html = json.loads(urllib.request.urlopen(
                req, timeout=90).read().decode('utf-8', 'replace')
                ).get(section_id, '')
        except Exception as exc:
            print(f'  fetch failed: {str(exc)[:60]}')
            time.sleep(10)
            continue
        missing = [u for u in want if u not in html]
        # The theme appends its own policy row outside this section, so a
        # hand-placed Legal column would duplicate every policy link.
        dupes = [u for u in ('/policies/privacy-policy',
                             '/policies/terms-of-service')
                 if html.count(u) > 0]
        if not missing and not dupes:
            print(f'storefront section verified: all {len(want)} links render, '
                  f'no duplicated policy links')
            print('  (the cached homepage HTML can lag this by many minutes)')
            return 0
        print(f'  attempt {attempt + 1}: missing={missing} duplicated={dupes}')
        time.sleep(12)
    print('section render still wrong; check the admin asset')
    return 1


if __name__ == '__main__':
    sys.exit(main())
