#!/usr/bin/env python3
"""Create the first wave of CJ US-WAREHOUSE products.

WHY THESE. Picked from a sweep of all 57 dog-relevant CJ categories for
`countryCode=US` stock (1,532 products, 175 candidates, 34 verified live;
docs/cj-us-sourcing-shortlist-2026-09.md). Every variant of every product here
was checked individually against `/product/stock/queryBySku` and holds real US
warehouse units, and each quotes a 3 to 5 or 3 to 7 day US domestic carrier.
That is the whole point: US stock skips CJ's 5 to 11 day handling step, which
is where the delivery time actually goes (docs/knowledge/cj-delay-diagnosis-2026-08.md).

  LED Safety Halo Collar   806 other CJ sellers, the most-listed item found
                           anywhere in the sweep. 230 US units on every one of
                           its 20 variants. Night-walk safety is a real need
                           the store does not serve at all.
  3-in-1 Travel Bowl       143 sellers, 230 US units per variant. Complements
                           the Travel Water Bottle directly and is a natural
                           Travel Kit component.
  Dog GPS Tracker          295 sellers, 34 US units. SUBSCRIPTION REQUIRED and
                           said so prominently, see below.

THE GPS TRACKER NEEDS A PAID SUBSCRIPTION, AND THAT IS DISCLOSED THREE TIMES:
in the first line of the body, in a bordered callout, and in the SEO
description that shows in Google. CJ's own title ends "Subscription Required"
and the plans run $28.99 for 3 months to $74.99 a year, paid to the device
maker and not to Wagvive. A customer discovering a $75/year commitment after
paying $27.99 is a refund, a chargeback and a bad review, and burying it would
be exactly the kind of small untruth the delivery-promise work exists to
remove. If the owner would rather not carry a third-party subscription he
cannot support, unpublish it; the disclosure is written so that decision can
be made from the live page.

SIZING. The Halo Collar is the only sized product here, and CJ's four sizes
overlap almost completely (neck 14 to 16.5, 15 to 19, 16 to 21, 17 to 23
inches), which is precisely the confusion `config/size_scale.py` exists to
kill. Mapped to the canonical scale by NECK girth against each band's dogs:

    CJ Small   14 to 16.5in  ->  M   (25 to 50 lb, neck about 33 to 42cm)
    CJ Large   16 to 21in    ->  L   (50 to 90 lb, neck about 43 to 53cm)
    CJ X-Large 17 to 23in    ->  XL  (90 lb and up, neck about 50 to 60cm)
    CJ Medium  15 to 19in    ->  RETIRED, redundant between Small and Large

It does not start at XS or S: the smallest CJ size only closes to a 14 inch
neck, which is bigger than a Shih Tzu's. The guide says so rather than letting
a chihuahua owner order one.

MONEY, at the 20% floor with $5.50 US domestic freight
(landed = (goods + freight) x 1.03, margin nets the 3.103% payment fee and
$0.30). Every US-origin freight quote came back $0.00, which freight_floor.py
knows is missing data and not free carriage; $5.50 is the middle of the only
real observations on this account (GOFO+ $4.98, USPS+ $5.10 to $5.26).

    Halo Collar  goods $13.03  ->  $25.99   22.3%
    Travel Bowl  goods $12.26  ->  $24.99   22.5%
    GPS Tracker  goods $14.39  ->  $27.99   22.6%

    python config/add_us_warehouse_wave1.py            # report
    python config/add_us_warehouse_wave1.py --apply    # create as draft
    python config/add_us_warehouse_wave1.py --finish --apply
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'config'))
import delivery_promise as DP          # noqa: E402
import size_scale as SS                # noqa: E402

SHOP_LOCATION = 113363058977           # canonical; the only location that can sell
COMFORT_HEALTH_ID = 516731371809       # manual collection; needs an explicit collect
FLOOR_PCT = 20.0                       # the store-wide non-negotiable

SIZING_CSS = (
    '<style>.wv-size{width:100%;border-collapse:collapse;margin:0 0 1em;'
    'font-size:.95em}.wv-size th,.wv-size td{border:1px solid #DCD2C1;'
    'padding:.5em .6em;text-align:left;vertical-align:top}'
    '.wv-size th{background:#F7F2E9;font-weight:600}</style>')


def table(headers, rows):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
                   for r in rows)
    return (f'{SIZING_CSS}<table class="wv-size"><thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


# --------------------------------------------------------------- halo collar
# neck ranges transcribed from CJ's own description text.
HALO_NECK = {'M': '14 to 16.5 in (36 to 42 cm)',
             'L': '16 to 21 in (41 to 53 cm)',
             'XL': '17 to 23 in (43 to 58 cm)'}
HALO_GUIDE = (
    '<h3>Choosing a size</h3>'
    '<p>This one is sized by your dog’s NECK, not their chest, because it is '
    'a collar. Pick by weight using the table, and if you want to be exact, run '
    'a soft tape around the neck where a collar sits. Every size here means the '
    'same dog it means everywhere else on Wagvive.</p>'
    + table(['Size', 'Dog weight', 'Typical breeds', 'Adjusts to fit a neck of'],
            [(f'<strong>{s}</strong>', SS.weight_text(s), SS.BY_SIZE[s]['breeds'],
              HALO_NECK[s]) for s in ('M', 'L', 'XL')])
    + '<p>If your dog is between two sizes, choose the larger one and take up '
      'the slack on the slider.</p>'
    + '<p><strong>This collar starts at M.</strong> The smallest size only '
      'closes down to a 14 in (36 cm) neck, which is larger than most toy and '
      'small breeds, so it is not the right buy for a chihuahua or a shih tzu.</p>')

HALO_BODY = (
    '<p><strong>They stay visible after dark, and you stop squinting into the '
    'garden.</strong></p>'
    '<p>A soft nylon collar with a light strip running the whole way round, '
    'bright enough to pick out at a distance on an unlit path. It is the '
    'difference between a dog you can see from the back door and a dog you are '
    'calling into the dark. Charges nothing, takes a coin cell, and switches '
    'between a steady glow and two flashing speeds.</p>'
    '<ul>'
    '<li><strong>Visible from a long way off</strong>, which matters on lanes, '
    'in parks and around traffic</li>'
    '<li><strong>Three modes</strong>, steady, slow flash and fast flash, on a '
    'single button</li>'
    '<li><strong>Ordinary collar underneath</strong>, with a D-ring for a lead '
    'and tags, so it replaces rather than adds</li>'
    '<li><strong>Adjustable nylon webbing</strong> with a quick-release buckle</li>'
    '<li><strong>Five colours</strong>, so it is findable in daylight too</li>'
    '</ul>'
    + HALO_GUIDE)

HALO_COLOURS = ['Red', 'Blue', 'Orange', 'Hot Pink', 'Green']
# canonical size -> CJ's size word inside the variantKey
HALO_SIZE_TO_CJ = {'M': 'SMALL', 'L': 'LARGE', 'XL': 'XLARGE'}

# ----------------------------------------------------------------- bowl
BOWL_GUIDE = (
    '<h3>Choosing a size</h3>'
    '<p>This is sized by how much it holds, not by your dog, so both sizes suit '
    'any breed. Pick by how much your dog drinks in one sitting.</p>'
    + table(['Capacity', 'Holds', 'Best for'],
            [('<strong>450 ml</strong>', '15 fl oz',
              'Small and medium dogs, day walks, and anywhere packing small '
              'matters more than capacity'),
             ('<strong>650 ml</strong>', '22 fl oz',
              'Larger dogs, hot days, long hikes, and two dogs sharing one '
              'stop')])
    + '<p>Colours differ by size: the 450 ml comes in green and blue, and the '
      '650 ml adds pink and yellow.</p>')

BOWL_BODY = (
    '<p><strong>Three things in one pocket-sized disc.</strong></p>'
    '<p>It folds flat to about the size of a coaster, opens into a proper bowl, '
    'and the raised pattern moulded into the base slows a dog who inhales '
    'their food. Suction cups underneath hold it still on a hard floor or a '
    'car boot, which is the part most travel bowls get wrong.</p>'
    '<ul>'
    '<li><strong>Folds flat</strong> and springs back into shape, so it lives '
    'in a coat pocket or a glovebox</li>'
    '<li><strong>Slow-feeder base</strong> makes a fast eater work around the '
    'ridges instead of gulping</li>'
    '<li><strong>Suction cups underneath</strong> stop it sliding across the '
    'floor or tipping in the car</li>'
    '<li><strong>Food-grade silicone</strong>, so it takes water or dry food '
    'and rinses clean</li>'
    '<li><strong>Loop on the rim</strong> for a carabiner or a lead</li>'
    '</ul>'
    + BOWL_GUIDE)

BOWL_VARIANTS = [                       # (Colour, Capacity, CJ sku)
    ('Green', '450 ml', 'CJPB26582870002'),
    ('Blue', '450 ml', 'CJPB26582870003'),
    ('Green', '650 ml', 'CJPB26582870006'),
    ('Blue', '650 ml', 'CJPB26582870007'),
    ('Pink', '650 ml', 'CJPB26582870005'),
    ('Yellow', '650 ml', 'CJPB26582870008'),
]

# ------------------------------------------------------------------ gps
GPS_SUBSCRIPTION = (
    '<div style="border:2px solid #3A3026; padding:14px 16px; margin:18px 0; '
    'background:#F7F2E9;">'
    '<p style="margin:0 0 8px 0;"><strong>This tracker needs a paid data plan '
    'to work, and it is not ours.</strong></p>'
    '<p style="margin:0;">Live GPS needs a mobile connection, so the maker '
    'charges for it separately: about $28.99 for 3 months, $46.99 for 6 months '
    'or $74.99 for a year, paid to them in their app when you set the tracker '
    'up. Without a plan you still get the QR tag on the back, but you do not '
    'get live tracking, the geofence or the alerts. We would rather you knew '
    'that before you bought it than after.</p></div>')

GPS_BODY = (
    '<p><strong>Know where they are, and know the moment they leave the '
    'garden.</strong></p>'
    + GPS_SUBSCRIPTION +
    '<p>A 28 gram tag that clips onto the collar your dog already wears and '
    'reports its position in real time. Draw a safe zone around your garden or '
    'your yard in the app and your phone tells you the moment they cross it, '
    'which is the alert that actually prevents a lost dog rather than helping '
    'you chase one.</p>'
    '<ul>'
    '<li><strong>Live position</strong> on a map, with no distance limit as '
    'long as there is mobile coverage</li>'
    '<li><strong>Geofence alerts</strong> when they leave an area you have '
    'drawn</li>'
    '<li><strong>Route history</strong>, so you can see where they went and '
    'how far they walked</li>'
    '<li><strong>Beeper and flashing light</strong> you can trigger from the '
    'app when they are close but out of sight</li>'
    '<li><strong>QR tag on the back</strong> that shows your contact details '
    'to whoever finds them, and keeps working when the battery is flat</li>'
    '<li><strong>IP67 waterproof</strong>, and up to 9 days on a charge</li>'
    '<li><strong>Fits most collars</strong> with the included buckle. Works '
    'with iPhone and Android</li>'
    '</ul>'
    '<p>It is 2.5 x 1.5 x 0.7 in (63.5 x 38 x 18.5 mm) and weighs about an '
    'ounce, so a medium dog will not notice it.</p>')

PRODUCTS = {
 'wagvive-led-safety-halo-collar': dict(
   title='Wagvive LED Safety Halo Collar',
   price='25.99', weight_g=800.0, spu='CJTR2301714',
   product_type='Comfort & Health',
   tags='collar, dog, led, night, outdoor, safety, visibility, walks',
   body=HALO_BODY,
   seo_title='LED Dog Collar, Light Up Collar for Night Walks, M to XL',
   seo_desc=('A soft nylon collar with a light strip all the way round, so you '
             'can see your dog after dark. Steady or flashing, five colours, '
             'sizes M to XL.'),
   options=[('Color', HALO_COLOURS), ('Size', ['M', 'L', 'XL'])],
   variants=None,      # resolved at runtime from CJ, see halo_variants()
 ),
 'wagvive-3-in-1-travel-bowl': dict(
   title='Wagvive 3-in-1 Travel Bowl',
   price='24.99', weight_g=132.0, spu='CJPB2658287',
   product_type='Comfort & Health',
   tags='bowl, collapsible, dog, feeding, hydration, outdoor, slow feeder, travel',
   body=BOWL_BODY,
   seo_title='Collapsible Dog Travel Bowl with Slow Feeder Base',
   seo_desc=('Folds flat to a coaster, opens into a proper bowl, and the '
             'ridged base slows a fast eater. Suction cups underneath. '
             '450 ml and 650 ml.'),
   options=[('Color', ['Green', 'Blue', 'Pink', 'Yellow']),
            ('Capacity', ['450 ml', '650 ml'])],
   variants=BOWL_VARIANTS,
 ),
 'wagvive-gps-pet-tracker': dict(
   title='Wagvive GPS Pet Tracker',
   price='27.99', weight_g=38.0, spu='CJBC2653057',
   product_type='Comfort & Health',
   tags='dog, geofence, gps, outdoor, safety, tracker, travel, walks',
   body=GPS_BODY,
   seo_title='Real Time Dog GPS Tracker with Geofence (Plan Required)',
   seo_desc=('Live GPS tracking, geofence alerts and route history, with a QR '
             'tag that works even when the battery dies. Needs a paid data '
             'plan from the maker.'),
   options=[],
   variants=[('Blue and white', None, 'CJBC265305702BY')],
 ),
}

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


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read().decode()
            time.sleep(0.6)
            return json.loads(b) if b.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise SystemExit(f'{method} {path}: {exc.code} '
                             f'{exc.read().decode()[:300]}')
    return {}


def gql(q, v=None):
    body = json.dumps({'query': q, 'variables': v or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit(json.dumps(out['errors'])[:600])
    time.sleep(0.4)
    return out


HALO_SKU_BY_KEY = {}


def halo_variants():
    """[(colour, canonical size, CJ sku)] resolved from CJ's live variant list.

    Resolved rather than transcribed: 20 hand-typed SKUs is 20 chances to pair
    a colour to the wrong one, and a mispaired SKU sends the customer a
    different colour than the swatch they clicked. CJ's variantKey is the
    authority.
    """
    import cj_api
    if not HALO_SKU_BY_KEY:
        res = cj_api.call('/product/query', {'productSku': 'CJTR2301714'}) or {}
        if str(res.get('code')) == '16900500':
            raise SystemExit('CJ points quota exhausted; stop, do not retry.')
        d = res.get('data')
        if isinstance(d, list):
            d = d[0] if d else {}
        for v in (d or {}).get('variants') or []:
            HALO_SKU_BY_KEY[str(v.get('variantKey')).upper()] = v.get('variantSku')
    if not HALO_SKU_BY_KEY:
        raise SystemExit('CJ returned no variants for the Halo Collar. '
                         'An empty answer is UNKNOWN, not a finding: re-run.')
    out = []
    for colour in HALO_COLOURS:
        for size in ('M', 'L', 'XL'):
            key = f'{colour.upper()}-{HALO_SIZE_TO_CJ[size]}'
            sku = HALO_SKU_BY_KEY.get(key)
            if not sku:
                raise SystemExit(f'CJ has no variant {key!r}; refusing to guess')
            out.append((colour, size, sku))
    return out


def variants_for(handle):
    cfg = PRODUCTS[handle]
    return halo_variants() if cfg['variants'] is None else cfg['variants']


def existing(handle):
    for p in api('GET', 'products.json?limit=250&status=any')['products']:
        if p['handle'] == handle:
            return p
    return None


def cj_stock_for(skus):
    """{sku: units} via sync_inventory, the only sanctioned reader, with retry.

    An empty answer from CJ is UNKNOWN, never zero. Creating a product with a
    zeroed variant publishes something nobody can buy, which is exactly what
    happened to the Dental Chew Stick on 2026-08-08.
    """
    import sync_inventory
    out = {}
    for sku in skus:
        n = None
        for attempt in range(3):
            try:
                n = sync_inventory.cj_stock(sku)
                if n is not None:
                    break
            except Exception:
                pass
            time.sleep(1.5 * (attempt + 1))
        if n is None:
            raise SystemExit(f'CJ would not report stock for {sku} after 3 tries. '
                             f'Refusing to create a product with an unknown '
                             f'quantity; re-run later.')
        out[sku] = n
    return out


def build_payload(handle):
    cfg = PRODUCTS[handle]
    vs = variants_for(handle)
    opts = cfg['options']
    variants = []
    for row in vs:
        if not opts:                                   # single-variant product
            _, _, sku = row
            v = {'sku': sku, 'option1': 'Default Title'}
        elif len(opts) == 1:
            name, _, sku = row
            v = {'sku': sku, 'option1': name}
        else:
            a, b, sku = row
            v = {'sku': sku, 'option1': a, 'option2': b}
        v.update({'price': cfg['price'], 'grams': cfg['weight_g'],
                  'weight': cfg['weight_g'], 'weight_unit': 'g',
                  'inventory_management': 'shopify',
                  'inventory_policy': 'deny',
                  'requires_shipping': True, 'taxable': True})
        variants.append(v)

    body = cfg['body'] + DP.DELIVERY_BLOCK
    payload = {'product': {
        'title': cfg['title'], 'handle': handle, 'body_html': body,
        'vendor': 'Wagvive', 'product_type': cfg['product_type'],
        'status': 'draft', 'tags': cfg['tags'], 'variants': variants}}
    if opts:
        payload['product']['options'] = [{'name': n, 'values': v} for n, v in opts]
    return payload


def main():
    apply = '--apply' in sys.argv
    if '--finish' in sys.argv:
        return finish(apply)

    total_new = 0
    for handle, cfg in PRODUCTS.items():
        vs = variants_for(handle)
        print(f"\n{cfg['title']}   {handle}")
        print(f"  CJ {cfg['spu']}   ${cfg['price']}   floor {FLOOR_PCT}%   "
              f"{len(vs)} variants   type {cfg['product_type']}")
        for row in vs[:4]:
            print(f"    {str(row[0]):12} {str(row[1] or ''):8} {row[2]}")
        if len(vs) > 4:
            print(f'    ... and {len(vs) - 4} more')
        already = existing(handle)
        if already:
            print(f"  EXISTS id={already['id']} status={already['status']}")
        else:
            total_new += 1

    if not apply:
        print(f'\n{total_new} product(s) would be created as DRAFT. Use --apply.')
        return 0

    for handle, cfg in PRODUCTS.items():
        if existing(handle):
            print(f'{handle}: exists, skipping')
            continue
        vs = variants_for(handle)
        stock = cj_stock_for([r[2] for r in vs])
        prod = api('POST', 'products.json', build_payload(handle))['product']
        pid = prod['id']
        print(f"\ncreated {cfg['title']} id={pid} (draft)")

        gid = f'gid://shopify/Product/{pid}'
        gql('''mutation($input: ProductInput!) {
                 productUpdate(input: $input) { product { id }
                   userErrors { field message } } }''',
            {'input': {'id': gid, 'metafields': [
                {'namespace': 'global', 'key': 'title_tag',
                 'type': 'single_line_text_field', 'value': cfg['seo_title']},
                {'namespace': 'global', 'key': 'description_tag',
                 'type': 'multi_line_text_field', 'value': cfg['seo_desc']}]}})
        print('  SEO set')

        # product_type alone does not join a MANUAL collection. Comfort &
        # Health is manual; Travel & Outdoor is smart and picks these up from
        # the "outdoor"/"travel" tags without a collect.
        api('POST', 'collects.json',
            {'collect': {'product_id': pid, 'collection_id': COMFORT_HEALTH_ID}})
        print('  added to the Comfort & Health collection')

        for v in prod['variants']:
            q = stock.get(v['sku'], 0)
            api('POST', 'inventory_levels/set.json',
                {'location_id': SHOP_LOCATION,
                 'inventory_item_id': v['inventory_item_id'], 'available': q})
        print(f"  stock written for {len(prod['variants'])} variants at Shop location")
    print('\nAll created as DRAFT. Next: imagery, then --finish --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
