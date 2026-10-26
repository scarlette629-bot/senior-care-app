export function freshSeries(item, now=Date.now()) {
  if(!item)return false;
  if(!item.autoDiscovered)return true;
  const verified=Date.parse(item.verifiedAt);
  return Number.isFinite(verified)&&verified<=now&&now-verified<=7*86400000;
}
