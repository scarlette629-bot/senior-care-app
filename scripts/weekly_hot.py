"""Current-week Chinese entertainment reports; no previous-week substitution."""
import datetime as dt
import email.utils
import hashlib
import json
import os
import re
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
TZ=dt.timezone(dt.timedelta(hours=8))
QUERIES={
 '陸劇':'(陸劇 OR 电视剧) (熱播 OR 热播 OR 熱搜 OR 热搜 OR 微博 OR 開播) when:7d',
 '台劇':'台劇 (熱播 OR 熱門 OR 新劇 OR 收視 OR Netflix) when:7d',
 '綜藝':'綜藝 (熱播 OR 熱搜 OR 微博 OR 收視 OR 熱門) when:7d'}

def get(url):
 if os.environ.get('WECARE_OFFLINE')=='1':raise OSError('Offline test')
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:return r.read()

def refresh(previous,now,load=get):
 start=now.astimezone(TZ).date()-dt.timedelta(days=now.astimezone(TZ).weekday());end=start+dt.timedelta(days=6)
 minimum=dt.datetime.combine(start,dt.time.min,tzinfo=TZ);stamp=now.isoformat(timespec='seconds')
 items={};sources=[]
 known={k:[] for k in QUERIES}
 evidence_path=Path(__file__).resolve().parents[1]/'data/series-release-evidence.json'
 if evidence_path.exists():
  for entry in json.loads(evidence_path.read_text()).values():
   if entry.get('type') in known:known[entry['type']].extend([entry['title']]+entry.get('aliases',[]))
 for kind,query in QUERIES.items():
  if known[kind]:query='('+query.replace(' when:7d','')+' OR '+' OR '.join(known[kind])+') when:7d'
  url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'zh-TW','gl':'TW','ceid':'TW:zh-Hant'})
  try:
   root=ET.fromstring(load(url))
   if root.tag!='rss' or root.find('channel') is None:raise ValueError('Invalid RSS response')
   accepted=0
   for story in root.findall('./channel/item'):
    title=(story.findtext('title') or '').strip();link=(story.findtext('link') or '').strip();source=(story.findtext('source') or '公開娛樂新聞').strip()
    try:published=email.utils.parsedate_to_datetime(story.findtext('pubDate') or '').astimezone(TZ)
    except (ValueError,TypeError):continue
    if not minimum<=published<=now or not title or not link.startswith('https://'):continue
    anchors={'陸劇':r'陸劇|陆剧|电视剧|古裝|古装|國產劇|国产剧|優酷|优酷|騰訊|腾讯|芒果|愛奇藝|爱奇艺','台劇':r'台劇|臺劇|台灣劇|臺灣劇|民視|三立|公視|八大','綜藝':r'綜藝|综艺|節目|节目|真人秀|實境|選秀|歌唱|料理|美食'}
    if not (re.search(anchors[kind],title) or any(t in title for t in known[kind])) or re.search(r'韓劇|韩剧|日劇|日剧|歐美劇|近年|歷年|公認|史上|回顧|经典老剧|經典老劇',title):continue
    if link in items:continue
    items[link]={'id':'weekly-'+hashlib.sha256(link.encode()).hexdigest()[:16],'title':title,'type':kind,'source':source,'sourceUrl':link,'observedAt':published.isoformat(timespec='seconds'),'isWeiboMention':'微博' in title or '微博' in source,'verified':False,'evidenceType':'本週娛樂報導（非官方熱搜排行）'}
    accepted+=1
    if accepted>=8:break
   sources.append({'type':kind,'status':'success','checkedAt':stamp,'itemCount':accepted})
  except Exception as exc:sources.append({'type':kind,'status':'error','checkedAt':stamp,'error':str(exc)[:160]})
 # Retain only genuinely current-week dated reports when their category fails.
 failed={x['type'] for x in sources if x['status']=='error'}
 for item in previous.get('items',[]):
  if item.get('type') not in failed:continue
  try:observed=dt.datetime.fromisoformat(item['observedAt'])
  except (ValueError,KeyError):continue
  if minimum<=observed<=now and item.get('sourceUrl'):items.setdefault(item['sourceUrl'],item)
 success=all(x['status']=='success' for x in sources)
 return {'weekStart':start.isoformat(),'weekEnd':end.isoformat(),'checkedAt':stamp,'updatedAt':stamp,'lastSuccessfulAt':stamp if success else previous.get('lastSuccessfulAt'),'status':'success' if success else 'partial' if len(failed)<len(QUERIES) else 'failed','sources':sources,'market':'台灣及華語市場','method':'本週發布的娛樂報導；微博相關報導優先，不宣稱官方熱搜或播放排名','items':sorted(items.values(),key=lambda x:(x.get('isWeiboMention',False),x['observedAt']),reverse=True)}

if __name__=='__main__':
 path=Path('public/entertainment-daily.json');feed=json.loads(path.read_text());feed['weeklyHot']=refresh(feed.get('weeklyHot',{}),dt.datetime.now(TZ));path.write_text(json.dumps(feed,ensure_ascii=False,indent=2)+'\n');print('Weekly topics:',feed['weeklyHot']['status'],len(feed['weeklyHot']['items']))
 if feed['weeklyHot']['status']=='failed':raise SystemExit(1)
