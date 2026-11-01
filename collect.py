"""Collect Classroom data for the daily brief.

Usage: python3 collect.py DAYS > data.json
Env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
"""
import json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

d = urllib.parse.urlencode({'client_id': os.environ['GOOGLE_CLIENT_ID'], 'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
    'refresh_token': os.environ['GOOGLE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode()
H = {'Authorization': 'Bearer ' + json.load(urllib.request.urlopen('https://accounts.google.com/o/oauth2/token', d, timeout=30))['access_token']}


def get(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))
    except urllib.error.HTTPError as e:
        return {'_error': e.code}


def lst(path, key, **q):
    out, page = [], None
    while True:
        if page:
            q['pageToken'] = page
        r = get('https://classroom.googleapis.com/v1/' + path + '?' + urllib.parse.urlencode(q))
        out += r.get(key, [])
        page = r.get('nextPageToken')
        if not page:
            return out


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def files(x):
    out = []
    for m in x.get('materials', []):
        if 'driveFile' in m:
            f = m['driveFile']['driveFile']
            r = get(f"https://www.googleapis.com/drive/v3/files/{f['id']}/comments?fields=comments(author/displayName,content,createdTime,replies(author/displayName,content))&pageSize=100")
            out.append({'type': 'file', 'id': f['id'], 'title': f.get('title'), 'comments': r.get('comments', [])})
        elif 'link' in m:
            out.append({'type': 'link', 'url': m['link'].get('url'), 'title': m['link'].get('title')})
        elif 'form' in m:
            out.append({'type': 'form', 'url': m['form'].get('formUrl'), 'title': m['form'].get('title')})
        elif 'youtubeVideo' in m:
            out.append({'type': 'video', 'url': m['youtubeVideo'].get('alternateLink'), 'title': m['youtubeVideo'].get('title')})
    return out


now = datetime.now(timezone.utc)
since = now - timedelta(days=int(sys.argv[1]))
pending_since = now - timedelta(days=60)
result = {'generated': now.isoformat(), 'since': since.isoformat(), 'courses': []}

for co in lst('courses', 'courses', courseStates='ACTIVE', pageSize=100):
    cid = co['id']
    course = {'name': co['name'], 'id': cid, 'updates': [], 'pending': []}
    for kind, path, key in [('work', f'courses/{cid}/courseWork', 'courseWork'),
                            ('announcement', f'courses/{cid}/announcements', 'announcements'),
                            ('material', f'courses/{cid}/courseWorkMaterials', 'courseWorkMaterial')]:
        for x in lst(path, key, pageSize=50, orderBy='updateTime desc'):
            recent = ts(x['updateTime']) >= since
            if kind != 'work' and not recent:
                break
            if kind == 'work' and ts(x['updateTime']) < pending_since:
                break
            it = {'kind': kind, 'title': x.get('title', ''), 'text': x.get('description') or x.get('text', ''),
                  'by_teacher': x.get('creatorUserId') == co.get('ownerId'),
                  'created': x['creationTime'], 'updated': x['updateTime'], 'link': x.get('alternateLink'),
                  'due': x.get('dueDate'), 'dueTime': x.get('dueTime'), 'workType': x.get('workType')}
            if kind == 'work':
                subs = lst(f'courses/{cid}/courseWork/{x["id"]}/studentSubmissions', 'studentSubmissions')
                if subs:
                    s = subs[0]
                    it.update(state=s.get('state'), late=s.get('late'), grade=s.get('assignedGrade'), maxPoints=x.get('maxPoints'))
                if it.get('state') in ('NEW', 'CREATED', 'RECLAIMED_BY_STUDENT'):
                    course['pending'].append(dict(it, files=files(x)))
            if recent:
                course['updates'].append(dict(it, files=files(x)))
    if course['updates'] or course['pending']:
        result['courses'].append(course)

json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
