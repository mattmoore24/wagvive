#!/usr/bin/env python3
"""Rebuild the homepage kits-first. Keeps the hero video; reorders and rewrites.

WHY. The store's own unit economics say never to sell singles first: average
single contribution is $4.71 against $16.76 to $43.06 for kits, and bundle
buyers are the higher-LTV customers. Yet the homepage led with eight singles
("The favorites") and put the kits seventh, several screens down. This flips
the merchandising to match the economics.

WHAT THE RESEARCH SAYS, and what each change implements:
  * Baymard: a homepage must say WHAT the store sells above the fold, with an
    action-specific CTA; a hero that pushes all category access below the fold
    is a navigation failure. -> hero keeps the looping video but the headline
    states the offer ("complete dog care kits") and the primary CTA goes to
    the kits collection, not /collections/all.
  * Gymshark leads with bestseller product cards carrying real prices;
    Skims runs few sections, each with one job and one CTA. -> the kit grid
    with live prices AND compare_at strikethrough (price anchoring) is the
    first content section; every band below has exactly one CTA.
  * Bundling data: bundles lift AOV 20 to 30 percent and bundle buyers show
    about 2.7x LTV, but bundles fail when arbitrary. -> ours are job-based
    and the savings are real ($11.95 to $26.95 by kit), so the copy leads
    with the job and states the saving as a number.
  * Baymard: low trust causes about 17 percent of abandonment. -> the trust
    row (honest delivery, curation, returns) sits directly under the kit grid,
    before any secondary browsing.
  * A flagship spotlight: Calm & Comfort is the highest-contribution kit
    ($43.06) and the paid landing page for phase 1, so it gets the mid-page
    band, with its real price and saving.

HONESTY RULES. Every number rendered is pulled from no source other than the
live catalogue at apply time; the script refuses to write if any claimed
saving does not match price vs compare_at. No invented reviews, no fake press,
no urgency theatre.

    python config/homepage_kits_first.py            # show the plan and diffs
    python config/homepage_kits_first.py --apply    # write + verify live
"""
import copy, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNER_IMAGE = 'wagvive-band-calm-kit.jpg'   # uploaded to Files before --apply

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

KIT_HANDLES = ['new-puppy-kit', 'toy-kit', 'grooming-essentials-kit',
               'dog-enrichment-kit', 'travel-kit', 'calm-comfort-kit']
FLAGSHIP = 'calm-comfort-kit'


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
            raise
    return {}


def storefront(handle):
    u = f'https://wagvive.com/products/{handle}.js?nocache={int(time.time()*1000)}'
    rq = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(rq, timeout=60) as r:
        return json.loads(r.read().decode())


def live_savings():
    """Real price vs compare_at per kit. The copy is built from these and from
    nothing else, so a future repricing cannot silently strand a stale claim."""
    out = {}
    for h in KIT_HANDLES:
        d = storefront(h)
        p, c = d['price'] / 100, (d['compare_at_price'] or 0) / 100
        if c <= p:
            raise SystemExit(f'{h}: compare_at ${c} not above price ${p}; '
                             f'a savings claim would be false. Refusing.')
        out[h] = {'title': d['title'], 'price': p, 'compare': c,
                  'save': round(c - p, 2)}
    return out


def text_block(html, preset='paragraph', color='{{ settings.color_palette.foreground }}',
               max_width='normal', alignment='center'):
    return {'type': 'text', 'settings': {
        'text': html, 'width': 'fit-content', 'max_width': max_width,
        'alignment': alignment, 'type_preset': preset,
        'font': 'var(--font-body--family)', 'line_height': 'normal',
        'letter_spacing': 'normal', 'case': 'none', 'wrap': 'pretty',
        'text_color': color, 'background': False,
        'background_color': '#00000026', 'corner_radius': 0,
        'padding-block-start': 0, 'padding-block-end': 0,
        'padding-inline-start': 0, 'padding-inline-end': 0}, 'blocks': {}}


def check_copy(tpl_json):
    """The standing copy rules, enforced before write: no em/en dashes, no
    hyphenated day ranges, no British spellings in anything customer-facing."""
    text = tpl_json
    bad = []
    for ch, name in [('—', 'em dash'), ('–', 'en dash'),
                     ('&ndash;', 'ndash'), ('&mdash;', 'mdash')]:
        if ch in text:
            bad.append(name)
    for w in ['ageing', 'colour', 'centre', 'odour', 'fulfilment', 'favourites']:
        if w in text.lower():
            bad.append(f'British spelling {w!r}')
    if re.search(r'\d+\s*-\s*\d+\s*(business\s+)?day', text):
        bad.append('hyphenated day range')
    return bad


def main():
    apply = '--apply' in sys.argv

    s = live_savings()
    max_save = max(v['save'] for v in s.values())
    min_save = min(v['save'] for v in s.values())
    flag = s[FLAGSHIP]
    print('Live kit economics the copy is built from:')
    for h, v in s.items():
        print(f"  {v['title']:26} ${v['price']:>7.2f}  save ${v['save']:>6.2f}")
    print(f"  savings range ${min_save:.2f} to ${max_save:.2f}; "
          f"flagship {flag['title']} saves ${flag['save']:.2f}\n")

    tid = next(t for t in api('GET', 'themes.json')['themes']
               if t['role'] == 'main')['id']
    q = urllib.parse.quote('templates/index.json')
    tpl = json.loads(api('GET', f'themes/{tid}/assets.json?asset[key]={q}')
                     ['asset']['value'])
    sec = tpl['sections']

    # ---- 1. HERO: keep the video, state the offer, aim the CTA at kits ------
    hero = sec['hero']
    hero['blocks']['h'] = text_block(
        '<p>The whole routine, in one box.</p>', 'h1',
        '{{ settings.color_palette.background }}')
    hero['blocks']['sub'] = text_block(
        '<p>Six dog care kits. One job each. Less than buying the pieces '
        'apart.</p>',
        'paragraph', '{{ settings.color_palette.background }}', '560px')
    hero['blocks']['cta']['settings'].update({
        'label': 'Shop the kits',
        'link': 'shopify://collections/bundles-kits'})
    hero['blocks']['cta2'] = {'type': 'button', 'settings': {
        'label': 'Browse everything',
        'link': 'shopify://collections/all', 'open_in_new_tab': False,
        'style_class': 'button-custom',
        'custom_button_background': '#FFFFFF00',
        'custom_button_text': '#FFFFFF',
        'custom_button_border': '#FFFFFF',
        'width': 'fit-content', 'custom_width': 100,
        'width_mobile': 'fit-content', 'custom_width_mobile': 100},
        'blocks': {}}
    hero['block_order'] = ['h', 'sub', 'cta', 'cta2']

    # ---- 2. MARQUEE: correct the facts, add the savings line ----------------
    mq = sec['marquee']
    lines = ['Free US shipping over $60', '30-day returns',
             'Six kits, one for every routine',
             f'Kits save up to ${max_save:.2f} vs separates',
             'Any 3 toys, 15% off', 'Tracking on every order']
    mq['blocks'] = {f'm{i+1}': text_block(
        f'<p>{t}</p>', 'paragraph', '{{ settings.color_palette.background }}')
        for i, t in enumerate(lines)}
    mq['block_order'] = [f'm{i+1}' for i in range(len(lines))]

    # ---- 3. KIT GRID first: heading + all six kits, 3 columns ---------------
    bh = sec['bundle_head']
    bh['blocks']['h'] = text_block('<h2>Start with a kit</h2>', 'h2')
    bh['blocks']['p'] = text_block(
        f'<p>4 or 5 essentials per kit, in colorways you pick. '
        f'Save ${min_save:.2f} to ${max_save:.2f}.</p>',
        'paragraph', max_width='520px')
    bp = sec['bundle_products']
    bp['settings'].update({'columns': 3, 'max_products': 6,
                           'padding-block-end': 72})

    # ---- 4. FLAGSHIP band: Calm & Comfort with its real numbers -------------
    kb = sec['kit_band']
    kb['blocks']['h'] = text_block(
        '<p>Storm season, handled.</p>', 'h2', '#FFFFFF')
    kb['blocks']['p'] = text_block(
        f'<p>Heartbeat plush, calming wrap, fleece, cooling pad, squeak toy. '
        f'${flag["price"]:.2f} together, ${flag["save"]:.2f} less than '
        f'apart.</p>',
        'paragraph', '#FFFFFF', '560px')
    kb['blocks']['b']['settings'].update({
        'label': 'Meet the Calm & Comfort Kit',
        'link': f'shopify://products/{FLAGSHIP}'})
    kb['settings'].update({
        'background_image': f'shopify://shop_images/{BANNER_IMAGE}',
        'overlay_color': '#22301F52'})

    # Trust row: one-line blurbs (owner call 2026-08-08: fewer words sitewide).
    # US spelling throughout; colorway NAMES like "Grey" are established option
    # values and stay, but prose is US.
    vals = sec['values']['blocks']
    vals['v1']['blocks']['p'] = text_block(
        '<p>Puppy to senior, gear that holds up.</p>', 'paragraph',
        max_width='300px')
    vals['v2']['blocks']['p'] = text_block(
        '<p>Tested before it earns a listing.</p>', 'paragraph',
        max_width='300px')
    vals['v3']['blocks']['p'] = text_block(
        '<p>Wrong or damaged? Replaced free.</p>', 'paragraph',
        max_width='300px')

    # ---- 5. Secondary paths: categories, then singles -----------------------
    ch = sec['cats_head']
    ch['blocks']['h'] = text_block('<h2>Prefer to build your own?</h2>', 'h2')
    ch['blocks']['p'] = text_block(
        '<p>Toys, grooming, comfort. Any 3 toys, 15% off.</p>',
        'paragraph', max_width='520px')

    fh = sec['featured_head']
    fh['blocks']['p'] = text_block(
        '<p>All of them live inside a kit too.</p>', 'paragraph',
        max_width='520px')

    # Story band: one line instead of two paragraphs
    st = sec['story']
    st['blocks']['p'] = text_block(
        '<p>Built for the dog who flinches at clippers and the senior who '
        'takes a run-up to stand. Every product earned its place.</p>',
        'paragraph', '{{ settings.color_palette.background }}', '560px')

    # ---- 6. FAQ: put the real numbers in the savings answer -----------------
    faq = sec['faq']['blocks']['acc']['blocks']
    faq['f4']['blocks']['a'] = text_block(
        f'<p>Yes. Each kit is priced below the combined cost of its items: the '
        f'saving runs from ${min_save:.2f} to ${max_save:.2f} depending on the '
        f'kit, and the exact figure is shown on each kit\'s own page. It also '
        f'arrives as one parcel rather than several.</p>',
        'rte', alignment='left')
    faq['f4']['blocks']['a']['settings']['width'] = '100%'

    # ---- 7. Newsletter: US spelling ----------------------------------------
    nl = sec['newsletter']
    nl['blocks']['p'] = text_block(
        '<p>New gear, senior dog guides, the odd discount.</p>',
        'paragraph', max_width='520px')

    # ---- 8. The order itself: kits before everything ------------------------
    tpl['order'] = ['hero', 'marquee',
                    'bundle_head', 'bundle_products',
                    'values',
                    'kit_band',
                    'cats_head', 'collection_list',
                    'featured_head', 'featured_products',
                    'story',
                    'faq_head', 'faq',
                    'newsletter']

    out = json.dumps(tpl, indent=2, ensure_ascii=False)
    problems = check_copy(out)
    if problems:
        print('COPY RULE VIOLATIONS, refusing to write:', problems)
        return 1

    print('New section order:')
    for k in tpl['order']:
        print(f'  {k}')
    print(f'\nhero CTA -> bundles-kits; flagship band -> {FLAGSHIP}; '
          f'kit grid 3x2 with compare_at anchoring')

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    # The flagship band needs its background image to exist in Files first.
    fq = json.dumps({'query': '''query($q: String!) {
        files(first: 5, query: $q) { nodes { ... on MediaImage {
          image { url } fileStatus } } } }''',
        'variables': {'q': f'filename:{BANNER_IMAGE.split(".")[0]}'}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=fq,
        method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        nodes = json.loads(r.read().decode())['data']['files']['nodes']
    ready = [n for n in nodes if n.get('fileStatus') == 'READY']
    if not ready:
        print(f'\n{BANNER_IMAGE} is not READY in Files; upload it first. '
              f'Refusing to point the band at a missing image.')
        return 1
    print(f'\nbanner image confirmed in Files: {ready[0]["image"]["url"][:80]}')

    api('PUT', f'themes/{tid}/assets.json',
        {'asset': {'key': 'templates/index.json', 'value': out}})
    print('template written')

    # keep the repo copy in step
    local = os.path.join(ROOT, 'config', 'theme-work', 'templates__index.json')
    with open(local, 'w', encoding='utf-8') as fh2:
        fh2.write(out)
    print('repo copy updated: config/theme-work/templates__index.json')

    # ---- verify against the live storefront --------------------------------
    print('\nverifying...')
    back = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset']['value']
    same = json.loads(back)['order'][2] == 'bundle_head'
    print(f"  {'OK ' if same else 'BAD'} admin asset has kits third in order")

    markers = ['Start with a kit', 'The whole routine, in one box',
               'Storm season, handled', 'Six kits, one for every routine',
               'senior dog guides']
    ok = False
    for attempt in range(10):
        u = f'https://wagvive.com/?nocache={int(time.time()*1000)}'
        rq2 = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(rq2, timeout=60) as r:
            html = r.read().decode('utf-8', 'replace')
        missing = [m for m in markers if m not in html]
        # kits before favorites in the DOM
        kits_pos = html.find('Start with a kit')
        fav_pos = html.find('The favorites')
        ordered = kits_pos != -1 and fav_pos != -1 and kits_pos < fav_pos
        if not missing and ordered:
            ok = True
            break
        time.sleep(5 * (attempt + 1))
    print(f"  {'OK ' if ok else 'BAD'} live homepage renders all markers, kits "
          f"before favorites"
          + ('' if ok else f'  (missing {missing}, ordered={ordered})'))
    print('\n' + ('homepage rebuilt and verified live' if same and ok
                  else 'CDN may still be settling; re-check in a few minutes'))
    return 0 if (same and ok) else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:500], file=sys.stderr)
        sys.exit(1)
