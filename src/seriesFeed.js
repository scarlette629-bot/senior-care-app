export function freshSeries(item, now=Date.now()) {
  if(!item)return false;
  if(!item.autoDiscovered)return true;
  const verified=Date.parse(item.verifiedAt);
  return Number.isFinite(verified)&&verified<=now&&now-verified<=7*86400000;
}
export function selectDailySeries(feed, filter='all', interests=[], now=Date.now()) {
  const all=(feed?.recommendations||[]).filter(x=>x?.autoDiscovered&&x.verified===true&&x.title&&x.platform&&x.description&&freshSeries(x,now));
  const matches=x=>filter==='all'||(filter==='mine'?interests.includes(x.type):x.type===filter);
  const items=all.filter(matches).sort((a,b)=>String(b.firstSeenAt).localeCompare(String(a.firstSeenAt)));
  const candidates=(feed?.seriesDiscovery?.candidates||[]).filter(x=>x&&matches(x)&&Number.isFinite(Date.parse(x.publishedAt))&&now-Date.parse(x.publishedAt)>=0&&now-Date.parse(x.publishedAt)<=7*86400000);
  return {all,items,candidates};
}
