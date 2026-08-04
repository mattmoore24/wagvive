#!/usr/bin/env python3
"""
Minimal CJ Dropshipping API 2.0 client.

The auth endpoint is rate limited to one call per 300 seconds, so the access
token is cached on disk and reused until it is close to expiring. Import this
module rather than re-authenticating ad hoc.

CLI:
    python config/cj_api.py auth                  # show token status
    python config/cj_api.py product <productSku>  # product + variant dump
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENVF = os.path.join(ROOT, 'config', 'cj.env')
CACHE = os.path.join(ROOT, 'config', 'cj_token.json')


def env():
    e = {}
    with open(ENVF, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and '=' in line:
                k, v = line.split('=', 1)
                e[k] = v
    return e


E = env()
BASE = E['CJ_API_BASE']


def _post(path, payload, headers=None):
    req = urllib.request.Request(
        f'{BASE}{path}', data=json.dumps(payload).encode(), method='POST',
        headers={'Content-Type': 'application/json', **(headers or {})})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _get(path, params, headers=None):
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(f'{BASE}{path}?{q}', headers=headers or {})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _cached():
    if not os.path.exists(CACHE):
        return None
    with open(CACHE, encoding='utf-8') as fh:
        c = json.load(fh)
    # keep a 10 minute safety margin
    if c.get('expires_epoch', 0) - 600 > time.time():
        return c['accessToken']
    return None


def token(force=False):
    if not force:
        t = _cached()
        if t:
            return t
    res = _post('/authentication/getAccessToken',
                {'email': E['CJ_EMAIL'], 'password': E['CJ_API_KEY']})
    if not res.get('result') or 'data' not in res:
        raise RuntimeError(f"auth failed: {json.dumps(res)[:300]}")
    d = res['data']
    exp = d.get('accessTokenExpiryDate')
    epoch = time.time() + 6 * 24 * 3600
    if exp:
        for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try:
                dt = datetime.strptime(exp, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                epoch = dt.timestamp()
                break
            except ValueError:
                continue
    with open(CACHE, 'w', encoding='utf-8') as fh:
        json.dump({'accessToken': d['accessToken'], 'expires_epoch': epoch,
                   'expiry_raw': exp, 'obtained': datetime.now(timezone.utc).isoformat()}, fh)
    return d['accessToken']


_last_call = [0.0]
MIN_INTERVAL = 1.3       # CJ enforces 1 request/second
MAX_RETRIES = 4


def call(path, params=None, payload=None):
    """GET when params given, POST when payload given.

    CJ caps throughput at one request per second and answers 429 past that, so
    space calls out and back off rather than losing the response.
    """
    h = {'CJ-Access-Token': token()}
    for attempt in range(MAX_RETRIES):
        gap = time.time() - _last_call[0]
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap)
        _last_call[0] = time.time()
        try:
            return _post(path, payload, h) if payload is not None else _get(path, params or {}, h)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return {'httpError': exc.code, 'body': exc.read().decode()[:400]}
    return {'httpError': 429, 'body': 'retries exhausted'}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == 'auth':
        t = token()
        with open(CACHE, encoding='utf-8') as fh:
            c = json.load(fh)
        left = (c['expires_epoch'] - time.time()) / 3600
        print(f'token ok  prefix={t[:8]}...  len={len(t)}')
        print(f'expires   {c.get("expiry_raw")}  (~{left:.1f}h left)')
        return

    if cmd == 'product':
        sku = sys.argv[2]
        res = call('/product/query', {'productSku': sku})
        if not res.get('data'):
            print('no data:', json.dumps(res)[:400]); return
        d = res['data']
        name = str(d.get('productNameEn') or '')[:70]
        print(f'{sku}  {name.encode("ascii","replace").decode()}')
        print(f'  pid={d.get("pid")}  type={d.get("productType")}  weight={d.get("productWeight")}')
        variants = d.get('variants') or []
        print(f'  variants={len(variants)}')
        for v in variants:
            key = str(v.get('variantKey') or '').replace('\n', ' ')[:34]
            print('    %-34s vid=%-34s sku=%-24s $%-7s wt=%s' % (
                key.encode('ascii', 'replace').decode(), v.get('vid'),
                v.get('variantSku'), v.get('variantSellPrice'), v.get('variantWeight')))
        return

    print(__doc__)


if __name__ == '__main__':
    main()
