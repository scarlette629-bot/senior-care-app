#!/usr/bin/env python3
"""Regression checks for WECARE entertainment feed, deliberately network-free."""
import json
from pathlib import Path
from urllib.parse import urlparse

root=Path(__file__).resolve().parents[1]
feed=json.loads((root/"public/entertainment-daily.json").read_text(encoding="utf-8"))
source=json.loads((root/"data/entertainment-reviewed.json").read_text(encoding="utf-8"))
fixture=json.loads((root/"data/cpbl-reviewed-2026.json").read_text(encoding="utf-8"))
categories={"韓劇","台劇","陸劇","日劇","歐美劇","綜藝"}
published=[x for x in source if x.get("verified") is True]
assert len(published)>=20, f"Recommendation regression: {len(published)}"
assert {x["type"] for x in published}==categories,"An interest category has no verified recommendations"
for kind in categories:
    amount=sum(x["type"]==kind for x in published)
    assert amount>=3,f"{kind}: only {amount} recommendations"
for x in published:
    for field in ("id","title","type","platform","cast","description","source","url"):
        assert isinstance(x.get(field),str) and x[field].strip(),(x.get("id"),field)
    assert len(x["description"])>=35,x["id"]
    host=urlparse(x["url"]).hostname
    allowed={"Netflix":{"www.netflix.com"},"愛奇藝":{"www.iq.com","iq.com"},"騰訊視頻":{"wetv.vip","v.qq.com"},"芒果TV":{"www.mgtv.com","w.mgtv.com"}}
    assert urlparse(x["url"]).scheme=="https" and host in allowed[x["platform"]],x["id"]
assert len({x["id"] for x in published})==len(published)
assert len(fixture)>=11, "Postseason fixtures missing"
assert len({x["date"] for x in fixture})==len(fixture)
for x in fixture:
    assert x["date"][:4]=="2026"
    for field in ("date","match","timeTW","venue","sourceUrl","verifiedAt"):
        assert x.get(field), (x["id"],field)
    assert "cpbl" in urlparse(x["sourceUrl"]).netloc or urlparse(x["sourceUrl"]).netloc in {"www.cna.com.tw","udn.com"}
actual=feed["recommendations"]
assert {x["id"] for x in actual}=={x["id"] for x in published}, "Published feed is out of sync with reviewed catalogue"
assert len(feed["cpblGames"])>=len(fixture), "Published fixture count shrank"
assert feed.get("cpblDataMode") in {"reviewed","official"}, "Feed must identify fixture mode"
if feed["cpblDataMode"]=="reviewed":
    assert not feed.get("cpblLastSuccessAt"),"Offline/curated data falsely marked official CPBL sync successful"
print("PASS:",len(published),"verified recommendations;",len(fixture),"CPBL fixtures; all six interest categories")

# New release-date and current-week integrity checks
from datetime import date, timedelta
import re
for x in published:
    if x.get("releasePrecision")=="day":
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}",x["releaseDate"]), x["id"]
        date.fromisoformat(x["releaseDate"])
        assert x.get("releaseSourceUrl"),("missing date evidence",x["id"])
    else:
        assert x.get("releaseWindow") or x.get("releaseStatus")=="upcoming", ("missing qualified date window",x["id"])
weekly=feed.get("weeklyHot")
assert weekly and isinstance(weekly.get("items"),list),"Weekly digest is missing"
start=date.fromisoformat(weekly["weekStart"])
end=date.fromisoformat(weekly["weekEnd"])
assert end-start==timedelta(days=6),"Weekly digest must use a seven-day Monday–Sunday window"
for x in weekly["items"]:
    observed=date.fromisoformat(x["observedAt"][:10])
    assert start<=observed<=end,("stale weekly news",x.get("id"))
    assert x.get("source") and x.get("sourceUrl"),("missing hot-list source",x.get("id"))
app=(root/"src/App.jsx").read_text(encoding="utf-8")
assert 'const all=["棒球","籃球","羽球","桌球","台劇","韓劇","陸劇","日劇","歐美劇","綜藝"]' in app
assert 'weeklyCurrent' in app and 'weeklySorted' in app
assert 'aria-label="開啟我的興趣、節目表與本週熱播"' in app

print('PASS: release-date precision, weekly freshness, interest settings')

# Week-specific editorial backup must never leak into future weeks.
seed=json.loads((root/"data/weekly-hot-reviewed.json").read_text(encoding="utf-8"))
assert seed["weekStart"]==weekly["weekStart"] and seed["weekEnd"]==weekly["weekEnd"]
assert len(seed["items"])>=6, "Reviewed weekly hot content should be substantive"
for x in seed["items"]:
    assert weekly["weekStart"]<=x["observedAt"][:10]<=weekly["weekEnd"],x["title"]
    assert x["sourceUrl"].startswith("https://") and x["type"] in categories,x["title"]
assert len(weekly["items"])>=len(seed["items"]), "Current-week curated hot topics missing from preview"
print("PASS: verified source-backed current-week Chinese-market hot topics",len(seed["items"]))


# Home layout regression: avoid duplicate navigation, protect all four task headings.
assert app.count('<InterestSummary go={go}/>')==1, "Duplicate entertainment entry"
assert '<button className="wideCard" onClick={()=>go("entertainment")}' not in app, "Old duplicate card still displayed"
assert app.count('className="taskHeading"')==3, "All four task types must use the shared icon-title row"
styles=(root/"src/styles.css").read_text(encoding="utf-8")
assert '.compactTasks .taskHeading' in styles and 'white-space:nowrap' in styles
assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in styles
assert 'mergedEntertainment' in styles
print("PASS: single entertainment entry and non-wrapping four-card task headings")


# Prevent PWA update regressions: changing UI must always produce a new build ID.
app=(root/"src/App.jsx").read_text(encoding="utf-8")
vite=(root/"vite.config.js").read_text(encoding="utf-8")
sw=(root/"public/sw.js").read_text(encoding="utf-8")
assert "remote.build===WECARE_BUILD_ID" in app
assert "version.json?wecare_check=" in app
assert 'WECARE_VERSION="1.0.5"' in app
assert 'localStorage.clear(' not in app and 'indexedDB.deleteDatabase(' not in app
assert '__WECARE_BUILD_ID__' in vite and 'fileName: "version.json"' in vite
assert 'url.pathname===BASE+"version.json"' in sw
assert 'k.startsWith("wecare-")' in sw
print("PASS: versioned PWA updates preserve user data and bypass cached release metadata")


# Home typography must respond to saved Standard/Large/Extra-large settings.
styles=(root/"src/styles.css").read_text(encoding="utf-8")
for size in ("large","xlarge"):
    assert ':root[data-size="'+size+'"] {' in styles,("Missing size profile",size)
for selector in (".home .hero h1",".home .hero p",".home .sectionTitle h2",".home .compactTasks .taskHeading strong",".home .morningCard strong",".home .mergedEntertainment>.summaryContent>strong"):
    assert selector in styles,("Home font size not adjustable",selector)
assert "--wecare-home-task-detail" in styles
assert "white-space:nowrap" in styles
html=(root/"index.html").read_text(encoding="utf-8")
assert 'rel="apple-touch-icon" sizes="120x120"' in html
assert 'apple-touch-icon.png' in html and 'apple-touch-icon-120x120.png' in html
png=(root/"public/apple-touch-icon-120x120.png").read_bytes()
assert png[:8]==bytes.fromhex("89504e470d0a1a0a")
assert int.from_bytes(png[16:20],"big")==120
assert int.from_bytes(png[20:24],"big")==120
manifest=json.loads((root/"public/manifest.webmanifest").read_text(encoding="utf-8"))
assert any(i.get("src")=="apple-touch-icon-120x120.png" and i.get("type")=="image/png" for i in manifest["icons"])
print("PASS: accessible homepage text sizes and iPhone 6 PNG icon")


# Safety: opening WECARE must not silently delete historical iPhone records.
assert "useEffect(()=>{autoCleanup();" not in app
assert '<DataBackup/>' in app
recovery=(root/"src/DataBackup.jsx").read_text(encoding="utf-8")
assert "WECARE_LOCAL_BACKUP_V1" in recovery
assert "backupCurrent()" in recovery
assert "wecare-recovery-before-import-" in recovery
assert "window.confirm(" in recovery
assert "localStorage.clear(" not in recovery
assert "fetch(" not in recovery, "Local backup must never upload records"
vite=(root/"vite.config.js").read_text(encoding="utf-8")
package=json.loads((root/"package.json").read_text(encoding="utf-8"))
assert '@vitejs/plugin-legacy' in vite and 'iOS >= 12' in vite
assert '@vitejs/plugin-legacy' in package["devDependencies"]
print("PASS: no automatic history deletion, local-only backup and iPhone 6 legacy build")

# iPhone 6 backup must copy actual JSON, not leave old URLs on clipboard.
recovery=(root/"src/DataBackup.jsx").read_text(encoding="utf-8")
assert 'document.execCommand("copy")' in recovery
assert 'navigator.clipboard.writeText(copyText)' in recovery
assert 'onClick={copyBackup}' in recovery
assert 'onClick={testPaste}' in recovery
assert 'sample===copyText' in recovery
assert 'backupCurrent()' in recovery
assert 'window.location.reload()' in recovery
assert 'localStorage.clear(' not in recovery
assert 'fetch(' not in recovery
print("PASS: legacy iPhone clipboard fallback and backup verification")


# WECARE data preservation: no automatic startup cleanup, family backups optional,
# historic records deleted only after the user explicitly confirms.
assert "useEffect(()=>{autoCleanup();" not in app
assert "if(!window.confirm(\"只有這次手動清除過期紀錄" in app
assert "家人協助：備份及還原（平常不需要操作）" in app
assert "<DataBackup/>" in app
assert "🧹 立即清除舊紀錄" in app
assert "localStorage.clear(" not in app

# The weekly streaming section contains all three target platforms, permits
# multiple drama interests per item, and expires on the next Monday.
stream=feed.get("weeklyStreaming")
assert isinstance(stream,dict) and isinstance(stream.get("items"),list)
assert stream["weekStart"]==weekly["weekStart"] and stream["weekEnd"]==weekly["weekEnd"]
assert len(stream["items"])>=5
stream_platforms={x["platform"] for x in stream["items"]}
assert {"Netflix","HBO Max","Disney+"}<=stream_platforms
interest_kinds={t for x in stream["items"] for t in x.get("interests",[])}
assert {"韓劇","日劇","歐美劇"}<=interest_kinds
for x in stream["items"]:
    assert x.get("sourceUrl","").startswith("https://")
    assert x["eventAt"][:10]>=stream["weekStart"] and x["eventAt"][:10]<=stream["weekEnd"]
    assert x.get("source") and x.get("eventLabel") and x.get("description")
    assert x["platform"] in {"Netflix","HBO Max","Disney+"}
assert "weeklyStreamingCurrent" in app
assert "streamingSorted" in app and "pickedStreaming" in app
seed=json.loads((root/"data/weekly-streaming-reviewed.json").read_text(encoding="utf-8"))
assert seed["weekStart"]==stream["weekStart"] and seed["weekEnd"]==stream["weekEnd"]
assert {x["id"] for x in seed["items"]}<={x["id"] for x in stream["items"]}
print("PASS: manual-only data cleanup and 3-platform Korean/Japanese/Western weekly streaming")


# Empty Chinese-market week must not show an empty heading for Western-only
# interests. Compact streaming source/date must not override homepage typography.
assert 'const chineseMarketInterests=shows.filter(t=>["陸劇","台劇","綜藝"].includes(t))' in app
assert 'weeklySorted.length>0&&<section className="interestSection chineseHotSection"' in app
assert 'className="interestSection streamingNews"' in app
assert 'className="streamingMeta"' in app
assert 'taipeiNow=new Date(Date.now()+8*60*60*1000)' in app
assert 'Intl.DateTimeFormat("en-CA"' not in app
styles=(root/"src/styles.css").read_text(encoding="utf-8")
assert '.streamingNews .streamingMeta span' in styles
assert 'font-size:12px' in styles
assert '.message .streamingNews .streamingDescription' in styles
assert ':root[data-theme="night"] .streamingNews .streamingMeta span' in styles
print("PASS: no empty Western-interest Chinese hot block; compact readable stream metadata")
