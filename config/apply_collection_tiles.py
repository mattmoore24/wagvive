#!/usr/bin/env python3
"""Set each collection's tile image from approved local art.

WHY. The homepage's "Prefer to build your own?" tiles and the collection pages
render collection.image. The originals were stock photos: other brands'
products, mixed color grades, and a kits tile with no kit in it. These tiles
are house-style shots of dogs with OUR actual products, generated from the
same reference discipline as the kit covers and eyeballed before upload.

Usage:
    python config/apply_collection_tiles.py            # report
    python config/apply_collection_tiles.py --apply
Expects the approved art in config/branding/collection-tiles/<handle>.jpg.
"""
import json, mimetypes, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'config', 'branding', 'collection-tiles')

env = {}
with open(os.path.join(ROOT, 'config', 'shopify.env'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line and '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
D, T, V = (env['SHOPIFY_STORE_DOMAIN'], env['SHOPIFY_ADMIN_API_TOKEN'],
           env['SHOPIFY_API_VERSION'])

ALTS = {
    'toys-play': 'A golden retriever chewing the Wagvive sneaker toy',
    'grooming': 'A freshly bathed dog in the Wagvive hooded bath robe beside '
                'the paw washing cup and slicker brush',
    'comfort-health': 'A senior dog asleep on the Wagvive paw print fleece '
                      'with the heartbeat sloth',
    'bundles-kits': 'A puppy unboxing Wagvive kit essentials from a plain box',
    'travel-outdoor': 'A dog with the Wagvive travel water bottle and bath robe',
    'calming-enrichment': 'A dog about to press the Wagvive talk button beside '
                          'the slow feeder bowl',
}


def gql(q, variables=None):
    body = json.dumps({'query': q, 'variables': variables or {}}).encode()
    rq = urllib.request.Request(f'https://{D}/admin/api/{V}/graphql.json',
                                data=body, method='POST',
                                headers={'X-Shopify-Access-Token': T,
                                         'Content-Type': 'application/json'})
    with urllib.request.urlopen(rq, timeout=180) as r:
        out = json.loads(r.read().decode())
    if out.get('errors'):
        raise SystemExit(json.dumps(out['errors'])[:500])
    time.sleep(0.4)
    return out['data']


def staged_upload(path, fname):
    size = os.path.getsize(path)
    mime = mimetypes.guess_type(fname)[0] or 'image/jpeg'
    st = gql('''mutation($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets { url resourceUrl parameters { name value } }
        userErrors { field message } } }''',
        {'input': [{'resource': 'FILE', 'filename': fname, 'mimeType': mime,
                    'httpMethod': 'POST', 'fileSize': str(size)}]})
    tgt = st['stagedUploadsCreate']['stagedTargets'][0]
    boundary = uuid.uuid4().hex
    parts = []
    for p in tgt['parameters']:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                     f'name="{p["name"]}"\r\n\r\n{p["value"]}\r\n'.encode())
    with open(path, 'rb') as fh:
        data = fh.read()
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                 f'name="file"; filename="{fname}"\r\n'
                 f'Content-Type: {mime}\r\n\r\n'.encode() + data + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    body = b''.join(parts)
    rq = urllib.request.Request(tgt['url'], data=body, method='POST', headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))})
    with urllib.request.urlopen(rq, timeout=300) as r:
        assert r.status in (200, 201, 204)
    return tgt['resourceUrl']


def main():
    apply = '--apply' in sys.argv
    colls = gql('''{ collections(first: 30) { nodes {
        id title handle image { url } } } }''')['collections']['nodes']
    by_handle = {c['handle']: c for c in colls}

    todo = []
    for handle in ALTS:
        path = os.path.join(ART, f'{handle}.jpg')
        exists = os.path.exists(path)
        c = by_handle.get(handle)
        cur = ((c or {}).get('image') or {}).get('url', 'NO IMAGE')
        print(f"{handle:20} art={'yes' if exists else 'MISSING'}  "
              f"current={cur.split('/')[-1].split('?')[0][:48]}")
        if exists and c:
            todo.append((c, path))

    if not apply:
        print(f'\nDry run. {len(todo)} tile(s) ready. Use --apply to set.')
        return 0

    for c, path in todo:
        # collectionUpdate SILENTLY keeps the old image if one exists (no
        # userErrors, mutation "succeeds"), so clear it first. Caught by
        # re-fetching: four collections kept their stock photos on the first
        # pass while the two imageless ones updated fine.
        if c.get('image'):
            gql('''mutation($input: CollectionInput!) {
              collectionUpdate(input: $input) {
                collection { id } userErrors { field message } } }''',
                {'input': {'id': c['id'], 'image': None}})
        fname = f"tile-{c['handle']}-{int(time.time())}.jpg"
        src = staged_upload(path, fname)
        out = gql('''mutation($input: CollectionInput!) {
          collectionUpdate(input: $input) {
            collection { id image { url } }
            userErrors { field message } } }''',
            {'input': {'id': c['id'],
                       'image': {'src': src, 'altText': ALTS[c['handle']]}}})
        errs = out['collectionUpdate']['userErrors']
        img = (out['collectionUpdate']['collection'].get('image') or {}).get('url')
        print(f"  {c['handle']:20} -> {'ERR ' + str(errs) if errs else (img or '')[:70]}")

    # verify by re-fetch, and against the EXPECTED new filename, not mere
    # presence: presence-only verification is how the silent keep slipped by
    print('\nverifying...')
    fresh = gql('''{ collections(first: 30) { nodes { handle image { url } } } }'''
                )['collections']['nodes']
    ok = True
    for f in fresh:
        if f['handle'] not in ALTS:
            continue
        url = (f.get('image') or {}).get('url', '')
        fname = url.split('/')[-1].split('?')[0]
        good = fname.startswith(f"tile-{f['handle']}-")
        print(f"  {'OK ' if good else 'BAD'} {f['handle']:20} {fname[:52]}")
        ok &= good
    print('\n' + ('all tiles set to the new art' if ok
                  else 'A TILE STILL SHOWS THE OLD IMAGE'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
