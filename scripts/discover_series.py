"""Daily title discovery, with official Netflix verification and explicit source health."""
import concurrent.futures
import datetime as dt
import email.utils
import html
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TZ = dt.timezone(dt.timedelta(hours=8))
KINDS = ('台劇', '韓劇', '陸劇', '日劇', '歐美劇', '綜藝')
CATALOGUES = ('https://www.netflix.com/tw/browse/genre/434295', 'https://www.netflix.com/tw/browse/genre/83')
DISCOVERY = Path('public/series-discovery.json')


def get(url):
    if os.environ.get('WECARE_OFFLINE') == '1':
        raise OSError('Offline test')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-TW,zh;q=0.9'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode('utf-8')


def text(value):
    return html.unescape(re.sub('<[^>]+>', '', value)).strip()


def official_ids(page):
    # Read the public new-release rows plus the leading discovery row; do not
    # rescan thousands of old catalogue titles on every daily refresh.
    rows = re.split(r'data-uia="locp-collections-title-row"', page)[1:]
    if rows:
        selected = [rows[0]] + [row for row in rows if re.search(r'<h2[^>]*>[^<]*(?:最新作品|新上架|近期推出|新推出)', row)]
        page = '\n'.join(selected)
    ids = list(dict.fromkeys(re.findall(r'https://www\.netflix\.com/tw/title/(\d+)', page)))
    if not ids:
        raise ValueError('Official catalogue layout has changed or is unavailable')
    return ids


def parse_official(page, title_id, now, listed_in_taiwan=False):
    match = re.search(r'netflix.reactContext\s*=\s*({.*?});\s*</script>', page, re.S)
    if not match:
        raise ValueError('Official title metadata unavailable')
    data = json.loads(re.sub(r'\\x([0-9a-fA-F]{2})', r'\\u00\1', match.group(1)))['models']['nmTitleGQL']['data']
    meta = data['metaData']
    if str(meta['videoId']) != title_id:
        raise ValueError('Redirected to a different title')
    if meta.get('type') != 'Show' or (meta.get('isAvailable') is not True and not listed_in_taiwan):
        print('Excluded title', title_id, 'type=', meta.get('type'), 'available=', meta.get('isAvailable'), flush=True)
        return None
    genre = re.search(r'<h4[^>]*>類型</h4>\s*<span[^>]*>(.*?)</span>', page, re.S)
    genres = text(genre.group(1)) if genre else ''
    kind = next((v for k, v in [('台灣', '台劇'), ('韓國', '韓劇'), ('日本', '日劇'), ('中國', '陸劇'), ('美國', '歐美劇'), ('英國', '歐美劇'), ('加拿大', '歐美劇'), ('法國', '歐美劇'), ('德國', '歐美劇'), ('西班牙', '歐美劇')] if k in genres), None)
    if any(term in genres for term in ('實境', '綜藝', '競賽')):
        kind = '綜藝'
    release_evidence=load_release_evidence().get(title_id,{})
    if not kind and release_evidence.get('title')==data['copy']['title']:
        kind=release_evidence.get('type')
    if not kind or '動漫' in genres or '動畫' in genres:
        print('Excluded title', title_id, 'genres=', genres, flush=True)
        return None
    year_match = re.search(r'<li[^>]*>\s*(20\d{2})\s*</li>', page)
    if not year_match:
        raise ValueError('Title year missing')
    year = int(year_match.group(1))
    if year < now.year or year > now.year:
        print('Excluded title', title_id, 'year=', year, flush=True)
        return None
    title = data['copy']['title'].strip()
    synopsis = data['copy']['synopsis'].strip()
    if not title or len(synopsis) < 15:
        raise ValueError('Title description missing')
    url = 'https://www.netflix.com/tw/title/' + title_id
    return {'id': 'netflix-auto-' + title_id, 'title': title, 'type': kind, 'platform': 'Netflix',
            'cast': '、'.join(a['name'] for a in data['persons'].get('actors', [])[:5]) or '官方尚未提供',
            'description': synopsis, 'source': 'Netflix 台灣官方作品頁（自動核對）', 'url': url,
            'verified': True, 'verifiedAt': now.isoformat(timespec='seconds'), 'autoDiscovered': True,
            'releasePrecision': 'year', 'releaseWindow': str(year) + ' 年作品；確切上架日未核實',
            'releaseStatus': 'catalogue-listed', 'releaseSourceUrl': url, 'catalogueYear': year,
            'availabilityNote': 'Netflix 台灣官方公開片庫列出；實際可播放情況請開啟平台確認',
            'platformAvailabilityVerified': False}


def load_release_evidence():
    path=Path(__file__).resolve().parents[1]/'data/series-release-evidence.json'
    return json.loads(path.read_text()) if path.exists() else {}

def apply_release_evidence(item,evidence):
    if evidence and item.get('title')==evidence.get('title'):
        dt.date.fromisoformat(evidence['releaseDate'])
        return {**item,**evidence,'releasePrecision':'day','releaseStatus':'released'}
    return item


def discover(previous, now, load=get):
    stamp = now.isoformat(timespec='seconds')
    result = {'checkedAt': stamp, 'sources': [], 'verified': [], 'candidates': [], 'method': '官方片庫每日發現並逐片核對；新聞候選不等於正式上架。公開來源無法保證涵蓋所有平台全部新劇。'}
    ids = []
    for url in CATALOGUES:
        try:
            found = official_ids(load(url))
            ids.extend(found)
            result['sources'].append({'url': url, 'status': 'success', 'checkedAt': stamp, 'titleCount': len(found)})
        except Exception as exc:
            result['sources'].append({'url': url, 'status': 'error', 'checkedAt': stamp, 'error': str(exc)[:180]})
    ids = list(dict.fromkeys(ids))
    print('Official catalogue titles to check:', len(ids), flush=True)
    old = {x['id'].removeprefix('netflix-auto-'): x for x in previous.get('verified', [])}
    def verify(title_id):
        url = 'https://www.netflix.com/tw/title/' + title_id
        try:
            item=parse_official(load(url), title_id, now, listed_in_taiwan=True)
            return title_id, apply_release_evidence(item,load_release_evidence().get(title_id)) if item else None, None
        except Exception as exc:
            return title_id, None, str(exc)[:160]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for index, (title_id, item, error) in enumerate(pool.map(verify, ids), 1):
            if index % 50 == 0:
                print('Checked', index, '/', len(ids), 'titles', flush=True)
            if item:
                item['firstSeenAt'] = old.get(title_id, {}).get('firstSeenAt', stamp)
                result['verified'].append(item)
            if error:
                result['sources'].append({'url': 'https://www.netflix.com/tw/title/' + title_id, 'status': 'error', 'checkedAt': stamp, 'error': error})
    # A failed source may retain a dated, clearly identified result for up to 7 days.
    for title_id, item in old.items():
        if title_id not in ids or any(s['status'] == 'error' and (s['url'].endswith('/' + title_id) or s['url'] in CATALOGUES) for s in result['sources']):
            age = now - dt.datetime.fromisoformat(item['verifiedAt'])
            if age <= dt.timedelta(days=7) and not any(x['id'] == item['id'] for x in result['verified']):
                result['verified'].append({**item, 'verificationStale': True})
    for kind in KINDS:
        query = kind + ' (新劇 OR 新上架 OR 開播 OR 首播 OR 定檔) (Netflix OR Disney OR HBO OR 愛奇藝 OR 騰訊 OR 芒果TV) when:7d'
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl': 'zh-TW', 'gl': 'TW', 'ceid': 'TW:zh-Hant'})
        try:
            root = ET.fromstring(load(url))
            if root.tag != 'rss' or root.find('channel') is None:
                raise ValueError('News source returned an invalid feed')
            for story in root.findall('./channel/item'):
                headline = story.findtext('title') or ''
                link = story.findtext('link') or ''
                try:
                    published = email.utils.parsedate_to_datetime(story.findtext('pubDate') or '').astimezone(TZ)
                except (ValueError, TypeError):
                    continue
                if not now - dt.timedelta(days=7) <= published <= now or not link.startswith('https://'):
                    continue
                if not any(t in headline for t in ('新劇', '上架', '開播', '首播', '定檔')) or any(t in headline for t in ('重播', '回顧', '經典老劇')):
                    continue
                for title in re.findall(r'《([^》]{2,40})》', headline):
                    if any(x['title'] == title for x in result['verified'] + result['candidates']):
                        continue
                    result['candidates'].append({'title': title, 'type': kind, 'headline': headline, 'source': story.findtext('source') or '公開新聞', 'sourceUrl': link, 'publishedAt': published.isoformat(timespec='seconds'), 'status': '新聞提及，平台與上架日待核對'})
            result['sources'].append({'url': url, 'type': kind, 'status': 'success', 'checkedAt': stamp})
        except Exception as exc:
            result['sources'].append({'url': url, 'type': kind, 'status': 'error', 'checkedAt': stamp, 'error': str(exc)[:180]})
    result['lastSuccessfulAt'] = stamp if result['sources'] and all(s['status'] == 'success' for s in result['sources']) else previous.get('lastSuccessfulAt')
    result['status'] = 'success' if result['lastSuccessfulAt'] == stamp else 'partial' if any(s['status'] == 'success' for s in result['sources']) else 'failed'
    return result


def merge(feed, discovery, now, reviewed=None):
    manual = [x for x in feed.get('recommendations', []) if not x.get('autoDiscovered')]
    recent_path=Path(__file__).resolve().parents[1]/'data/series-recent-reviewed.json'
    recent=reviewed if reviewed is not None else json.loads(recent_path.read_text()) if recent_path.exists() else []
    recent_ids={x['id'] for x in recent}
    manual=[x for x in manual if x['id'] not in recent_ids]+recent
    titles = {(x['title'], x['platform']) for x in manual}
    auto = []
    for item in discovery.get('verified', []):
        age = now - dt.datetime.fromisoformat(item['verifiedAt'])
        if dt.timedelta(0) <= age <= dt.timedelta(days=7) and item.get('catalogueYear') == now.year and (item['title'], item['platform']) not in titles:
            auto.append(item)
    evidence=load_release_evidence()
    feed['recommendations'] = [apply_release_evidence(item,evidence.get(item['id'].removeprefix('netflix-auto-'))) for item in manual + auto]
    feed['seriesDiscovery'] = {k: v for k, v in discovery.items() if k != 'verified'}
    feed['seriesDiscovery']['verifiedCount'] = len(auto)
    return feed


if __name__ == '__main__':
    now = dt.datetime.now(TZ)
    previous = json.loads(DISCOVERY.read_text()) if DISCOVERY.exists() else {}
    result = discover(previous, now)
    DISCOVERY.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    path = Path('public/entertainment-daily.json')
    feed = merge(json.loads(path.read_text()), result, now)
    path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + '\n')
    print('Series discovery:', result['status'], 'verified:', len(result['verified']), 'candidates:', len(result['candidates']))
    if result['status'] == 'failed' or not any(not x.get('verificationStale') for x in result['verified']) or any(x['status'] == 'error' and x['url'] in CATALOGUES for x in result['sources']):
        raise SystemExit(1)
    if result['status'] == 'partial':
        print('::warning::Some individual title or news sources could not be verified; see published source health.')
