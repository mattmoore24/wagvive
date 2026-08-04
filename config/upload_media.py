#!/usr/bin/env python3
"""Upload the refresh media (hero videos + band/tile photos) to Shopify Files.

Staged uploads: stagedUploadsCreate gives a signed POST target, the bytes go
there as multipart, then fileCreate registers the staged resource. Videos are
transcoded by Shopify after creation, so poll until READY before using them.

Results land in config/media_ids.json as {local name: {id, url}} so the
template edits can reference them without re-querying.
"""
import json, mimetypes, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK = os.path.join(ROOT, 'config', 'branding', 'stock')

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

FILES = [
    'hero-desktop-9898282.mp4',
    'hero-mobile-19824572.mp4',
    'tile-toys-14084426.jpg',
    'tile-grooming-8498861.jpg',
    'tile-comfort-33119363.jpg',
    'tile-kits-7055930.jpg',
    'band-puppy-12538668.jpg',
    'band-story-6589017.jpg',
]

STAGE = """
mutation($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets { url resourceUrl parameters { name value } }
    userErrors { field message }
  }
}
"""
CREATE = """
mutation($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files { id fileStatus alt }
    userErrors { field message }
  }
}
"""
STATUS = """
query($id: ID!) {
  node(id: $id) {
    ... on Video { id fileStatus filename sources { url format width } }
    ... on MediaImage { id fileStatus image { url width height } }
  }
}
"""


def gql(query, variables=None):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(
        f'https://{DOMAIN}/admin/api/{VERSION}/graphql.json', data=body, method='POST',
        headers={'X-Shopify-Access-Token': TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def multipart_post(url, params, path, mime):
    boundary = uuid.uuid4().hex
    parts = []
    for p in params:
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                     f'name="{p["name"]}"\r\n\r\n{p["value"]}\r\n'.encode())
    with open(path, 'rb') as fh:
        blob = fh.read()
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                 f'filename="{os.path.basename(path)}"\r\n'
                 f'Content-Type: {mime}\r\n\r\n'.encode())
    body = b''.join(parts) + blob + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=600) as r:
        r.read()


def main():
    out_path = os.path.join(ROOT, 'config', 'media_ids.json')
    out = {}
    if os.path.exists(out_path):
        with open(out_path, encoding='utf-8') as fh:
            out = json.load(fh)

    for name in FILES:
        if name in out:
            print(f'{name:32} already uploaded, skipped')
            continue
        path = os.path.join(STOCK, name)
        size = os.path.getsize(path)
        mime = mimetypes.guess_type(name)[0]
        is_video = mime.startswith('video')
        stage_in = [{'resource': 'VIDEO' if is_video else 'IMAGE',
                     'filename': name, 'mimeType': mime,
                     'fileSize': str(size), 'httpMethod': 'POST'}]
        res = gql(STAGE, {'input': stage_in})['data']['stagedUploadsCreate']
        if res['userErrors']:
            print(name, 'stage error', res['userErrors']); sys.exit(1)
        tgt = res['stagedTargets'][0]
        multipart_post(tgt['url'], tgt['parameters'], path, mime)

        res = gql(CREATE, {'files': [{
            'originalSource': tgt['resourceUrl'],
            'contentType': 'VIDEO' if is_video else 'IMAGE',
            'alt': name.rsplit('.', 1)[0].replace('-', ' '),
        }]})['data']['fileCreate']
        if res['userErrors']:
            print(name, 'create error', res['userErrors']); sys.exit(1)
        fid = res['files'][0]['id']
        print(f'{name:32} -> {fid}')
        out[name] = {'id': fid}
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(out, fh, indent=1)

    # wait for processing so the theme never points at a half-baked file
    for name, rec in out.items():
        for _ in range(60):
            node = gql(STATUS, {'id': rec['id']})['data']['node']
            st = node.get('fileStatus')
            if st == 'READY':
                if 'sources' in node:
                    rec['filename'] = node.get('filename')
                    src = sorted((s for s in node['sources'] if s['format'] == 'mp4'),
                                 key=lambda s: -(s['width'] or 0))
                    rec['url'] = src[0]['url'] if src else None
                else:
                    rec['url'] = node['image']['url']
                print(f'{name:32} READY')
                break
            if st == 'FAILED':
                print(f'{name:32} FAILED'); break
            time.sleep(5)
        else:
            print(f'{name:32} still processing after 5 min')
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)


if __name__ == '__main__':
    main()
