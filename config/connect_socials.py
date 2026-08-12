#!/usr/bin/env python3
"""Point the site at Wagvive's real social profiles, everywhere that matters.

THE PLACEHOLDER TRAP, AGAIN. Horizon shipped the footer's social-links block
with generic URLs (facebook.com, instagram.com, youtube.com, tiktok.com, x.com),
and those icons were LIVE: five icons in the footer all linking to platform
homepages rather than any Wagvive profile. Exactly like the placeholder product
cards, it looks configured while pointing at nothing. This replaces the block's
settings with only the profiles that actually exist, so no icon ever links to a
platform homepage.

Three writes, all idempotent:

  1. footer social block  -> Instagram + Pinterest only. A placeholder icon is
     worse than a missing one.
  2. Organization JSON-LD -> `sameAs` in snippets/meta-tags.liquid, homepage
     only. This is the machine-readable association between wagvive.com and its
     profiles, which is what search engines actually use.
  3. Pinterest claim tag  -> `--claim <value>` inserts
     <meta name="p:domain_verify" content="<value>">. The value comes from
     Pinterest (Settings -> Claimed accounts -> Claim -> HTML tag) and CANNOT be
     invented here. Claiming attributes every pin saved from wagvive.com to the
     account and unlocks Rich Pins.

    python config/connect_socials.py            # report
    python config/connect_socials.py --apply
    python config/connect_socials.py --apply --claim abc123...
"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(ROOT, 'config', 'theme-backup')

INSTAGRAM = 'https://www.instagram.com/wagvive/'
PINTEREST = 'https://www.pinterest.com/wagvive/'

JSONLD_MARK = 'wv-social-jsonld'
CLAIM_MARK = 'wv-pinterest-claim'

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


def api(method, path, payload=None, tries=6):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    for a in range(tries):
        req = urllib.request.Request(url, data=data, method=method, headers={
            'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                b = r.read().decode()
            time.sleep(0.55)
            return json.loads(b) if b.strip() else {}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 409) and a < tries - 1:
                time.sleep(2 ** a)
                continue
            raise
    return {}


def get_asset(tid, key):
    q = urllib.parse.quote(key)
    return api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset'].get('value') or ''


def put_asset(tid, key, value):
    api('PUT', f'themes/{tid}/assets.json', {'asset': {'key': key, 'value': value}})
    # Two traps in one readback. The assets GET is eventually consistent, so
    # poll rather than fail on the first read. And Shopify RE-SERIALIZES .json
    # assets on write, so byte comparison reports a successful write as failed;
    # compare parsed JSON for .json keys, bytes only for liquid.
    q = urllib.parse.quote(key)
    for a in range(8):
        back = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset'].get('value') or ''
        if key.endswith('.json'):
            try:
                if json.loads(back) == json.loads(value):
                    return
            except ValueError:
                pass
        elif back == value:
            return
        time.sleep(1.5 * (a + 1))
    raise SystemExit(f'{key}: write did not stick')


def backup(key, value):
    os.makedirs(BACKUP, exist_ok=True)
    with open(os.path.join(BACKUP, key.replace('/', '__')), 'w', encoding='utf-8') as fh:
        fh.write(value)


def main():
    apply = '--apply' in sys.argv
    claim = None
    if '--claim' in sys.argv:
        claim = sys.argv[sys.argv.index('--claim') + 1].strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{6,64}', claim):
            print(f'--claim value looks wrong: {claim!r}. Expected the content= '
                  f'value of the p:domain_verify meta tag from Pinterest.')
            return 2

    tid = next(t for t in api('GET', 'themes.json')['themes']
               if t['role'] == 'main')['id']

    # ---- 1. footer social block ---------------------------------------------
    key = 'sections/footer-group.json'
    raw = get_asset(tid, key)
    data = json.loads(raw)
    fixed = []

    def walk(d):
        if isinstance(d, dict):
            if d.get('type') == 'social-links':
                fixed.append(d)
            for v in d.values():
                walk(v)
    walk(data)

    print(f'footer: {len(fixed)} social-links block(s)')
    for b in fixed:
        cur = {k: v for k, v in b['settings'].items() if k.endswith('_url') and v}
        keep = {k: v for k, v in b['settings'].items() if not k.endswith('_url')}
        want = dict(keep, instagram_url=INSTAGRAM, pinterest_url=PINTEREST)
        placeholders = [f'{k}={v}' for k, v in cur.items()
                        if v.rstrip('/') in ('https://www.facebook.com',
                                             'https://www.instagram.com',
                                             'https://www.youtube.com',
                                             'https://www.tiktok.com',
                                             'https://x.com')]
        print(f'   now : {cur}')
        if placeholders:
            print(f'   !! {len(placeholders)} PLACEHOLDER link(s) live: {placeholders}')
        print(f'   want: instagram + pinterest only')
        if apply and b['settings'] != want:
            b['settings'] = want

    # ---- 2. Organization sameAs JSON-LD -------------------------------------
    key2 = 'snippets/meta-tags.liquid'
    meta = get_asset(tid, key2)
    jsonld = (
        '\n{%- comment -%}' + JSONLD_MARK + '{%- endcomment -%}\n'
        "{%- if request.page_type == 'index' -%}\n"
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "Organization",\n'
        '  "name": "Wagvive",\n'
        '  "url": "https://wagvive.com",\n'
        '  "sameAs": [\n'
        f'    "{INSTAGRAM}",\n'
        f'    "{PINTEREST}"\n'
        '  ]\n'
        '}\n'
        '</script>\n'
        '{%- endif -%}\n')
    has_jsonld = JSONLD_MARK in meta
    print(f'\nmeta-tags: sameAs JSON-LD {"already present" if has_jsonld else "to add"}')

    # ---- 3. Pinterest claim tag ----------------------------------------------
    has_claim = CLAIM_MARK in meta
    if claim:
        print(f'claim tag: {"already present" if has_claim else "to add"}')
    else:
        print('claim tag: no --claim value given'
              + (' (already present)' if has_claim else
                 ' - get it from Pinterest Settings > Claimed accounts'))

    if not apply:
        print('\nDry run. Use --apply to write.')
        return 0

    backup(key, raw)
    put_asset(tid, key, json.dumps(data, indent=2))
    print('\nfooter written')

    new_meta = meta
    if not has_jsonld:
        new_meta = new_meta + jsonld
    if claim and not has_claim:
        new_meta = ('{%- comment -%}' + CLAIM_MARK + '{%- endcomment -%}\n'
                    f'<meta name="p:domain_verify" content="{claim}">\n'
                    + new_meta)
    if new_meta != meta:
        backup(key2, meta)
        put_asset(tid, key2, new_meta)
        print('meta-tags written')

    # ---- verify on the LIVE storefront ---------------------------------------
    print('\nverifying live (CDN can serve stale renders, so retrying)...')
    checks = {
        'instagram profile link': f'href="{INSTAGRAM}"',
        'pinterest profile link': f'href="{PINTEREST}"',
        'sameAs JSON-LD': '"sameAs"',
        'no placeholder facebook link': ('https://www.facebook.com/"', False),
        'no placeholder youtube link': ('https://www.youtube.com/"', False),
        'no placeholder tiktok link': ('https://www.tiktok.com/"', False),
        'no placeholder x link': ('https://x.com/"', False),
    }
    if claim:
        checks['pinterest claim tag'] = f'content="{claim}"'

    ok_all = False
    for attempt in range(8):
        u = f'https://wagvive.com/?nocache={int(time.time()*1000)}'
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            src = r.read().decode('utf-8', 'replace')
        results = {}
        for name, spec in checks.items():
            needle, want = spec if isinstance(spec, tuple) else (spec, True)
            results[name] = (needle in src) == want
        if all(results.values()):
            ok_all = True
            break
        time.sleep(4 * (attempt + 1))
    for name in checks:
        print(f"  {'OK ' if results[name] else 'BAD'} {name}")
    if not ok_all:
        return 1
    print('\nconnected and verified live')
    if not claim:
        print('\nREMAINING: the Pinterest claim tag. In Pinterest: Settings >'
              '\nClaimed accounts > Claim > "Add HTML tag", copy the content'
              '\nvalue, then re-run:'
              '\n  python config/connect_socials.py --apply --claim <value>'
              '\nthen finish the Claim flow in Pinterest so it re-checks the site.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:400], file=sys.stderr)
        sys.exit(1)
