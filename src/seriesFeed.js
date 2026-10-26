export function freshSeries(item, now=Date.now()) {
  if(!item)return false;
  if(!item.autoDiscovered)return true;
  const verified=Date.parse(item.verifiedAt);
  return Number.isFinite(verified)&&verified<=now&&now-verified<=7*86400000;
}
export function selectDailySeries(feed, filter='all', interests=[], now=Date.now()) {
  const year=String(new Date(now+8*3600000).getUTCFullYear());
  const eligible=(feed?.recommendations||[]).filter(x=>x?.verified===true&&x.title&&x.platform&&x.description&&freshSeries(x,now)&&(x.autoDiscovered||String(x.releaseDate||x.releaseWindow||'').startsWith(year)));
  const unique=new Map();
  for(const item of eligible){const key=item.title.normalize('NFKC').replace(/\s/g,'').toLowerCase();if(!unique.has(key))unique.set(key,item);}
  const all=[...unique.values()];
  const matches=x=>filter==='all'||(filter==='mine'?interests.includes(x.type):x.type===filter);
  const items=all.filter(matches).sort((a,b)=>String(b.firstSeenAt||b.verifiedAt||b.releaseDate||'').localeCompare(String(a.firstSeenAt||a.verifiedAt||a.releaseDate||'')));
  const candidates=(feed?.seriesDiscovery?.candidates||[]).filter(x=>x&&matches(x)&&!unique.has(String(x.title||'').normalize('NFKC').replace(/\s/g,'').toLowerCase())&&Number.isFinite(Date.parse(x.publishedAt))&&now-Date.parse(x.publishedAt)>=0&&now-Date.parse(x.publishedAt)<=7*86400000);
  return {all,items,candidates};
}
