"""CPBL's published stats-site API; never substitute historical fixtures on failure."""
import datetime as dt
import json
import urllib.parse
import urllib.request

TZ = dt.timezone(dt.timedelta(hours=8))
BASE = 'https://stats.cpbl.com.tw'
KINDS = ('A', 'E', 'C')


def load_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def fetch_games(now, load=load_json):
    today = now.astimezone(TZ).date()
    end = today + dt.timedelta(days=31)
    months = sorted({(today.year, today.month), (end.year, end.month)})
    games = {}
    for year, month in months:
        for kind in KINDS:
            url = BASE + '/api/proxy/v1/games/schedule?' + urllib.parse.urlencode({'kindCode': kind, 'year': year, 'month': month})
            payload = load(url)
            rows = payload.get('Data', {}).get('Games')
            if not isinstance(rows, list):
                raise ValueError('Official schedule response has no Games array')
            for raw in rows:
                start = dt.datetime.fromisoformat(raw['PreExeDate'])
                if start.tzinfo is None:
                    start = start.replace(tzinfo=TZ)  # official wall-clock Taiwan time
                start = start.astimezone(TZ)
                if not today <= start.date() <= end:
                    continue
                away, home = raw['Visiting']['Team']['Name'], raw['Home']['Team']['Name']
                game_id = raw['GameId']
                if not away or not home or not game_id or raw['KindCode'] != kind:
                    raise ValueError('Invalid official fixture')
                status = {'SCHEDULED': '官方預定賽程', 'START': '同步時進行中（非即時）', 'FINISHED': '已結束', 'POSTPONED': '延賽', 'CANCELLED': '取消'}.get(raw['GameStatus'], '請查官方狀態')
                game = {'id': game_id, 'date': start.date().isoformat(), 'match': f'{away}（客） vs {home}（主）', 'timeTW': start.strftime('%H:%M'), 'venue': raw['Field']['Abbe'], 'status': status, 'source': '中華職棒官方進階數據', 'sourceUrl': BASE + '/schedule/' + game_id, 'series': kind, 'updatedAt': now.isoformat(timespec='seconds')}
                # Same game can appear at its original postponed and rescheduled dates.
                if game_id not in games or (game['date'], game['timeTW']) > (games[game_id]['date'], games[game_id]['timeTW']):
                    games[game_id] = game
    return sorted(games.values(), key=lambda g: (g['date'], g['timeTW'], g['id']))


def refresh(previous, now, load=load_json):
    result = {'cpblLastAttemptAt': now.isoformat(timespec='seconds'), 'cpblAsOfDate': now.astimezone(TZ).date().isoformat(), 'cpblGames': []}
    try:
        import os
        if os.environ.get('WECARE_OFFLINE') == '1':
            raise RuntimeError('Offline fixture validation')
        result['cpblGames'] = fetch_games(now, load)
        result.update(cpblLastSuccessAt=now.isoformat(timespec='seconds'), cpblSyncError=None, cpblDataMode='official', cpblValidUntil=(now + dt.timedelta(hours=3)).isoformat(timespec='seconds'))
    except Exception as exc:
        print('CPBL sync failed:', exc)
        result.update(cpblLastSuccessAt=previous.get('cpblLastSuccessAt'), cpblSyncError='官方賽程更新失敗，已隱藏舊資料；請開啟官方賽程確認。', cpblDataMode='unavailable', cpblValidUntil=None)
    return result


if __name__ == '__main__':
    from pathlib import Path
    path = Path('public/entertainment-daily.json')
    feed = json.loads(path.read_text())
    feed.update(refresh(feed, dt.datetime.now(TZ)))
    path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + '\n')
    if feed['cpblSyncError']:
        raise SystemExit(1)
