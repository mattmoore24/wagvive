#!/usr/bin/env python3
"""One place that builds tracked links, so attribution is not guesswork later.

Inconsistent UTMs are the most common reason a small store cannot tell which
channel paid for itself. "facebook" / "Facebook" / "fb" / "meta" become four
channels in GA4, each too small to read, and the conclusion is drawn from
whichever one happened to be biggest. Fixing it retroactively is impossible
because the data was never collected correctly.

Convention, fixed:

    utm_source    the platform, lowercase, from SOURCES below. No synonyms.
    utm_medium    what kind of traffic: cpc, organic_social, email, referral
    utm_campaign  <phase>_<offer>          e.g. p1_calm_comfort_kit
    utm_content   the creative variant      e.g. video_storm_a
    utm_term      audience or keyword       optional

Campaign names carry the PHASE from the marketing plan so a report can be read
against the plan without a lookup table.

    python config/marketing/utm.py pinterest cpc p1_calm_comfort_kit \\
        --url /products/calm-comfort-kit --content video_storm_a
    python config/marketing/utm.py --list
"""
import sys, urllib.parse

BASE = 'https://wagvive.com'

# The only permitted values. If a platform is missing, add it here rather than
# inventing a spelling at the point of use.
SOURCES = {
    'pinterest': 'Pinterest',
    'meta': 'Facebook and Instagram ads (never "facebook" or "fb")',
    'google': 'Google Ads and Merchant Center',
    'tiktok': 'TikTok organic and ads (NOT TikTok Shop, see the plan)',
    'instagram': 'Instagram organic posts and bio link',
    'email': 'Shopify email flows and campaigns',
    'creator': 'Seeded creators and affiliates',
    'reddit': 'Reddit posts and comments',
    'youtube': 'YouTube organic',
}
MEDIUMS = {
    'cpc': 'paid click',
    'organic_social': 'unpaid post',
    'email': 'owned email',
    'referral': 'creator, partner or press link',
    'affiliate': 'commissioned creator link',
}
# Offers worth advertising. Singles are absent on purpose: see the plan,
# section 1. Advertising a single product cannot break even.
OFFERS = {
    'calm_comfort_kit': '/products/calm-comfort-kit',
    'travel_kit': '/products/travel-kit',
    'new_puppy_kit': '/products/new-puppy-kit',
    'grooming_essentials_kit': '/products/grooming-essentials-kit',
    'toy_kit': '/products/toy-kit',
    'dog_enrichment_kit': '/products/dog-enrichment-kit',
    'all_kits': '/collections/bundles-kits',
}


def build(source, medium, campaign, url='/', content=None, term=None):
    if source not in SOURCES:
        raise SystemExit(f'unknown source {source!r}. Allowed: '
                         f'{", ".join(sorted(SOURCES))}')
    if medium not in MEDIUMS:
        raise SystemExit(f'unknown medium {medium!r}. Allowed: '
                         f'{", ".join(sorted(MEDIUMS))}')
    params = {'utm_source': source, 'utm_medium': medium,
              'utm_campaign': campaign}
    if content:
        params['utm_content'] = content
    if term:
        params['utm_term'] = term
    if not url.startswith('http'):
        url = BASE + ('' if url.startswith('/') else '/') + url
    sep = '&' if '?' in url else '?'
    return url + sep + urllib.parse.urlencode(params)


def main():
    if '--list' in sys.argv or len(sys.argv) < 4:
        print('sources:')
        for k, v in SOURCES.items():
            print(f'  {k:14} {v}')
        print('\nmediums:')
        for k, v in MEDIUMS.items():
            print(f'  {k:14} {v}')
        print('\noffers worth advertising (singles are excluded on purpose):')
        for k, v in OFFERS.items():
            print(f'  {k:24} {v}')
        print('\nusage: utm.py <source> <medium> <campaign> '
              '[--url PATH|--offer NAME] [--content X] [--term Y]')
        return 0

    source, medium, campaign = sys.argv[1:4]
    def arg(flag, default=None):
        return (sys.argv[sys.argv.index(flag) + 1]
                if flag in sys.argv else default)
    url = arg('--url', '/')
    offer = arg('--offer')
    if offer:
        if offer not in OFFERS:
            raise SystemExit(f'unknown offer {offer!r}. Allowed: '
                             f'{", ".join(sorted(OFFERS))}')
        url = OFFERS[offer]
    print(build(source, medium, campaign, url,
                arg('--content'), arg('--term')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
