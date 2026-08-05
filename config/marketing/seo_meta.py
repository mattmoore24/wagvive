#!/usr/bin/env python3
"""Write SEO title and meta description for every product. All 42 had neither.

Found during the pre-spend audit of the Calm & Comfort Kit page and then
confirmed catalogue-wide: `seo.title` and `seo.description` are null on all 42
products, so Shopify falls back to the product title and a truncated slice of
the description.

That is survivable for paid clicks, which land on the page directly. It is not
survivable for the two FREE channels the marketing plan leads with:

  * Google free listings rank on product data quality, and the meta description
    is part of it.
  * Pinterest rich pins read the meta description directly, and Pinterest is
    the only channel affordable at our CAC ceiling on day one.

Written by hand rather than derived. A first pass generated these from the
product body plus a shipping line, and the result was titles of 14 to 25
characters against a 60 character budget and descriptions of 50 to 100 against
160. Mechanically valid, and a waste of the only free real estate we get.

Rules used, same as the feed titles in feed_health.py:
  * Describe the product the way a shopper types it. Never lead with "Wagvive";
    nobody searches for us yet.
  * Title under 60 characters, which is roughly where Google truncates.
  * Description 140 to 160 characters, specific enough to be worth a click:
    what it is, what is in it or what it does, and no adjectives doing work
    that a fact could do.
  * On-site titles are NEVER touched. This is metadata only.

    python config/marketing/seo_meta.py            # show the diff
    python config/marketing/seo_meta.py --apply    # write + verify live
"""
import json, os, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# product title without the "Wagvive " prefix -> (seo title, meta description)
SEO = {
    # --- kits: the paid-acquisition products, so these matter most ----------
    'Calm & Comfort Kit': (
        'Dog Anxiety Kit: Heartbeat Toy, Calming Wrap, Cooling Mat',
        'Five pieces for storms, fireworks and being left alone: a heartbeat '
        'plush, a compression wrap, a cooling mat, a fleece blanket and a '
        'squeak plush.'),
    'Travel Kit': (
        'Dog Travel Kit: Water Bottle, Cooling Mat, Paw Cleaner',
        'Five pieces that live by the door or in the car. Travel bottle with a '
        'built in bowl, cooling mat, paw washer, quick dry robe and a fleece '
        'blanket.'),
    'Grooming Essentials Kit': (
        'Dog Grooming Kit: Slicker Brush, Nail Grinder, Toothbrush',
        'Five tools for a full home grooming session: self cleaning slicker '
        'brush, quiet nail grinder, finger toothbrush, quick dry robe and a '
        'paw washing cup.'),
    'New Puppy Kit': (
        'New Puppy Starter Kit: Comfort Toy, Blanket and Chew',
        'Five things for the first month: a cuddle teddy for the crate, a '
        'sneaker chew for teething, a fleece blanket, a finger toothbrush and '
        'a bag dispenser.'),
    'Toy Kit': (
        'Dog Toy Bundle: 5 Squeaky Plush and Rope Toys',
        'Five toys and five different games: a barnyard squeaker, a rope '
        'frisbee, a sneaker chew, a jingle ball and a corduroy pal. Cheaper '
        'than buying four.'),
    'Dog Enrichment Kit': (
        'Dog Enrichment Kit: Lick Mat, Slow Feeder, Talk Button',
        'Four tools that turn meals and quiet time into work a dog enjoys: a '
        'talking button, a lick bowl, a slow feeder maze bowl and a bouncy egg '
        'squeaker.'),

    # --- outcome goods: anxiety, cooling, sleep -----------------------------
    'Cooling Comfort Pad': (
        'Dog Cooling Mat, Pressure Activated Gel Pad',
        'No water, no power, no freezer. Your dog lies down and the gel starts '
        'working. Four sizes for crates, beds and car seats, wipe clean.'),
    'Calming Thunder Wrap': (
        'Dog Anxiety Vest, Calming Compression Wrap',
        'Gentle, even pressure that feels like being held, for thunderstorms, '
        'fireworks and vet visits. Dimpled minky fabric, machine washable, '
        'three colors.'),
    'Heartbeat Soothing Sloth': (
        'Puppy Heartbeat Toy, Calming Sleep Aid Plush',
        'A pulsing heartbeat to sleep against, which is what settled them in '
        'the litter. For crate training, the first nights home and dogs left '
        'alone.'),
    'Waterproof Snuggle Blanket': (
        'Waterproof Dog Blanket for Sofa and Bed',
        'Soft on top, waterproof underneath, so muddy paws and accidents stop '
        'at the fabric. Machine washable, three sizes, for the sofa, the bed '
        'or the car.'),
    'Paw Print Fleece Blanket': (
        'Fleece Dog Blanket, Soft Paw Print Pet Throw',
        'Makes a crate feel like a den, and travels to the car and the vet '
        'smelling like home. Soft double sided fleece, machine washable, two '
        'sizes.'),
    'Waterproof Sofa & Furniture Cover': (
        'Waterproof Sofa Cover for Dogs, Furniture Protector',
        'Keeps hair, mud and claws off the furniture without looking like a '
        'dust sheet. Waterproof backing, non slip, machine washable, sizes to '
        'fit most seats.'),

    # --- grooming tools -----------------------------------------------------
    'Quiet Electric Nail Grinder': (
        'Dog Nail Grinder, Quiet Rechargeable Paw Trimmer',
        'No clipper crunch, which is what most dogs are actually frightened '
        'of. Low noise, low vibration, USB rechargeable, with ports for '
        'different nail sizes.'),
    'LED Nail Clippers': (
        'Dog Nail Clippers with LED Light and Safety Guard',
        'The light shows the quick so you can see where to stop, and the guard '
        'stops you going too far. Sharp stainless blades for small and medium '
        'dogs.'),
    'Self-Cleaning Slicker Brush': (
        'Self Cleaning Slicker Brush for Dogs',
        'One click and the coat lets go of the bristles, which is the part '
        'everyone hates. Bent pins reach the undercoat without scratching '
        'skin.'),
    'Dematting Comb': (
        'Dog Dematting Comb, Undercoat Rake for Tangles',
        'Serrated blades cut through mats instead of dragging them out. For '
        'double coats and the tangles behind ears and under legs.'),
    'Pet Hair Remover Mitt': (
        'Dog Grooming Glove, Deshedding Mitt',
        'For the dogs who will not tolerate a brush but will happily be '
        'stroked. Soft silicone tips lift loose hair, and it peels off the '
        'glove in one sheet.'),
    'Cordless Paw Trimmer': (
        'Dog Paw Trimmer, Cordless Quiet Clipper',
        'A slim head for the hair between paw pads, where a full size clipper '
        'cannot reach. Low noise motor, USB rechargeable, waterproof head '
        'rinses clean.'),
    'Quick-Dry Bath Robe': (
        'Dog Drying Robe, Microfiber Bath Towel Coat',
        'Ends the shake water everywhere lap of the house. Absorbent microfiber '
        'wraps and fastens, so they dry while wearing it. Three sizes, machine '
        'washable.'),
    'Paw Washing Cup': (
        'Dog Paw Cleaner Cup, Silicone Muddy Paw Washer',
        'Add water, twist, done. Soft silicone fins clean between the pads '
        'before the mud reaches the carpet. Three sizes, splash resistant '
        'lid.'),

    # --- dental -------------------------------------------------------------
    'Dental & Ear Wipes': (
        'Dog Dental and Ear Wipes, 50 Count',
        'Textured dental wipes for along the gum line, and soft ear wipes for '
        'the outer ear. A few times a week beats a perfect daily plan you '
        'never keep.'),
    'Finger Toothbrush': (
        'Dog Finger Toothbrush, Soft Silicone Set',
        'A soft sleeve over your finger gives far more control than a brush '
        'handle, and most dogs tolerate a finger better. Start early and it '
        'stays normal.'),

    # --- bowls, feeding, water ---------------------------------------------
    'Slow Feeder Bowl': (
        'Slow Feeder Dog Bowl, Anti Gulping Maze Bowl',
        'Dinner becomes a ten minute puzzle instead of a thirty second inhale. '
        'Raised maze ridges, non slip base, dishwasher safe.'),
    'Lick Bowl with Ball': (
        'Dog Lick Mat Bowl with Treat Ball',
        'Spread something tasty on the textured base and licking does what '
        'licking is for, settling them down. Suction base, dishwasher safe.'),
    'Anti-Spill Floating Water Bowl': (
        'No Spill Dog Water Bowl, Floating Disc Design',
        'A floating disc slows the water so eager drinkers stay hydrated '
        'without soaking the floor. For the house and the car, three '
        'capacities.'),
    'Travel Water Bottle & Bowl': (
        'Dog Travel Water Bottle with Built In Bowl',
        'The lid flips open into a drinking bowl, and unfinished water tips '
        'straight back inside so nothing is wasted. One handed, leak proof.'),

    # --- walk and waste -----------------------------------------------------
    'LED Waste Bag Dispenser': (
        'Dog Poop Bag Dispenser with LED Light',
        'Clips to the leash and lights the way on late walks, so you can see '
        'what you are picking up. Fits standard rolls, five colors.'),

    # --- enrichment ---------------------------------------------------------
    'Talk Button': (
        'Dog Talking Buttons, Recordable Training Buzzer',
        'Record a word and let them learn to press it. Most dogs surprise '
        'their owners inside a week. Clear sound, non slip base, four '
        'colors.'),

    # --- toys ---------------------------------------------------------------
    'Dental Duck Chew Toy': (
        'Dog Dental Chew Toy, Textured Rubber Duck',
        'Ridged latex, so chewing does something for the teeth instead of just '
        'passing time. Squeaks when bitten, for light to medium chewers.'),
    'Crinkle Plush Buddy': (
        'Crinkle Dog Toy, Squeaky Plush for Small Dogs',
        'Crinkles when squashed and squeaks when bitten, so it answers back '
        'twice. Light enough for small dogs to carry around all day.'),
    'Woodland Rope-Limb Plush': (
        'Rope Limb Dog Toy, Squeaky Plush Animal',
        'Rope arms and legs for tugging, a soft body for carrying, and a '
        'squeaker in the middle. Six woodland animals to choose from.'),
    'Rope-Limb Puppy Plush': (
        'Puppy Rope Toy, Soft Squeaky Plush',
        'Small and soft enough for a puppy mouth, with rope limbs for the '
        'tugging stage. A first toy that survives teething better than plush '
        'alone.'),
    'Squirrel Squeaky Plush': (
        'Squeaky Squirrel Dog Toy, Soft Plush for Fetch',
        'A long tail to grab and shake, and a squeaker that keeps a solo game '
        'going. Soft enough to carry, light enough to throw indoors.'),
    'Big Squeak Plush': (
        'Large Squeaky Dog Toy for Big Dogs',
        'Big enough to lean on and soft enough to sleep against, with a '
        'squeaker that survives more than one afternoon. Two colors.'),
    'Cuddle Companion Teddy': (
        'Puppy Comfort Toy, Soft Teddy for the Crate',
        'Something warm to sleep against instead of crying for the litter. '
        'Soft enough for a young mouth, and it makes a crate feel less '
        'empty.'),
    'Jingle Plush Ball': (
        'Jingle Ball Dog Toy, Soft Plush Rattle Ball',
        'Rattles when it rolls, so the game keeps going without you. Soft '
        'enough for indoors and light enough for small dogs to carry.'),
    'Corduroy Squeak Pals': (
        'Corduroy Dog Toy, Lightweight Squeaky Plush',
        'Ribbed corduroy to grip and a squeaker to answer back. Light enough '
        'for small dogs to carry around all day. Three characters.'),
    'Barnyard Squeaker': (
        'Squeaky Farm Animal Dog Toys, Soft Plush',
        'Soft plush for carrying and squeaking, in seven farm animals. Light '
        'enough for small dogs, and cheap enough to have more than one.'),
    'Screaming Chicken': (
        'Screaming Chicken Dog Toy, Loud Squeaky Rubber',
        'The loud one. Durable rubber with a scream that carries across a '
        'garden, for the dogs who lose interest in a polite squeak after two '
        'minutes.'),
    'Sneaker Chew Buddy': (
        'Sneaker Dog Chew Toy for Teething Puppies',
        'Teething happens to your shoes unless it has one of its own. Squeaky '
        'sneaker shaped chew, soft enough for puppies, three colors.'),
    'Bouncy Egg Squeaker': (
        'Wobble Egg Dog Toy, Erratic Bounce Squeaky Ball',
        'The egg shape bounces off at angles a ball never would, so solo play '
        'stays interesting for longer. Squeaks on impact, four colors, light '
        'enough for indoors.'),
    'Watermelon Rope Frisbee': (
        'Dog Frisbee Rope Toy, Soft Flying Disc',
        'Soft enough to throw indoors without breaking anything, with a rope '
        'center for tugging and chewing when the fetch is over.'),
}

SET_SEO = '''
mutation($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id seo { title description } }
    userErrors { field message }
  }
}
'''
READ = '''
{ products(first: 60, query: "status:active") {
    nodes { id title seo { title description } } } }
'''


def gql(query, variables=None, tries=5):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    for attempt in range(tries):
        req = urllib.request.Request(
            f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body,
            method='POST', headers={'X-Shopify-Access-Token': TOKEN,
                                    'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read().decode())
            if out.get('errors'):
                raise SystemExit('GraphQL: ' + json.dumps(out['errors'])[:300])
            return out
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return {}


def main():
    apply = '--apply' in sys.argv
    products = gql(READ)['data']['products']['nodes']

    plan, missing, toolong = [], [], []
    for p in products:
        short = p['title'].replace('Wagvive ', '')
        entry = SEO.get(short)
        if not entry:
            missing.append(short)
            continue
        title, desc = entry
        if len(title) > 60 or not (120 <= len(desc) <= 160):
            toolong.append((short, len(title), len(desc)))
        if p['seo']['title'] != title or p['seo']['description'] != desc:
            plan.append((p['id'], short, title, desc))

    print(f'{len(products)} active products, {len(SEO)} written, '
          f'{len(plan)} need updating\n')
    for _, short, title, desc in plan:
        print(f'  {short}')
        print(f'    title ({len(title):2}) {title}')
        print(f'    desc  ({len(desc):3}) {desc}')

    if missing:
        print(f'\nNO COPY WRITTEN for {len(missing)}: {missing}')
        return 1
    if toolong:
        print('\nOUT OF BOUNDS (title <=60, desc 120 to 160):')
        for s, t, d in toolong:
            print(f'  {s:34} title {t}, desc {d}')
        return 1

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    print(f'\nwriting {len(plan)}...')
    for pid, short, title, desc in plan:
        r = gql(SET_SEO, {'input': {'id': pid,
                                    'seo': {'title': title,
                                            'description': desc}}})
        errs = r['data']['productUpdate']['userErrors']
        if errs:
            print(f'  FAILED {short}: {json.dumps(errs)[:160]}')
            return 1
        time.sleep(0.55)
    print('done')

    # verify by re-reading, never from the mutation's return value
    fresh = gql(READ)['data']['products']['nodes']
    bad = []
    for p in fresh:
        short = p['title'].replace('Wagvive ', '')
        want = SEO.get(short)
        if not want:
            continue
        if p['seo']['title'] != want[0] or p['seo']['description'] != want[1]:
            bad.append(short)
    if bad:
        print(f'\nVERIFY FAILED on {len(bad)}: {bad}')
        return 1
    print(f'verified: all {len(fresh)} products carry the intended SEO title '
          f'and description')
    return 0


if __name__ == '__main__':
    sys.exit(main())
