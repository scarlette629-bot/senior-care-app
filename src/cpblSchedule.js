export function cpblView(feed, now = Date.now()) {
  const today = new Date(now + 8 * 3600000).toISOString().slice(0, 10);
  const success = Date.parse(feed?.cpblLastSuccessAt);
  const current = feed?.cpblDataMode === 'official' && !feed?.cpblSyncError && feed?.cpblAsOfDate === today && Number.isFinite(success) && success <= now + 60000 && now - success <= 3 * 3600000 && Date.parse(feed?.cpblValidUntil) > now;
  return { current, games: current ? (feed.cpblGames || []).filter(g => /^\d{4}-\d{2}-\d{2}$/.test(g.date) && g.date >= today) : [] };
}
