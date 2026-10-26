import json,datetime,email.utils,urllib.parse,urllib.request,xml.etree.ElementTree as ET,pathlib,os
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
QUERIES={"陸劇":"陸劇 微博 熱搜 新劇","台劇":"台劇 Netflix 愛奇藝 Disney+ 新劇","韓劇":"韓劇 Netflix Disney+ 新劇","綜藝":"綜藝 芒果TV 愛奇藝 騰訊視頻 Netflix 新節目","日劇":"日劇 Netflix 新劇","歐美劇":"歐美劇 Netflix 新劇"}
previous_path=pathlib.Path("public/entertainment-daily.json")
try:
    previous=json.loads(previous_path.read_text(encoding="utf-8"))
except Exception:
    previous={}
out={"schemaVersion":"1.04","updatedAt":NOW.isoformat(timespec="minutes"),"categories":{},"recommendations":[],"cpblGames":previous.get("cpblGames",[]),"sports":{"棒球":[],"籃球":[],"羽球":[],"桌球":[]}}
for kind,q in QUERIES.items():
    url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q,"hl":"zh-TW","gl":"TW","ceid":"TW:zh-Hant"})
    try:
        if os.environ.get("WECARE_OFFLINE")=="1": raise RuntimeError("Offline fixture validation")
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 WECARE/1.0"})
        with urllib.request.urlopen(req,timeout=25) as resp: root=ET.fromstring(resp.read())
        items=[]
        for item in root.findall("./channel/item"):
            title=(item.findtext("title") or "").strip()
            link=(item.findtext("link") or "").strip()
            pub=(item.findtext("pubDate") or "").strip()
            source=(item.findtext("source") or "").strip()
            if not title or not link: continue
            items.append({"title":title,"url":link,"published":pub,"source":source})
            if len(items)>=5:break
        out["categories"][kind]=items
    except Exception as exc:
        print(kind,exc)
        out["categories"][kind]=previous.get("categories",{}).get(kind,[])
# Share the same validated updater with the hourly sports refresh.
from cpbl import refresh as refresh_cpbl
out.update(refresh_cpbl(previous, NOW))

# Only explicitly reviewed, sourced text recommendations are eligible for publication.
# This file is maintained separately; do not infer plots or release dates from RSS headlines.
curated=pathlib.Path("data/entertainment-reviewed.json")
if curated.exists():
    entries=json.loads(curated.read_text(encoding="utf-8"))
    if not isinstance(entries,list): raise ValueError("Reviewed recommendations must be a list")
    allowed={"愛奇藝","騰訊視頻","芒果TV","Netflix"}
    for entry in entries:
        if not isinstance(entry,dict) or entry.get("verified") is not True: continue
        if entry.get("platform") not in allowed: continue
        if not all(isinstance(entry.get(k),str) and entry[k].strip() for k in ("title","description","url","source")): continue
        parsed=urllib.parse.urlparse(entry["url"])
        if parsed.scheme!="https" or not parsed.hostname: continue
        if len(entry["description"])<35: continue
        out["recommendations"].append(entry)
    # Keep all reviewed recommendations; the UI filters to the user’s selected interests.
# Daily discovery of recently mentioned Mainland-China drama titles. News mentions are
# candidates, NEVER verified premiere dates or confirmed streaming availability.
def discover_china_drama_titles():
    import re
    seen={}
    cutoff=NOW-datetime.timedelta(days=30)
    searches=["陸劇 新劇 開播 愛奇藝 騰訊 優酷 芒果TV","國產劇 今日開播 定檔 新劇","陸劇 2026 十月 新劇 追劇"]
    for query in searches:
        try:
            if os.environ.get("WECARE_OFFLINE")=="1":raise RuntimeError("offline")
            url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":query,"hl":"zh-TW","gl":"TW","ceid":"TW:zh-Hant"})
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 WECARE/1.0"})
            with urllib.request.urlopen(req,timeout=18) as response:root=ET.fromstring(response.read())
            for story in root.findall("./channel/item"):
                headline=(story.findtext("title") or "").strip()
                link=(story.findtext("link") or "").strip()
                stamp=(story.findtext("pubDate") or "").strip()
                source=(story.findtext("source") or "").strip()
                try: published=email.utils.parsedate_to_datetime(stamp).astimezone(NOW.tzinfo)
                except (ValueError,TypeError):continue
                if not cutoff<=published<=NOW or not link.startswith("https://"):continue
                if any(term in headline for term in ("回顧","經典老劇","重播","播出十年","播出14年")):continue
                for title in re.findall(r"《([^》]{2,22})》",headline):
                    title=title.strip()
                    if not re.search(r"[\u4e00-\u9fff]",title):continue
                    if title not in seen or published>datetime.datetime.fromisoformat(seen[title]["publishedAt"]):
                        seen[title]={"title":title,"publishedAt":published.isoformat(timespec="minutes"),
                            "source":source or "近期公開新聞","sourceUrl":link,
                            "status":"新聞提及（尚未核實正式開播）"}
        except Exception as exc:print("China drama discovery:",exc)
    return sorted(seen.values(),key=lambda x:x["publishedAt"],reverse=True)[:18]

new_china_titles=discover_china_drama_titles()
out["chinaDramaNewTitles"]={"checkedAt":NOW.isoformat(timespec="minutes"),"items":new_china_titles,
    "lastSuccessfulAt":NOW.isoformat(timespec="minutes") if new_china_titles else previous.get("chinaDramaNewTitles",{}).get("lastSuccessfulAt"),
    "method":"最近30天新聞提及的劇名，待官方核實後才能視為已開播"}
if not new_china_titles:
    saved=previous.get("chinaDramaNewTitles",{}).get("items",[])
    cutoff=(NOW-datetime.timedelta(days=30)).date().isoformat()
    out["chinaDramaNewTitles"]["items"]=[x for x in saved if x.get("publishedAt","")[:10]>=cutoff][:18]

# Preserve automatically verified titles across independent entertainment refreshes.
from discover_series import merge as merge_series
series_path=pathlib.Path("public/series-discovery.json")
if series_path.exists():
    out=merge_series(out,json.loads(series_path.read_text(encoding="utf-8")),NOW)

from weekly_hot import refresh as refresh_weekly_hot
out["weeklyHot"]=refresh_weekly_hot(previous.get("weeklyHot",{}),NOW)
# Korean, Japanese and Western series: separate, sourced weekly platform updates.
# This list is NOT a popularity ranking. RSS articles must have actual same-week
# publication timestamps; curated premiere-date items automatically expire Sunday.
def update_weekly_streaming():
    start=NOW.date()-datetime.timedelta(days=NOW.weekday())
    end=start+datetime.timedelta(days=6)
    minimum=datetime.datetime.combine(start,datetime.time.min,tzinfo=NOW.tzinfo)
    result=[]
    reviewed_path=pathlib.Path("data/weekly-streaming-reviewed.json")
    if reviewed_path.exists():
        try:
            seed=json.loads(reviewed_path.read_text(encoding="utf-8"))
            if seed.get("weekStart")==start.isoformat() and seed.get("weekEnd")==end.isoformat():
                for item in seed.get("items",[]):
                    if not isinstance(item,dict):continue
                    try: moment=datetime.datetime.fromisoformat(item["eventAt"]).astimezone(NOW.tzinfo)
                    except (KeyError,ValueError,TypeError):continue
                    if not minimum<=moment<=NOW:continue
                    if item.get("platform") not in ("Netflix","Disney+","HBO Max"):continue
                    if not set(item.get("interests",[])).intersection(("韓劇","日劇","歐美劇")):continue
                    if not str(item.get("sourceUrl","")).startswith("https://"):continue
                    result.append(item)
        except Exception as exc:print("Reviewed streaming updates unavailable:",exc)
    queries=[
        ("Netflix","韓劇","Netflix 韓劇 新劇 新消息 本週"),
        ("Netflix","日劇","Netflix 日劇 新劇 新消息 本週"),
        ("Netflix","歐美劇","Netflix 歐美劇 新劇 本週"),
        ("Disney+","韓劇","Disney+ 韓劇 新劇 新消息 本週"),
        ("Disney+","日劇","Disney+ 日劇 新劇 新消息 本週"),
        ("Disney+","歐美劇","Disney+ 歐美劇 新劇 本週"),
        ("HBO Max","韓劇","HBO Max 韓劇 新劇 本週"),
        ("HBO Max","日劇","HBO Max 日劇 新劇 本週"),
        ("HBO Max","歐美劇","HBO Max 歐美劇 新劇 本週")]
    for platform,kind,query in queries:
        try:
            if os.environ.get("WECARE_OFFLINE")=="1":raise RuntimeError("Offline test")
            url="https://news.google.com/rss/search?"+urllib.parse.urlencode({
                "q":query,"hl":"zh-TW","gl":"TW","ceid":"TW:zh-Hant"})
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 WECARE/1.0"})
            with urllib.request.urlopen(req,timeout=10) as response:root=ET.fromstring(response.read())
            added=0
            for article in root.findall("./channel/item"):
                title=(article.findtext("title") or "").strip()
                link=(article.findtext("link") or "").strip()
                try:pub=email.utils.parsedate_to_datetime(article.findtext("pubDate") or "").astimezone(NOW.tzinfo)
                except Exception:continue
                if pub<minimum or pub>NOW or not title or not link.startswith("https://"):continue
                if platform.lower().replace(" ","") not in title.lower().replace(" ","") and platform!="HBO Max":continue
                if any(x.get("title")==title for x in result):continue
                result.append({"id":"rss-"+kind+"-"+str(len(result))+"-"+pub.strftime("%Y%m%d"),
                    "title":title,"type":kind,"interests":[kind],"platform":platform,
                    "eventAt":pub.isoformat(timespec="minutes"),"eventLabel":"本週媒體消息（非官方熱度榜）",
                    "source":(article.findtext("source") or "華語娛樂新聞").strip(),
                    "sourceUrl":link,"evidenceType":"本週新聞"})
                added+=1
                if added>=2:break
        except Exception as exc:print("Streaming RSS unavailable",platform,kind,str(exc)[:120])
    # Keep curated verified source items visible ahead of general RSS discovery.
    curated=[x for x in result if not str(x.get("id","")).startswith("rss-")]
    found=[x for x in result if str(x.get("id","")).startswith("rss-")]
    return {"weekStart":start.isoformat(),"weekEnd":end.isoformat(),
        "updatedAt":NOW.isoformat(timespec="minutes"),"market":"台灣關注的三大串流平台",
        "method":"官方新公告或本週新上架優先；其餘為當週相關消息，不宣稱平台排行",
        "items":curated[:10]+found[:18]}

out["weeklyStreaming"]=update_weekly_streaming()

p=pathlib.Path("public/entertainment-daily.json")
if any(out["categories"].values()) or out["recommendations"] or out["cpblGames"]:
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
else:
    raise RuntimeError("No news fetched; preserve previous published data")
