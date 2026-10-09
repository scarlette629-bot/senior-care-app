import json,datetime,email.utils,urllib.parse,urllib.request,xml.etree.ElementTree as ET,pathlib
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
# CPBL schedule: official CPBL advanced-statistics API; preserve last successful feed on failure.
def refresh_cpbl():
    import zoneinfo
    today=NOW.date()
    games=[]
    for delta in range(0,7):
        date=(today+datetime.timedelta(days=delta)).isoformat()
        endpoint="https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/"+date
        req=urllib.request.Request(endpoint,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=15) as response:
            payload=json.load(response)
        if isinstance(payload,dict):
            rows=next((payload[k] for k in ("games","data","schedule","results") if isinstance(payload.get(k),list)),[])
        elif isinstance(payload,list): rows=payload
        else: rows=[]
        for game in rows:
            if not isinstance(game,dict): continue
            visitor=game.get("awayTeam") or game.get("visitingTeam") or game.get("away")
            home=game.get("homeTeam") or game.get("home")
            def team(value):
                if isinstance(value,dict): return value.get("name") or value.get("teamName") or value.get("chineseName") or ""
                return value if isinstance(value,str) else ""
            away_name,home_name=team(visitor),team(home)
            if not away_name or not home_name: continue
            start=game.get("startTime") or game.get("gameTime") or game.get("scheduledTime") or ""
            if isinstance(start,str) and "T" in start:
                try: start=datetime.datetime.fromisoformat(start.replace("Z","+00:00")).astimezone(zoneinfo.ZoneInfo("Asia/Taipei")).strftime("%H:%M")
                except ValueError: pass
            field=game.get("stadium") or game.get("venue") or game.get("field") or ""
            if isinstance(field,dict): field=field.get("name") or field.get("fieldName") or ""
            games.append({"id":str(game.get("id") or game.get("gameId") or date+"-"+away_name),"date":date,"match":away_name+"（客） vs "+home_name+"（主）","timeTW":str(start) if start else "待公布","venue":field,"status":str(game.get("status") or game.get("gameStatus") or "待確認"),"source":"中華職棒官方進階數據","updatedAt":NOW.isoformat(timespec="minutes")})
    return games

try:
    cpbl=refresh_cpbl()
    if not cpbl:
        raise ValueError("CPBL feed returned zero verified games; do not mark synchronization successful")
    out["cpblGames"]=cpbl
    out["cpblLastSuccessAt"]=NOW.isoformat(timespec="minutes")
    print("CPBL verified games:",len(cpbl))
except Exception as exc:
    print("CPBL update failed; preserving previous data:",exc)
    out["cpblLastSuccessAt"]=previous.get("cpblLastSuccessAt")
    out["cpblSyncError"]="官方賽程尚未取得有效資料"

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
        out["recommendations"].append(entry)
    out["recommendations"]=out["recommendations"][:5]
p=pathlib.Path("public/entertainment-daily.json")
if any(out["categories"].values()) or out["recommendations"] or out["cpblGames"]:
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
else:
    raise RuntimeError("No news fetched; preserve previous published data")
