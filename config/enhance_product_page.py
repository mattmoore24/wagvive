#!/usr/bin/env python3
"""Add trust signals + a details accordion to the Wagvive product page buy box."""
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
SAGE, FG = '#6B8F71', '{{ settings.color_palette.foreground }}'


def asset(key, value=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/themes/{THEME}/assets.json'
    if value is None:
        req = urllib.request.Request(f'{url}?asset[key]={key}',
                                     headers={'X-Shopify-Access-Token': TOKEN})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())['asset']['value']
    req = urllib.request.Request(url, method='PUT',
        data=json.dumps({'asset': {'key': key, 'value': value}}).encode('utf-8'),
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def text(body, preset='paragraph', align='left', color=FG, max_width='normal',
         width='fit-content', pt=0, pb=0):
    return {'type': 'text', 'settings': {
        'text': body, 'width': width, 'max_width': max_width, 'alignment': align,
        'type_preset': preset, 'font': 'var(--font-body--family)',
        'line_height': 'normal', 'letter_spacing': 'normal', 'case': 'none',
        'wrap': 'pretty', 'text_color': color, 'background': False,
        'background_color': '#00000026', 'corner_radius': 0,
        'padding-block-start': pt, 'padding-block-end': pb,
        'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}


def icon(name, width=22):
    return {'type': 'icon', 'settings': {
        'icon': name, 'width': width, 'link': '', 'open_in_new_tab': False,
        'icon_color': SAGE}, 'blocks': {}}


def group(children, order, direction='row', gap=8, width='fill', custom_width=100,
          align='flex-start', pt=0, pb=0):
    return {'type': 'group', 'settings': {
        'content_direction': direction, 'vertical_on_mobile': False,
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
        'padding-block-start': pt, 'padding-block-end': pb,
        'padding-inline-start': 0, 'padding-inline-end': 0},
        'blocks': children, 'block_order': order}


tpl = json.loads(asset('templates/product.json'))
details = tpl['sections']['main']['blocks']['product-details']

# --- trust row: three icon + label pairs -------------------------------------
trust_items = [
    ('t1', 'truck', 'Free US shipping over $60'),
    ('t2', 'return', '30-day returns'),
    ('t3', 'stopwatch', 'Ships in 1&ndash;3 business days'),
]
trust_children, trust_order = {}, []
for key, ic, label in trust_items:
    trust_children[key] = group(
        {'i': icon(ic), 'l': text(f'<p>{label}</p>', 'paragraph', 'left', FG)},
        ['i', 'l'], direction='row', gap=8, width='fill', align='flex-start')
    trust_order.append(key)

details['blocks']['wagvive_trust'] = group(
    trust_children, trust_order, direction='column', gap=10,
    width='fill', align='flex-start', pt=14, pb=6)

# --- details accordion -------------------------------------------------------
rows = [
    ('r1', 'Shipping &amp; delivery',
     '<p>Dispatched in 1&ndash;3 business days. Typical US delivery is 5&ndash;11 business '
     'days after dispatch, with tracking emailed as soon as it ships. Free over $60, '
     'otherwise $5.95 flat.</p>'),
    ('r2', 'Returns',
     '<p>30 days from delivery. Faulty, damaged, or incorrect items: we cover return '
     'shipping and replace or refund, your choice. Changed your mind is fine too &mdash; '
     'return postage is on you in that case.</p>'),
    ('r3', 'Care &amp; use',
     '<p>Rinse or wipe clean after use and let it dry fully before storing. Introduce '
     'new grooming tools gradually &mdash; a few short, calm sessions beat one long one, '
     'especially with older or anxious dogs.</p>'),
]
details['blocks']['wagvive_details'] = {
    'type': 'accordion',
    'settings': {'icon': 'plus', 'dividers': True, 'divider_color': '#33332D26',
                 'type_preset': 'h6', 'background_color': 'transparent',
                 'text_color': FG, 'border': 'none', 'border_width': 1,
                 'border_opacity': 100, 'border_color': '#00000026',
                 'border_radius': 0, 'padding-block-start': 12,
                 'padding-block-end': 0, 'padding-inline-start': 0,
                 'padding-inline-end': 0},
    'blocks': {k: {'type': '_accordion-row',
                   'settings': {'heading': h, 'open_by_default': False,
                                'icon': 'none', 'width': 20},
                   'blocks': {'a': text(body, 'rte', 'left', FG, 'normal', '100%')},
                   'block_order': ['a']} for k, h, body in rows},
    'block_order': [k for k, _, _ in rows]}

# place both after the buy buttons, before the description text
order = details['block_order']
anchor = order.index('buy_buttons_eYQEYi') + 1
for key in ('wagvive_details', 'wagvive_trust'):
    if key in order:
        order.remove(key)
order[anchor:anchor] = ['wagvive_trust', 'wagvive_details']

try:
    asset('templates/product.json', json.dumps(tpl, indent=2, ensure_ascii=False))
    print('Product page updated. Buy-box block order:')
    for b in details['block_order']:
        print('  -', details['blocks'][b]['type'], f'({b})')
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:800])
