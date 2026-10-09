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
# Fetch the published CPBL site endpoint (not the unverified stats proxy).
# Some cloud data-center IP addresses are denied by cpbl.com.tw. Failure must
# NEVER replace a reviewed fixture or advance cpblLastSuccessAt.
def refresh_cpbl():
    import http.cookiejar, re
    jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base="https://www.cpbl.com.tw"
    ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    request=urllib.request.Request(base+"/schedule",headers={"User-Agent":ua,"Accept-Language":"zh-TW,zh;q=0.9"})
    with opener.open(request,timeout=12) as response:
        html=response.read().decode("utf-8","replace")
    token=re.search(r"RequestVerificationToken:\\s*'([^']+)'",html)
    if not token:
        token=re.search(r'name="__RequestVerificationToken"\\s+value="([^"]+)"',html)
    if not token:
        raise ValueError("CPBL verification token unavailable (possible cloud IP block)")
    games=[]
    accepted=0
    for kind in ("A","C","E"):  # regular season / postseason series
        body=urllib.parse.urlencode({"calendar":f"{NOW.year}/01/01","location":"","kindCode":kind}).encode()
        req=urllib.request.Request(base+"/schedule/getgamedatas",data=body,headers={
            "User-Agent":ua,"RequestVerificationToken":token.group(1),
            "Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest",
            "Referer":base+"/schedule"})
        try:
            with opener.open(req,timeout=12) as response: payload=json.load(response)
            if not payload.get("Success"): continue
            raw=payload.get("GameDatas")
            rows=json.loads(raw) if isinstance(raw,str) else raw
            if not isinstance(rows,list): continue
            accepted+=1
            for game in rows:
                if not isinstance(game,dict): continue
                date=str(game.get("GameDate") or "")[:10]
                if len(date)!=10 or date < (NOW.date()-datetime.timedelta(days=1)).isoformat() or date > (NOW.date()+datetime.timedelta(days=45)).isoformat(): continue
                away=game.get("VisitingTeamName") or ""
                home=game.get("HomeTeamName") or ""
                if not away or not home: continue
                time_str=str(game.get("PreExeDate") or game.get("GameDateTimeS") or "")[11:16] or "待公布"
                venue=game.get("FieldName") or game.get("FieldAbbe") or "待公布"
                status="官方預定賽程（非即時結果）"
                if game.get("IsGameStop") in ("1",1,True): status="延賽／保留（請查官方）"
                if game.get("WinningPitcherName"): status="已結束（請查官方比分）"
                games.append({"id":f"official-{kind}-{game.get('GameSno',date)}","date":date,
                    "match":f"{away}（客） vs {home}（主）","timeTW":time_str,
                    "venue":venue,"status":status,"source":"中華職棒官方賽程",
                    "sourceUrl":base+"/schedule","series":kind,
                    "updatedAt":NOW.isoformat(timespec="minutes")})
        except Exception as exc:
            print("CPBL category",kind,"unavailable:",exc)
    if accepted==0: raise ValueError("Official CPBL feed inaccessible or invalid")
    return games

reviewed_path=pathlib.Path("data/cpbl-reviewed-2026.json")
reviewed=json.loads(reviewed_path.read_text(encoding="utf-8")) if reviewed_path.exists() else []
cutoff=(NOW.date()-datetime.timedelta(days=1)).isoformat()
reviewed=[g for g in reviewed if isinstance(g,dict) and g.get("date","")>=cutoff and g.get("match") and g.get("timeTW") and g.get("sourceUrl")]
try:
    official=refresh_cpbl()
    if official:
        out["cpblLastSuccessAt"]=NOW.isoformat(timespec="minutes")
        out["cpblSyncError"]=None
        out["cpblDataMode"]="official"
    else:
        out["cpblLastSuccessAt"]=previous.get("cpblLastSuccessAt")
        out["cpblSyncError"]="官方接口已回應，但近期無可核實場次，顯示人工核對賽程"
        out["cpblDataMode"]="reviewed"
except Exception as exc:
    print("CPBL official sync unavailable; retain cross-checked schedule:",exc)
    official=[]
    out["cpblLastSuccessAt"]=previous.get("cpblLastSuccessAt")
    out["cpblSyncError"]="中職官網自動連線未成功，以下為人工核對的預定賽程；比賽異動以官方公告為準"
    out["cpblDataMode"]="reviewed"
# Merge reviewed fixtures only where an official game was not available; never
# mark reviewed fixtures as a successful network synchronization.
keys={(g["date"],g["match"]) for g in official}
merged=official+[g for g in reviewed if (g["date"],g["match"]) not in keys]
merged.sort(key=lambda g:(g.get("date",""),g.get("timeTW",""),g.get("id","")))
if not merged:
    old=previous.get("cpblGames",[])
    merged=[g for g in old if isinstance(g,dict) and g.get("date","")>=cutoff]
out["cpblGames"]=merged
out["cpblReviewedAt"]=max((g.get("verifiedAt","") for g in reviewed),default=previous.get("cpblReviewedAt"))

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
p=pathlib.Path("public/entertainment-daily.json")
if any(out["categories"].values()) or out["recommendations"] or out["cpblGames"]:
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
else:
    raise RuntimeError("No news fetched; preserve previous published data")
