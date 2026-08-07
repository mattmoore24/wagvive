#!/usr/bin/env python3
"""Upload ONE theme snippet from config/theme-work, backing up what it replaces.

deploy_cro2.py uploads several files and rewrites template JSON. When only one
snippet has changed, running it risks pushing a stale copy of the others over
whatever is live. This does exactly one file and re-reads it afterwards to prove
the write landed, because a 200 from the assets endpoint is not proof.

    python config/deploy_snippet.py kit-callout
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'config', 'theme-work')
BACKUP = os.path.join(ROOT, 'config', 'theme-backup')

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


def api(method, path, payload=None):
    url = f'https://{DOMAIN}/admin/api/{VERSION}/{path}'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode()
        return json.loads(body) if body.strip() else {}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    key = f'snippets/{name}.liquid'

    with open(os.path.join(WORK, f'snippets__{name}.liquid'), encoding='utf-8') as fh:
        new = fh.read()

    tid = next(t for t in api('GET', 'themes.json')['themes']
               if t['role'] == 'main')['id']

    q = urllib.parse.quote(key)
    live = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset'].get('value') or ''
    if live == new:
        print(f'{key} already matches theme-work, nothing to do')
        return 0

    os.makedirs(BACKUP, exist_ok=True)
    bpath = os.path.join(BACKUP, key.replace('/', '__'))
    with open(bpath, 'w', encoding='utf-8') as fh:
        fh.write(live)
    print(f'backed up {len(live)} chars -> {os.path.relpath(bpath, ROOT)}')

    api('PUT', f'themes/{tid}/assets.json', {'asset': {'key': key, 'value': new}})

    # The assets endpoint is eventually consistent: a GET issued straight after a
    # PUT can still hand back the pre-write body. Reading once and failing on it
    # reports a successful upload as broken, so poll before believing the miss.
    for attempt in range(8):
        back = api('GET', f'themes/{tid}/assets.json?asset[key]={q}')['asset'].get('value') or ''
        if back == new:
            print(f'{key} uploaded and verified ({len(new)} chars, '
                  f'{attempt + 1} read(s))')
            return 0
        time.sleep(1.5 * (attempt + 1))
    print(f'VERIFY FAILED: theme still holds {len(back)} chars, sent {len(new)}')
    return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print('HTTP', exc.code, exc.read().decode()[:600], file=sys.stderr)
        sys.exit(1)
