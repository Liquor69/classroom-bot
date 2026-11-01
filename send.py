"""Send a text message or a file to the Telegram chat.

Usage: python3 send.py text FILE_WITH_TEXT
       python3 send.py file PATH [CAPTION]
Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""
import json, os, sys, uuid, urllib.request, urllib.parse

api = 'https://api.telegram.org/bot' + os.environ['TELEGRAM_BOT_TOKEN'] + '/'
chat = os.environ['TELEGRAM_CHAT_ID']

if sys.argv[1] == 'text':
    text = open(sys.argv[2], encoding='utf-8').read()
    parts, cur = [], ''
    for p in text.split('\n\n'):
        if cur and len(cur) + len(p) + 2 > 4000:
            parts.append(cur)
            cur = p
        else:
            cur = cur + '\n\n' + p if cur else p
    parts.append(cur)
    for p in parts:
        r = json.load(urllib.request.urlopen(api + 'sendMessage', urllib.parse.urlencode({'chat_id': chat, 'text': p}).encode(), timeout=60))
        print(r['ok'])
else:
    path = sys.argv[2]
    caption = sys.argv[3] if len(sys.argv) > 3 else ''
    b = uuid.uuid4().hex
    body = b''
    for k, v in (('chat_id', chat), ('caption', caption)):
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    fn = os.path.basename(path)
    body += f'--{b}\r\nContent-Disposition: form-data; name="document"; filename="{fn}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
    body += open(path, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request(api + 'sendDocument', body, {'Content-Type': f'multipart/form-data; boundary={b}'})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    print(r['ok'])
