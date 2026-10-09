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
    for field in ("id","title","type","platform","releaseDate","cast","description","source","url"):
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
