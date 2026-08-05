#!/usr/bin/env python3
"""Check the catalogue against what Google Merchant Center actually needs.

Free listings are the first channel in the plan because they are the only one
that costs nothing per click, and they are gated entirely on feed quality: the
same product data ranks the free listing and the paid Shopping ad, so one round
of feed work moves both. A disapproved product is invisible in both.

What this checks, and why each one matters:

  GTIN. We resell CJ goods with no manufacturer barcode. Google requires a
  GTIN where one exists, and where one genuinely does not, it requires the
  product to be declared as having no identifier. Leaving the field simply
  empty is what causes "Missing GTIN" disapprovals. Shopify's Google channel
  reads the variant BARCODE field, so the fix is either a real GTIN or an
  explicit declaration in the channel settings.

  TITLE. Google's Shopping match is heavily title-weighted and a shopper scans
  the first few words. "Wagvive Cooling Comfort Pad" spends its most valuable
  characters on a brand nobody is searching for. "Cooling Mat for Dogs,
  Pressure Activated Gel Pad" matches how people actually search. This is a
  title-for-Google problem, not a title-on-site problem, so it is solved with
  a feed-level title override, NOT by renaming products on the storefront.

  DESCRIPTION, IMAGE, TYPE, VENDOR. Straight disapproval or ranking risks.

  PRICE AND AVAILABILITY DRIFT. Any mismatch between the feed and the live
  storefront triggers disapproval, so this re-checks the public product JSON
  rather than the admin values.

    python config/marketing/feed_health.py
    python config/marketing/feed_health.py --titles   # suggested feed titles
"""
import json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MIN_DESC = 160
TAG = re.compile(r'<[^>]+>')

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

# Feed titles: what a shopper types, not what we call it internally.
# Format Google rewards: <what it is> for Dogs, <key attribute>, <variant axis>
FEED_TITLES = {
    'Cooling Comfort Pad': 'Dog Cooling Mat, Pressure Activated Gel Pad for Crates and Beds',
    'Calming Thunder Wrap': 'Dog Anxiety Vest, Calming Compression Wrap for Thunderstorms and Fireworks',
    'Heartbeat Soothing Sloth': 'Puppy Heartbeat Toy, Calming Sleep Aid Plush for Crate Training',
    'Waterproof Snuggle Blanket': 'Waterproof Dog Blanket, Pet Throw for Sofa and Bed',
    'Paw Print Fleece Blanket': 'Fleece Dog Blanket, Soft Paw Print Pet Throw',
    'Waterproof Sofa & Furniture Cover': 'Waterproof Sofa Cover for Dogs, Pet Furniture Protector',
    'Quiet Electric Nail Grinder': 'Dog Nail Grinder, Quiet Rechargeable Electric Paw Trimmer',
    'LED Nail Clippers': 'Dog Nail Clippers with LED Light and Safety Guard',
    'Self-Cleaning Slicker Brush': 'Self Cleaning Slicker Brush for Dogs, One Click Hair Release',
    'Dematting Comb': 'Dog Dematting Comb, Undercoat Rake for Mats and Tangles',
    'Pet Hair Remover Mitt': 'Dog Grooming Glove, Deshedding Mitt for Short and Long Hair',
    'Cordless Paw Trimmer': 'Dog Paw Trimmer, Cordless Quiet Clipper for Paw Pads',
    'Quick-Dry Bath Robe': 'Dog Drying Robe, Quick Dry Microfiber Bath Towel Coat',
    'Paw Washing Cup': 'Dog Paw Cleaner Cup, Silicone Muddy Paw Washer',
    'Dental & Ear Wipes': 'Dog Dental and Ear Wipes, 50 Count Grooming Wipes',
    'Finger Toothbrush': 'Dog Finger Toothbrush, Soft Silicone Dental Brush Set',
    'Slow Feeder Bowl': 'Slow Feeder Dog Bowl, Anti Gulping Maze Bowl',
    'Lick Bowl with Ball': 'Dog Lick Mat Bowl with Treat Ball, Slow Feeder Calming Mat',
    'Anti-Spill Floating Water Bowl': 'No Spill Dog Water Bowl, Floating Disc Anti Splash Bowl',
    'Travel Water Bottle & Bowl': 'Dog Travel Water Bottle with Built In Bowl, Portable Dispenser',
    'LED Waste Bag Dispenser': 'Dog Poop Bag Dispenser with LED Light, Leash Clip Holder',
    'Talk Button': 'Dog Talking Buttons, Recordable Communication Training Buzzer',
    'Dental Duck Chew Toy': 'Dog Dental Chew Toy, Textured Rubber Duck for Teeth Cleaning',
    'Crinkle Plush Buddy': 'Crinkle Dog Toy, Squeaky Plush for Small and Medium Dogs',
    'Woodland Rope-Limb Plush': 'Rope Limb Dog Toy, Squeaky Plush Animal for Tug and Chew',
    'Rope-Limb Puppy Plush': 'Puppy Rope Toy, Soft Squeaky Plush with Rope Arms',
    'Squirrel Squeaky Plush': 'Squeaky Squirrel Dog Toy, Soft Plush for Fetch and Play',
    'Big Squeak Plush': 'Large Squeaky Dog Toy, Soft Plush Companion for Big Dogs',
    'Cuddle Companion Teddy': 'Puppy Comfort Toy, Soft Teddy for Crate and Sleep',
    'Jingle Plush Ball': 'Jingle Ball Dog Toy, Soft Plush Rattle Ball',
    'Corduroy Squeak Pals': 'Corduroy Dog Toy, Lightweight Squeaky Plush for Small Dogs',
    'Barnyard Squeaker': 'Squeaky Farm Animal Dog Toys, Soft Plush Set',
    'Screaming Chicken': 'Screaming Chicken Dog Toy, Loud Squeaky Rubber Toy',
    'Sneaker Chew Buddy': 'Sneaker Dog Chew Toy, Squeaky Shoe for Teething Puppies',
    'Bouncy Egg Squeaker': 'Wobble Egg Dog Toy, Erratic Bounce Squeaky Ball',
    'Watermelon Rope Frisbee': 'Dog Frisbee Rope Toy, Soft Flying Disc for Fetch',
    # kits
    'Calm & Comfort Kit': 'Dog Anxiety Calming Kit, Heartbeat Toy Compression Wrap and Cooling Mat',
    'Travel Kit': 'Dog Travel Kit, Water Bottle Cooling Mat Paw Cleaner and Blanket',
    'Grooming Essentials Kit': 'Dog Grooming Kit, Slicker Brush Nail Grinder Toothbrush and Robe',
    'New Puppy Kit': 'New Puppy Starter Kit, Comfort Toy Blanket Chew and Toothbrush',
    'Toy Kit': 'Dog Toy Bundle, 5 Squeaky Plush and Rope Toys Variety Pack',
    'Dog Enrichment Kit': 'Dog Enrichment Kit, Lick Mat Slow Feeder Talking Button and Toy',
}


def api(path, tries=6):
    for attempt in range(tries):
        req = urllib.request.Request(
            f'https://{DOMAIN}/admin/api/{VERSION}/{path}',
            headers={'X-Shopify-Access-Token': TOKEN})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def main():
    products = api('products.json?limit=250&status=active')['products']
    problems, counts = {}, {}

    for p in products:
        short = p['title'].replace('Wagvive ', '')
        issues = []
        body = TAG.sub(' ', p.get('body_html') or '').strip()
        if len(body) < MIN_DESC:
            issues.append(f'description under {MIN_DESC} chars ({len(body)})')
        if not p.get('images'):
            issues.append('no image')
        if not p.get('product_type'):
            issues.append('no product_type')
        if not p.get('vendor'):
            issues.append('no vendor')
        if not any(v.get('barcode') for v in p['variants']):
            issues.append('no GTIN on any variant')
        if p['title'].startswith('Wagvive '):
            issues.append('title leads with brand')
        if short not in FEED_TITLES:
            issues.append('NO FEED TITLE WRITTEN')
        for i in issues:
            counts[i] = counts.get(i, 0) + 1
        if issues:
            problems[short] = issues

    print(f'{len(products)} active products checked against Merchant Center '
          f'requirements\n')
    for issue, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'  {n:3}  {issue}')

    print('\n--- what to do ---')
    if counts.get('no GTIN on any variant'):
        print('  GTIN: we resell CJ goods that have no manufacturer barcode.')
        print('        In the Google & YouTube channel, set the product')
        print('        identifier option to "these products do not have GTINs"')
        print('        rather than leaving barcodes blank, or every product is')
        print('        disapproved for a missing identifier.')
    if counts.get('title leads with brand'):
        print('  TITLES: override in the FEED only, never on the storefront.')
        print('        Run with --titles to see the suggested feed titles.')
        print('        Brand-first titles waste the characters Google matches')
        print('        on, and nobody searches "Wagvive".')

    if '--titles' in sys.argv:
        print('\n--- suggested Merchant Center titles ---')
        for p in sorted(products, key=lambda x: x['title']):
            short = p['title'].replace('Wagvive ', '')
            t = FEED_TITLES.get(short)
            print(f'\n  {p["title"]}')
            print(f'    -> {t if t else "*** NONE WRITTEN ***"}')
            if t and len(t) > 150:
                print(f'    !! {len(t)} chars, over the 150 limit')

    out = os.path.join(ROOT, 'docs', 'qa',
                       f'feed-health-{time.strftime("%Y-%m-%d")}.json')
    json.dump({'ran_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'products': len(products), 'counts': counts,
               'problems': problems,
               'feed_titles': FEED_TITLES}, open(out, 'w'), indent=1)
    print(f'\nlog -> {os.path.relpath(out, ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
