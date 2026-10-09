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
# Fetch the published CPBL site endpoint (not the unverified stats proxy).
# Some cloud data-center IP addresses are denied by cpbl.com.tw. Failure must
# NEVER replace a reviewed fixture or advance cpblLastSuccessAt.
def refresh_cpbl():
    if os.environ.get("WECARE_OFFLINE")=="1": raise RuntimeError("Offline fixture validation")
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
keys={(g["date"],g["timeTW"]) for g in official}
merged=official+[g for g in reviewed if (g["date"],g["timeTW"]) not in keys]
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
# Chinese-market weekly discussions are not lifetime recommendations. Freshness is checked
# against the current Asia/Taipei ISO week. Weibo mentions take precedence
# over other news; do not invent engagement totals or rank without an official rank.
def update_weekly_hot(reviewed):
    week_start=NOW.date()-datetime.timedelta(days=NOW.weekday())
    week_end=week_start+datetime.timedelta(days=6)
    minimum=datetime.datetime.combine(week_start,datetime.time.min,tzinfo=NOW.tzinfo)
    news=[]
    query="site:weibo.com 电视剧 综艺 热搜 本周 OR 电视剧 热播 微博 热议"
    url="https://news.google.com/rss/search?"+urllib.parse.urlencode({
        "q":query,"hl":"zh-CN","gl":"HK","ceid":"HK:zh-Hans"})
    try:
        if os.environ.get("WECARE_OFFLINE")=="1": raise RuntimeError("Offline check")
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 WECARE/1.0"})
        with urllib.request.urlopen(req,timeout=18) as resp:
            root=ET.fromstring(resp.read())
        for item in root.findall("./channel/item"):
            title=(item.findtext("title") or "").strip()
            link=(item.findtext("link") or "").strip()
            pub=(item.findtext("pubDate") or "").strip()
            if not title or not link:continue
            try:
                stamp=email.utils.parsedate_to_datetime(pub).astimezone(NOW.tzinfo)
            except Exception:continue
            if stamp<minimum or stamp>NOW:continue
            source=(item.findtext("source") or "").strip()
            is_weibo=("微博" in title or "微博" in source or "weibo.com" in link)
            news.append({"title":title,"url":link,"publishedAt":stamp.isoformat(timespec="minutes"),
                         "source":source or "華語娛樂新聞","weiboMention":is_weibo})
    except Exception as exc:
        print("Weekly hot lookup unavailable:",exc)
    matched=[]
    for entry in reviewed:
        if not entry.get("verified") or entry.get("type") not in ("台劇","陸劇","綜藝","韓劇","日劇","歐美劇"):continue
        title=entry.get("title","")
        signals=[n for n in news if title and title in n["title"]]
        if not signals:continue
        signals.sort(key=lambda x:(int(bool(x["weiboMention"])),x["publishedAt"]),reverse=True)
        top=signals[0]
        matched.append({"id":entry["id"],"title":title,"type":entry["type"],
                        "platform":entry.get("platform"),"description":entry.get("description"),
                        "cast":entry.get("cast"),"releaseDate":entry.get("releaseDate"),
                        "source":top["source"],"sourceUrl":top["url"],"observedAt":top["publishedAt"],
                        "isWeiboMention":top["weiboMention"],"evidenceType":"本週新聞／微博相關報導",
                        "verified":True})
    # Also show current-week entertainment reports for newly released titles not yet
    # represented in the hand-reviewed catalogue. These are labeled as news only,
    # not certified rankings or verified streaming premieres.
    for kind,items in out["categories"].items():
        for article in items:
            try:
                ts=email.utils.parsedate_to_datetime(article.get("published","")).astimezone(NOW.tzinfo)
            except Exception:continue
            if ts<minimum or ts>NOW:continue
            title=article.get("title","").strip()
            if not title:continue
            if any(m["title"] in title for m in matched):continue
            source=article.get("source") or "華語娛樂報導"
            is_weibo=("微博" in title or "微博" in source)
            matched.append({"id":"news-"+kind+"-"+ts.strftime("%Y%m%d%H%M")+"-"+str(len(matched)),
                "title":title,"type":kind,"source":source,"sourceUrl":article.get("url"),
                "observedAt":ts.isoformat(timespec="minutes"),"isWeiboMention":is_weibo,
                "evidenceType":"本週新聞話題（非官方排行）","verified":False})
    # Editorially reviewed, dated public reports are a fallback when Google RSS
    # is unavailable on the Actions runner. They expire automatically on Monday
    # and are NEVER recycled into a new week.
    reviewed_hot=pathlib.Path("data/weekly-hot-reviewed.json")
    if reviewed_hot.exists():
        try:
            seed=json.loads(reviewed_hot.read_text(encoding="utf-8"))
            if seed.get("weekStart")==week_start.isoformat() and seed.get("weekEnd")==week_end.isoformat():
                have={(x.get("title"),x.get("sourceUrl")) for x in matched}
                for x in seed.get("items",[]):
                    try: observed=datetime.datetime.fromisoformat(x["observedAt"]).astimezone(NOW.tzinfo)
                    except (ValueError,KeyError):continue
                    if not minimum<=observed<=NOW:continue
                    if x.get("type") not in QUERIES or not x.get("sourceUrl","").startswith("https://"):continue
                    if (x.get("title"),x["sourceUrl"]) in have:continue
                    matched.append(x)
                    have.add((x["title"],x["sourceUrl"]))
        except (OSError,ValueError,TypeError) as exc:
            print("Reviewed weekly topics unavailable:",exc)
    # Highest confidence: a Weibo-specific news item this week. Chronological
    # order within each tier, without inventing a numeric popularity score.
    matched.sort(key=lambda x:(int(bool(x["isWeiboMention"])),x["observedAt"]),reverse=True)
    return {"weekStart":week_start.isoformat(),"weekEnd":week_end.isoformat(),
            "updatedAt":NOW.isoformat(timespec="minutes"),"market":"台灣及華語市場",
            "method":"本週報導提及作品，微博相關報導優先；不代表微博官方熱搜排名",
            "items":matched[:12]}

out["weeklyHot"]=update_weekly_hot(out["recommendations"])
p=pathlib.Path("public/entertainment-daily.json")
if any(out["categories"].values()) or out["recommendations"] or out["cpblGames"]:
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
else:
    raise RuntimeError("No news fetched; preserve previous published data")
