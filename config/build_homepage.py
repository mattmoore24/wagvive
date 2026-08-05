#!/usr/bin/env python3
"""Compose the Wagvive homepage (templates/index.json) for the Horizon theme."""
import json, os, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
DOMAIN, TOKEN, VERSION = env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'], env['SHOPIFY_API_VERSION']
THEME = 187585560865

CREAM, SOFT_SAGE, WHITE, SAGE = '#F7F2E9', '#EDF2EE', '#FFFFFF', '#6B8F71'
FG = '{{ settings.color_palette.foreground }}'
BG = '{{ settings.color_palette.background }}'

C_FRONT, C_GROOMING, C_COMFORT, C_BUNDLES = 516730487073, 516731339041, 516731371809, 516867031329
gid = lambda i: f'gid://shopify/Collection/{i}'

PAD = {'padding-block-start': 0, 'padding-block-end': 0,
       'padding-inline-start': 0, 'padding-inline-end': 0}


def text(body, preset='paragraph', align='center', color=FG, max_width='normal',
         width='fit-content', pt=0, pb=0):
    return {'type': 'text', 'settings': {
        'text': body, 'width': width, 'max_width': max_width, 'alignment': align,
        'type_preset': preset, 'font': 'var(--font-body--family)',
        'line_height': 'normal', 'letter_spacing': 'normal', 'case': 'none',
        'wrap': 'pretty', 'text_color': color, 'background': False,
        'background_color': '#00000026', 'corner_radius': 0,
        'padding-block-start': pt, 'padding-block-end': pb,
        'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}


def button(label, link, bg=SAGE, fg='#FFFFFF', border=SAGE):
    return {'type': 'button', 'settings': {
        'label': label, 'link': link, 'open_in_new_tab': False,
        'style_class': 'button-custom', 'custom_button_background': bg,
        'custom_button_text': fg, 'custom_button_border': border,
        'width': 'fit-content', 'custom_width': 100,
        'width_mobile': 'fit-content', 'custom_width_mobile': 100}, 'blocks': {}}


def icon(name, color=SAGE, width=44):
    return {'type': 'icon', 'settings': {
        'icon': name, 'width': width, 'link': '', 'open_in_new_tab': False,
        'icon_color': color}, 'blocks': {}}


def group(children, order, direction='column', gap=10, width='fill',
          custom_width=100, align='center'):
    return {'type': 'group', 'settings': {
        'content_direction': direction, 'vertical_on_mobile': True,
        'horizontal_alignment': align, 'vertical_alignment': 'center',
        'align_baseline': False,
        'horizontal_alignment_flex_direction_column': align,
        'vertical_alignment_flex_direction_column': 'center',
        'gap': gap, 'width': width, 'custom_width': custom_width,
        'width_mobile': '100%', 'custom_width_mobile': 100,
        'height': 'fit-content', 'custom_height': 100,
        'background_media': 'none', 'background_color': 'transparent',
        'video_position': 'cover', 'background_image_position': 'cover',
        'toggle_overlay': False, 'overlay_color': '#00000026',
        'overlay_style': 'solid', 'gradient_direction': 'to bottom',
        'border': 'none', 'border_width': 1, 'border_opacity': 100,
        'border_color': '#00000026', 'border_radius': 0,
        'link': '', 'open_in_new_tab': False, 'placeholder': '',
        'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 12, 'padding-inline-end': 12},
        'blocks': children, 'block_order': order}


def section(blocks, order, bg=CREAM, pt=64, pb=64, direction='column', gap=16,
            align='center', width='page-width'):
    return {'type': 'section', 'blocks': blocks, 'block_order': order,
            'settings': {
                'content_direction': direction, 'vertical_on_mobile': True,
                'horizontal_alignment': align, 'vertical_alignment': 'center',
                'align_baseline': False,
                'horizontal_alignment_flex_direction_column': align,
                'vertical_alignment_flex_direction_column': 'center',
                'gap': gap, 'section_width': width, 'section_height': '',
                'section_height_custom': 50, 'background_media': 'none',
                'background_color': bg, 'video_position': 'cover',
                'background_image_position': 'cover', 'toggle_overlay': False,
                'overlay_color': '#00000026', 'overlay_style': 'solid',
                'gradient_direction': 'to bottom', 'border': 'none',
                'border_width': 1, 'border_opacity': 100,
                'border_color': '#00000026', 'border_radius': 0,
                'padding-block-start': pt, 'padding-block-end': pb}}


def product_card():
    return {'card': {'type': '_product-card', 'static': True, 'settings': {
        'product_card_gap': 6, 'border': 'none', 'border_width': 1,
        'border_opacity': 100, 'border_radius': 8, **PAD},
        'blocks': {
            'gallery': {'type': '_product-card-gallery', 'settings': {
                'image_ratio': 'square', 'border': 'none', 'border_width': 1,
                'border_opacity': 100, 'border_radius': 8, **PAD}, 'blocks': {}},
            'title': {'type': 'product-title', 'settings': {
                'width': '100%', 'max_width': 'normal', 'alignment': 'left',
                'type_preset': 'rte', 'font': 'var(--font-body--family)',
                'font_size': '1rem', 'line_height': 'normal',
                'letter_spacing': 'normal', 'case': 'none', 'wrap': 'pretty',
                'background': False, 'background_color': '#00000026',
                'corner_radius': 0, 'padding-block-start': 8,
                'padding-block-end': 0, 'padding-inline-start': 0,
                'padding-inline-end': 0}, 'blocks': {}},
            'price': {'type': 'price', 'settings': {
                'show_sale_price_first': True, 'show_installments': False,
                'show_tax_info': False, 'width': '100%', 'max_width': 'normal',
                'alignment': 'left', 'type_preset': 'paragraph',
                'font': 'var(--font-body--family)', 'font_size': '1rem',
                'line_height': 'normal', 'letter_spacing': 'normal',
                'case': 'none', 'background': False,
                'background_color': '#00000026', 'corner_radius': 0,
                'padding-block-start': 2, 'padding-block-end': 0,
                'padding-inline-start': 0, 'padding-inline-end': 0},
                'blocks': {}},
        },
        'block_order': ['gallery', 'title', 'price']}}


def product_list(collection_id, columns=4, max_products=4, bg=CREAM, pt=8, pb=64):
    return {'type': 'product-list', 'blocks': product_card(),
            'block_order': [],
            'settings': {
                'collection': gid(collection_id), 'layout_type': 'grid',
                'carousel_on_mobile': True, 'max_products': max_products,
                'columns': columns, 'mobile_columns': '2',
                'mobile_card_size': '75cqw', 'columns_gap': 24, 'rows_gap': 32,
                'icons_style': 'arrow', 'icons_shape': 'none',
                'section_width': 'page-width', 'horizontal_alignment': 'center',
                'gap': 24, 'background_color': bg,
                'padding-block-start': pt, 'padding-block-end': pb}}


# ---------------------------------------------------------------- sections
sections, order = {}, []


def add(key, payload):
    sections[key] = payload
    order.append(key)


# 1. Hero -----------------------------------------------------------------
add('hero', {
    'type': 'hero',
    'blocks': {
        'h': text('<p>Wellness for every wag.</p>', 'h1', 'center', BG, 'normal'),
        'sub': text('<p>Grooming and comfort essentials for dogs who have earned '
                    'a little extra care &mdash; chosen for the ones who find it hardest.</p>',
                    'paragraph', 'center', BG, '560px'),
        'cta': button('Shop the range', 'shopify://collections/all', '#FFFFFF', SAGE, '#FFFFFF'),
    },
    'block_order': ['h', 'sub', 'cta'],
    'settings': {
        'media_type_1': 'image', 'image_1': 'shopify://shop_images/wagvive-hero-bg.png',
        'media_type_2': 'image', 'stack_media_on_mobile': False,
        'custom_mobile_media': False, 'media_type_1_mobile': 'image',
        'media_type_2_mobile': 'image', 'open_in_new_tab': False,
        'content_direction': 'column', 'vertical_on_mobile': True,
        'horizontal_alignment': 'center', 'vertical_alignment': 'center',
        'align_baseline': True,
        'horizontal_alignment_flex_direction_column': 'center',
        'vertical_alignment_flex_direction_column': 'center',
        'gap': 24, 'section_width': 'full-width', 'section_height': 'large',
        'section_height_custom': 50, 'background_color': SAGE,
        'toggle_overlay': True, 'overlay_color': '#2B3A2E4D',
        'overlay_style': 'solid', 'gradient_direction': 'to bottom',
        'blurred_reflection': False, 'reflection_opacity': 75,
        'padding-block-start': 96, 'padding-block-end': 96}})

# 2. Value marquee --------------------------------------------------------
marquee_items = [
    ('m1', 'Free US shipping over $60'),
    ('m2', '30-day returns'),
    ('m3', 'Chosen for senior dogs'),
    ('m4', 'One vetted supplier'),
    ('m5', 'Tracking on every order'),
]
add('marquee', {
    'type': 'marquee',
    'blocks': {k: text(f'<p>{v}</p>', 'paragraph', 'center', BG) for k, v in marquee_items},
    'block_order': [k for k, _ in marquee_items],
    'settings': {'movement_direction': 'left', 'background_color': SAGE,
                 'padding-block-start': 14, 'padding-block-end': 14,
                 'gap_between_elements': 56}})

# 3. Featured products ----------------------------------------------------
add('featured_head', section(
    {'h': text('<h2>Start here</h2>', 'h2', 'center', FG),
     'p': text('<p>The four pieces most people reach for first.</p>',
               'paragraph', 'center', FG, '520px')},
    ['h', 'p'], bg=CREAM, pt=72, pb=8))
add('featured_products', product_list(C_FRONT, columns=4, max_products=4, bg=CREAM, pt=8, pb=72))

# 4. Why Wagvive ----------------------------------------------------------
values = [
    ('v1', 'paw_print', 'Chosen for senior dogs',
     'Quiet motors, low-vibration tools, and joint-friendly comfort gear &mdash; '
     'picked for the dogs who struggle most with grooming day.'),
    ('v2', 'check_box', 'One vetted supplier',
     'Every product ships from a single partner we audited on quality, rating, '
     'and years in business. Fewer split parcels, consistent standards.'),
    ('v3', 'return', '30 days to change your mind',
     'If it arrives wrong or damaged we cover return shipping and replace it. '
     'No arguing, no restocking fee.'),
]
add('values', section(
    {k: group({'i': icon(ic), 'h': text(f'<h3>{title}</h3>', 'h5', 'center', FG),
               'p': text(f'<p>{body}</p>', 'paragraph', 'center', FG, '340px')},
              ['i', 'h', 'p'], gap=12, width='custom', custom_width=33)
     for k, ic, title, body in values},
    [k for k, _, _, _ in values],
    bg=WHITE, pt=76, pb=76, direction='row', gap=32, align='center'))

# 5. Categories -----------------------------------------------------------
add('cats_head', section(
    {'h': text('<h2>Shop by need</h2>', 'h2', 'center', FG),
     'p': text('<p>Two routines, covered end to end.</p>', 'paragraph', 'center', FG, '520px')},
    ['h', 'p'], bg=SOFT_SAGE, pt=76, pb=8))
add('collection_list', {
    'type': 'collection-list',
    'settings': {
        'collection_list': [gid(C_GROOMING), gid(C_COMFORT)],
        'layout_type': 'grid', 'carousel_on_mobile': False, 'columns': 2,
        'mobile_columns': '1', 'mobile_card_size': '85cqw', 'columns_gap': 24,
        'bento_gap': 24, 'rows_gap': 24, 'max_collections': 2,
        'icons_style': 'arrow', 'icons_shape': 'none',
        'section_width': 'page-width', 'gap': 24, 'background_color': SOFT_SAGE,
        'padding-block-start': 8, 'padding-block-end': 76}})

# 6. Bundle upsell --------------------------------------------------------
add('bundle_head', section(
    {'h': text('<h2>Buy the routine, not just the tool</h2>', 'h2', 'center', FG),
     'p': text('<p>Each kit bundles four essentials for less than buying them '
               'separately &mdash; so a whole routine arrives in one parcel.</p>',
               'paragraph', 'center', FG, '560px')},
    ['h', 'p'], bg=CREAM, pt=76, pb=8))
add('bundle_products', product_list(C_BUNDLES, columns=2, max_products=2, bg=CREAM, pt=8, pb=40))
add('bundle_cta', section(
    {'b': button('See both kits', 'shopify://collections/bundles-kits')},
    ['b'], bg=CREAM, pt=0, pb=76))

# 7. Brand story ----------------------------------------------------------
add('story', section(
    {'h': text('<h2>We started with the hard parts</h2>', 'h2', 'center', BG),
     'p': text('<p>Most pet gear is designed for the easy dog &mdash; the one who sits '
               'still for a nail trim and sleeps anywhere. Wagvive started from the other '
               'end: the dog who flinches at clippers, the senior who takes a run-up to '
               'stand, the one who drinks too little because the bowl slides across the '
               'floor.</p><p>Every product here was picked for a specific, ordinary problem, '
               'from one supplier we could actually stand behind.</p>',
               'paragraph', 'center', BG, '660px'),
     'b': button('Read our story', 'shopify://pages/about', '#FFFFFF', SAGE, '#FFFFFF')},
    ['h', 'p', 'b'], bg=SAGE, pt=88, pb=88))

# 8. FAQ ------------------------------------------------------------------
faq = [
    ('f1', 'How long will delivery take?',
     '<p>Orders are processed in 1&ndash;3 business days, then typically arrive in '
     '5&ndash;11 business days within the US. Tracking is emailed the moment your parcel '
     'ships. We ship direct rather than paying for domestic warehousing &mdash; that keeps '
     'prices down, and we would rather say so plainly than surprise you at checkout.</p>'),
    # Was "Are these suitable for senior dogs?", which answered "that is who the
    # range was built around" - untrue since the Senior Dog Kit was retired.
    # Replaced 2026-08-04 with the question a six-kit store actually gets, which
    # is also the strongest AOV prompt on the page. See config/fix_home_faq.py.
    ('f2', 'Which kit should I start with?',
     '<p>Match it to the job in front of you. <strong>New Puppy</strong> covers the '
     'first month: crate, teething, teeth and first walks. <strong>Grooming '
     'Essentials</strong> is a full home session, coat to nails to teeth. '
     '<strong>Calm &amp; Comfort</strong> is for storms, fireworks and being left '
     'alone. <strong>Enrichment</strong> slows down dinner and gives a bored dog a '
     'job. <strong>Travel</strong> is the bag by the door, and the <strong>Toy '
     'Kit</strong> is five different games rather than five versions of the same '
     'one. Every kit costs less than buying its pieces separately.</p>'),
    ('f3', 'What if it is not right?',
     '<p>You have 30 days from delivery. If it arrived faulty, damaged, or wrong, we cover '
     'return shipping and send a replacement or full refund, your choice. Changed your '
     'mind is fine too; return shipping is on you in that case.</p>'),
    # No item count here: kits hold four OR five items, and a number in copy
    # goes stale silently. The saving is computed live on the kit page.
    ('f4', 'Do the kits actually save money?',
     '<p>Yes. Each kit is priced below the combined cost of its items, and the exact '
     'saving is shown on the kit\'s own page. It also arrives as one parcel rather '
     'than several.</p>'),
]
add('faq_head', section(
    {'h': text('<h2>Questions worth answering</h2>', 'h2', 'center', FG)},
    ['h'], bg=WHITE, pt=80, pb=8))
add('faq', section(
    {'acc': {'type': 'accordion', 'settings': {
        'icon': 'plus', 'dividers': True, 'divider_color': '#33332D26',
        'type_preset': 'h6', 'background_color': 'transparent',
        'text_color': FG, 'border': 'none', 'border_width': 1,
        'border_opacity': 100, 'border_color': '#00000026', 'border_radius': 0,
        'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 0, 'padding-inline-end': 0},
        'blocks': {k: {'type': '_accordion-row',
                       'settings': {'heading': q, 'open_by_default': i == 0,
                                    'icon': 'none', 'width': 20},
                       'blocks': {'a': text(a, 'rte', 'left', FG, 'normal', '100%')},
                       'block_order': ['a']}
                   for i, (k, q, a) in enumerate(faq)},
        'block_order': [k for k, _, _ in faq]}},
    ['acc'], bg=WHITE, pt=8, pb=88, width='narrow', align='flex-start'))

# 9. Newsletter -----------------------------------------------------------
add('newsletter', section(
    {'h': text('<h2>Get the good stuff, occasionally</h2>', 'h2', 'center', FG),
     'p': text('<p>New products, care guides for ageing dogs, and the odd discount. '
               'No daily email &mdash; we promise.</p>', 'paragraph', 'center', FG, '520px'),
     'e': {'type': 'email-signup', 'settings': {
         'width': '100%', 'custom_width': 100, 'heading': '',
         'heading_text_color': FG, 'heading_preset': 'h5',
         'border_style': 'solid', 'input_style': 'outline', 'border_width': 1,
         'border_radius': 6, 'input_background_color': '#FFFFFF',
         'input_text_color': FG, 'input_border_color': '#33332D33',
         'input_type_preset': 'paragraph', 'style_class': 'button-custom',
         'custom_button_background': SAGE, 'custom_button_text': '#FFFFFF',
         'custom_button_border': SAGE, 'link_text_color': FG,
         'display_type': 'inline', 'label': 'Email address',
         'integrated_button': True, 'button_type_preset': 'paragraph',
         'padding-block-start': 8, 'padding-block-end': 0,
         'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}},
    ['h', 'p', 'e'], bg=CREAM, pt=80, pb=88, width='narrow'))

template = {'sections': sections, 'order': order}

payload = {'asset': {'key': 'templates/index.json',
                     'value': json.dumps(template, indent=2, ensure_ascii=False)}}
req = urllib.request.Request(
    f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json',
    data=json.dumps(payload).encode('utf-8'), method='PUT',
    headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        res = json.loads(r.read().decode())
    print('Homepage updated. Sections in order:')
    for i, k in enumerate(order, 1):
        print(f'  {i:2}. {k:20} ({sections[k]["type"]})')
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:800])
