"""Download a Drive file (Google Docs/Sheets/Slides exported to PDF).

Usage: python3 download.py FILE_ID OUT_DIR
Env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
Prints the saved path.
"""
import json, os, sys, urllib.request, urllib.parse

d = urllib.parse.urlencode({'client_id': os.environ['GOOGLE_CLIENT_ID'], 'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
    'refresh_token': os.environ['GOOGLE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode()
H = {'Authorization': 'Bearer ' + json.load(urllib.request.urlopen('https://accounts.google.com/o/oauth2/token', d, timeout=30))['access_token']}
fid, out = sys.argv[1], sys.argv[2]
api = 'https://www.googleapis.com/drive/v3/files/' + fid
meta = json.load(urllib.request.urlopen(urllib.request.Request(api + '?fields=name,mimeType', headers=H), timeout=60))
name = meta['name']
if meta['mimeType'].startswith('application/vnd.google-apps.'):
    url = api + '/export?mimeType=application/pdf'
    name += '.pdf'
else:
    url = api + '?alt=media'
os.makedirs(out, exist_ok=True)
path = os.path.join(out, name.replace('/', '_'))
open(path, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=300).read())
print(path)
