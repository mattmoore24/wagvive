#!/usr/bin/env python3
"""The 2026-08 homepage refresh: motion up top, photography everywhere.

Modeled on the Skims/Gymshark audit (config/design-audit-2026-08.md). The page
becomes: video hero -> marquee -> 8-product favorites row -> full-bleed puppy
band -> 4-kit row -> 4 photo category tiles -> story band on photography ->
faq -> newsletter.

Also fixes two long-standing wrongs while it is in here: the template JSON
still carried em dashes (dedash.py never covered templates), and the story
band still claimed "one supplier", which stopped being true on 2026-07-29.

Data side first (collection images, featured collection contents), then the
template, then typography. Backups of both JSON files are in
config/theme-backup/*.bak-2026-08-01.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

MEDIA = json.load(open(os.path.join(ROOT, 'config', 'media_ids.json'), encoding='utf-8'))

COLLECTIONS = {          # id, kind, tile image
    'toys':     (517062132001, 'smart_collections',  'tile-toys-14084426.jpg'),
    'grooming': (516731339041, 'custom_collections', 'tile-grooming-8498861.jpg'),
    'comfort':  (516731371809, 'custom_collections', 'tile-comfort-33119363.jpg'),
    'bundles':  (516867031329, 'custom_collections', 'tile-kits-7055930.jpg'),
}
HOME_COLLECTION = 516730487073

# The favorites row: two from each category, cheap and dear mixed, in the
# order they should appear (collection sort becomes manual).
FEATURED_HANDLE_ORDER = [
    'cooling-comfort-pad',        # comfort hero
    'anti-spill-water-bowl',      # comfort, strongest visual
    'self-cleaning-slicker-brush',  # grooming
    'quiet-electric-nail-grinder',  # grooming, premium
    'sofa-furniture-cover',       # comfort, high AOV
    'slow-feeder-bowl',           # comfort, low entry
    'dental-duck-chew-toy',       # toy, impulse
    'finger-toothbrush',          # $14 entry point
]


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def collections():
    print('== collection tile images ==')
    for name, (cid, kind, img) in COLLECTIONS.items():
        api('PUT', f'{kind[:-1]}s/{cid}.json', {kind[:-1]: {
            'id': cid, 'image': {'src': MEDIA[img]['url'],
                                 'alt': f'Wagvive {name} collection'}}})
        print(f'   {name:10} <- {img}')


def featured():
    print('== featured collection ==')
    live = {p['handle']: p['id']
            for p in api('GET', 'products.json?limit=250&status=active')['products']}
    picks = []
    for want in FEATURED_HANDLE_ORDER:
        hit = next((pid for h, pid in live.items()
                if all(w in h for w in want.split('-'))), None)
        if hit:
            picks.append(hit)
        else:
            print(f'   !! no live product matches "{want}"')
    have = {c['product_id']: c['id'] for c in
            api('GET', f'collects.json?collection_id={HOME_COLLECTION}&limit=250')['collects']}
    for pid in picks:
        if pid not in have:
            api('POST', 'collects.json', {'collect': {
                'product_id': pid, 'collection_id': HOME_COLLECTION}})
    have = {c['product_id']: c['id'] for c in
            api('GET', f'collects.json?collection_id={HOME_COLLECTION}&limit=250')['collects']}
    for pid, coll_id in list(have.items()):
        if pid not in picks:
            api('DELETE', f'collects/{coll_id}.json')
            print(f'   removed stray product {pid}')
    # collects have no update route; ordering goes through the collection,
    # and the array must reference the EXISTING collect ids
    have = {c['product_id']: c['id'] for c in
            api('GET', f'collects.json?collection_id={HOME_COLLECTION}&limit=250')['collects']}
    api('PUT', f'custom_collections/{HOME_COLLECTION}.json', {'custom_collection': {
        'id': HOME_COLLECTION, 'sort_order': 'manual',
        'collects': [{'id': have[pid], 'position': pos}
                     for pos, pid in enumerate(picks, 1) if pid in have]}})
    print(f'   {len(picks)} products, manual order set')


def template(theme_id):
    print('== homepage template ==')
    key = 'templates/index.json'
    q = urllib.parse.quote(key)
    idx = json.loads(api('GET', f'themes/{theme_id}/assets.json?asset[key]={q}')
                     ['asset']['value'])
    S = idx['sections']

    # hero: video, both breakpoints
    h = S['hero']['settings']
    h['media_type_1'] = 'video'
    h['video_1'] = 'shopify://files/videos/hero-desktop-9898282.mp4'
    h['custom_mobile_media'] = True
    h['media_type_1_mobile'] = 'video'
    h['video_1_mobile'] = 'shopify://files/videos/hero-mobile-19824572.mp4'
    h['overlay_color'] = '#22301F52'
    S['hero']['blocks']['sub']['settings']['text'] = (
        '<p>Grooming, comfort and play essentials for every stage of dog life.</p>')

    # marquee: merchandise the range, not just trust
    S['marquee']['blocks']['m3']['settings']['text'] = '<p>Four kits for four life stages</p>'
    S['marquee']['blocks']['m4']['settings']['text'] = '<p>Any 3 toys, 15% off</p>'

    # favorites row: eight products
    for b in S['featured_head']['blocks'].values():
        t = b['settings'].get('text', '')
        if t.startswith('<h2>'):
            b['settings']['text'] = '<h2>The favorites</h2>'
        elif t.startswith('<p>'):
            b['settings']['text'] = '<p>Eight essentials people reach for first.</p>'
    S['featured_products']['settings']['max_products'] = 8

    # full-bleed puppy band before the kit row
    S['kit_band'] = {
        'type': 'section',
        'blocks': {
            'h': {'type': 'text', 'settings': {
                'text': '<h2>Everything they need to land running</h2>',
                'width': 'fit-content', 'max_width': 'normal', 'alignment': 'center',
                'type_preset': 'h2', 'font': 'var(--font-body--family)',
                'line_height': 'normal', 'letter_spacing': 'normal', 'case': 'none',
                'wrap': 'pretty', 'text_color': '#FFFFFF', 'background': False,
                'background_color': '#00000026', 'corner_radius': 0,
                'padding-block-start': 0, 'padding-block-end': 0,
                'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}},
            'p': {'type': 'text', 'settings': {
                'text': '<p>Each kit bundles four essentials for one job and costs '
                        'less than buying them apart.</p>',
                'width': 'fit-content', 'max_width': '560px', 'alignment': 'center',
                'type_preset': 'paragraph', 'font': 'var(--font-body--family)',
                'line_height': 'normal', 'letter_spacing': 'normal', 'case': 'none',
                'wrap': 'pretty', 'text_color': '#FFFFFF', 'background': False,
                'background_color': '#00000026', 'corner_radius': 0,
                'padding-block-start': 0, 'padding-block-end': 0,
                'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}},
            'b': {'type': 'button', 'settings': {
                'label': 'Shop the kits', 'link': 'shopify://collections/bundles-kits',
                'open_in_new_tab': False, 'style_class': 'button-custom',
                'custom_button_background': '#FFFFFF',
                'custom_button_text': '#33332D', 'custom_button_border': '#FFFFFF',
                'width': 'fit-content', 'custom_width': 100,
                'width_mobile': 'fit-content', 'custom_width_mobile': 100},
                'blocks': {}},
        },
        'block_order': ['h', 'p', 'b'],
        'settings': {
            'content_direction': 'column', 'vertical_on_mobile': True,
            'horizontal_alignment': 'center', 'vertical_alignment': 'center',
            'align_baseline': False,
            'horizontal_alignment_flex_direction_column': 'center',
            'vertical_alignment_flex_direction_column': 'center', 'gap': 20,
            'section_width': 'full-width', 'section_height': 'large',
            'section_height_custom': 50,
            'background_media': 'image',
            'background_image': 'shopify://shop_images/band-puppy-12538668.jpg',
            'background_image_position': 'cover',
            'background_color': '#6B8F71',
            'toggle_overlay': True, 'overlay_color': '#22301F45',
            'overlay_style': 'solid', 'gradient_direction': 'to bottom',
            'padding-block-start': 96, 'padding-block-end': 96,
        },
    }

    # kit row shows all four kits
    for b in S['bundle_head']['blocks'].values():
        t = b['settings'].get('text', '')
        if t.startswith('<p>'):
            b['settings']['text'] = ('<p>New puppy, grooming, senior comfort and play. '
                                     'The saving on each is real and shown on the page.</p>')
    S['bundle_products']['settings']['max_products'] = 4

    # category tiles: all four collections, photo led
    c = S['collection_list']['settings']
    c['collection_list'] = [
        'gid://shopify/Collection/517062132001',   # toys
        'gid://shopify/Collection/516731339041',   # grooming
        'gid://shopify/Collection/516731371809',   # comfort
        'gid://shopify/Collection/516867031329',   # bundles
    ]
    c['columns'] = 4
    c['max_collections'] = 4
    c['mobile_columns'] = '2'
    for b in S['cats_head']['blocks'].values():
        t = b['settings'].get('text', '')
        if t.startswith('<p>'):
            b['settings']['text'] = '<p>Toys, grooming, comfort and complete kits.</p>'

    # story band: photography instead of flat green, honest copy, no dashes
    st = S['story']['settings']
    st['background_media'] = 'image'
    st['background_image'] = 'shopify://shop_images/band-story-6589017.jpg'
    st['background_image_position'] = 'cover'
    st['toggle_overlay'] = True
    st['overlay_color'] = '#22301F66'
    st['overlay_style'] = 'solid'
    st['padding-block-start'] = 96
    st['padding-block-end'] = 96
    S['story']['blocks']['p']['settings']['text'] = (
        '<p>Most pet gear is designed for the easy dog, the one who sits still for a '
        'nail trim and sleeps anywhere. Wagvive started from the other end: the dog who '
        'flinches at clippers, the senior who takes a run-up to stand, the one who '
        'drinks too little because the bowl slides across the floor.</p>'
        '<p>Every product here was picked for a specific, ordinary problem, and every '
        'one had to earn its place.</p>')

    # drop the redundant kit CTA row and slot the band into the order
    S.pop('bundle_cta', None)
    order = [s for s in idx['order'] if s != 'bundle_cta']
    if 'kit_band' not in order:
        order.insert(order.index('bundle_head'), 'kit_band')
    # tiles after kits: hero, marquee, featured, band, kits, cats, story...
    idx['order'] = order

    # template-wide dash sweep (the JSON kept em dashes dedash.py never saw)
    raw = json.dumps(idx, ensure_ascii=False)
    for old, new in (
        (' &mdash; ', ', '), (' &ndash; ', ', '),
        ('&mdash; ', ''), ('&ndash; ', ''), ('&mdash;', ', '), ('&ndash;', ', '),
    ):
        raw = raw.replace(old, new)
    idx = json.loads(raw)

    api('PUT', f'themes/{theme_id}/assets.json',
        {'asset': {'key': key, 'value': json.dumps(idx, ensure_ascii=False, indent=2)}})
    print(f'   sections now: {" > ".join(idx["order"])}')


def typography(theme_id):
    print('== typography ==')
    key = 'config/settings_data.json'
    q = urllib.parse.quote(key)
    sd = json.loads(api('GET', f'themes/{theme_id}/assets.json?asset[key]={q}')
                    ['asset']['value'])
    cur = sd['current']
    cur['type_heading_font'] = 'archivo_n6'
    cur['type_subheading_font'] = 'archivo_n5'
    cur['type_accent_font'] = 'archivo_n6'
    cur['type_letter_spacing_h1'] = 'heading-loose'
    cur['type_letter_spacing_h2'] = 'heading-loose'
    cur['page_width'] = 'normal'
    api('PUT', f'themes/{theme_id}/assets.json',
        {'asset': {'key': key, 'value': json.dumps(sd, ensure_ascii=False, indent=2)}})
    print('   headings Archivo 600, subheads Archivo 500, body stays Inter')
    print('   page width narrow -> normal')


def main():
    theme = next(t for t in api('GET', 'themes.json')['themes'] if t['role'] == 'main')
    collections()
    featured()
    template(theme['id'])
    typography(theme['id'])
    print('\ndone')


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
