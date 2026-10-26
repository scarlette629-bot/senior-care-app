export function freshSeries(item, now=Date.now()) {
  if(!item)return false;
  if(!item.autoDiscovered)return true;
  const verified=Date.parse(item.verifiedAt);
  return Number.isFinite(verified)&&verified<=now&&now-verified<=7*86400000;
}
export function selectDailySeries(feed, filter='mine', interests=[], now=Date.now()) {
  const eligible=(feed?.recommendations||[]).filter(x=>interests.includes(x?.type)&&x?.verified===true&&x.title&&x.platform&&x.description&&freshSeries(x,now)&&dailySeriesEligible(x,now));
  const unique=new Map();
  for(const item of eligible){const key=item.title.normalize('NFKC').replace(/\s/g,'').toLowerCase();if(!unique.has(key))unique.set(key,item);}
  const all=[...unique.values()];
  const knownTitles=new Set(all.flatMap(item=>[item.title,...(item.aliases||[])]).map(title=>title.normalize("NFKC").replace(/\s/g,"").toLowerCase()));
  const matches=x=>interests.includes(x.type)&&(!interests.includes(filter)||x.type===filter);
  const items=all.filter(matches).sort((a,b)=>String(b.firstSeenAt||b.verifiedAt||b.releaseDate||'').localeCompare(String(a.firstSeenAt||a.verifiedAt||a.releaseDate||'')));
  const candidates=(feed?.seriesDiscovery?.candidates||[]).filter(x=>x&&matches(x)&&!knownTitles.has(String(x.title||'').normalize('NFKC').replace(/\s/g,'').toLowerCase())&&Number.isFinite(Date.parse(x.publishedAt))&&now-Date.parse(x.publishedAt)>=0&&now-Date.parse(x.publishedAt)<=7*86400000);
  return {all,items,candidates};
}
export function recentPremiere(item,now=Date.now()) {
  if(item?.releasePrecision!=='day'||!/^\d{4}-\d{2}-\d{2}$/.test(item.releaseDate||'')||!/^https:\/\//.test(item.releaseSourceUrl||''))return false;
  const day=Date.parse(item.releaseDate+'T00:00:00Z');
  if(!Number.isFinite(day)||new Date(day).toISOString().slice(0,10)!==item.releaseDate)return false;
  const today=Date.parse(new Date(now+8*3600000).toISOString().slice(0,10)+'T00:00:00Z');
  return day<=today&&today-day<30*86400000;
}
// Unknown premiere dates stay visible; never use the check time as a release date.
export function dailySeriesEligible(item, now=Date.now()) {
  const raw=item?.type==='綜藝'&&item.latestEpisodeDate ? item.latestEpisodeDate : item?.releaseDate;
  const today=new Date(now+8*3600000).toISOString().slice(0,10);
  if(/^\d{4}-\d{2}-\d{2}$/.test(raw||'')) {
    const date=Date.parse(raw+'T00:00:00Z');
    if(Number.isFinite(date)&&new Date(date).toISOString().slice(0,10)===raw)
      return date<=Date.parse(today)&&Date.parse(today)-date<30*86400000;
  }
  // A past year is enough evidence that a work exceeds 30 days, except
  // at the year boundary where the exact day could still be recent.
  const year=Number(item?.catalogueYear||(/^\d{4}/.exec(raw||'')||[])[0]);
  if(year&&Date.parse(`${year}-12-31T00:00:00Z`)<Date.parse(today)-29*86400000)return false;
  return item?.releaseStatus!=='upcoming';
}
export function currentWeeklyHot(feed,interests=[],now=Date.now()) {
  const taipei=new Date(now+8*3600000);const day=new Date(Date.UTC(taipei.getUTCFullYear(),taipei.getUTCMonth(),taipei.getUTCDate()));day.setUTCDate(day.getUTCDate()-((day.getUTCDay()+6)%7));const start=day.toISOString().slice(0,10);const end=new Date(day.getTime()+6*86400000).toISOString().slice(0,10);
  const hot=feed?.weeklyHot;
  if(hot?.weekStart!==start||hot?.weekEnd!==end)return [];
  return (hot.items||[]).filter(x=>interests.includes(x.type)&&x.sourceUrl&&Number.isFinite(Date.parse(x.observedAt))&&x.observedAt.slice(0,10)>=start&&x.observedAt.slice(0,10)<=end&&Date.parse(x.observedAt)<=now).sort((a,b)=>Number(!!b.isWeiboMention)-Number(!!a.isWeiboMention)||String(b.observedAt).localeCompare(String(a.observedAt)));
}
