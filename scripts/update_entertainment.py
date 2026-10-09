import json,datetime,email.utils,urllib.parse,urllib.request,xml.etree.ElementTree as ET,pathlib
NOW=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
QUERIES={"陸劇":"陸劇 微博 熱搜 新劇","台劇":"台劇 Netflix 愛奇藝 Disney+ 新劇","韓劇":"韓劇 Netflix Disney+ 新劇","綜藝":"綜藝 Netflix 愛奇藝 Disney+ 新節目"}
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
        out["categories"][kind]=[]
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
