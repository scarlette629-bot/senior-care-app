import test from 'node:test';
import assert from 'node:assert/strict';
import { cpblView } from '../src/cpblSchedule.js';
const now = Date.parse('2026-10-26T16:00:00+08:00');
const feed = { cpblDataMode: 'official', cpblAsOfDate: '2026-10-26', cpblLastSuccessAt: '2026-10-26T15:00:00+08:00', cpblValidUntil: '2026-10-26T18:00:00+08:00', cpblGames: [{date:'2026-10-25'}, {date:'2026-10-26'}, {date:'2026-10-27'}] };
test('Taiwan today filters yesterday and retains today/future', () => assert.deepEqual(cpblView(feed, now).games.map(g=>g.date), ['2026-10-26','2026-10-27']));
test('failure, legacy feed, expiry and future timestamps hide all games', () => {
  for (const patch of [{cpblSyncError:'failed'}, {cpblDataMode:'reviewed'}, {cpblAsOfDate:undefined}, {cpblLastSuccessAt:'2026-10-26T17:00:00+08:00'}, {cpblValidUntil:'2026-10-26T15:59:00+08:00'}]) assert.equal(cpblView({...feed,...patch},now).games.length,0);
});
test('Taiwan midnight invalidates yesterday even within 3 hours', () => assert.equal(cpblView({...feed,cpblLastSuccessAt:'2026-10-26T23:59:00+08:00',cpblValidUntil:'2026-10-27T02:59:00+08:00'},Date.parse('2026-10-27T00:01:00+08:00')).current,false));
test('verified empty schedule distinct from unknown', () => assert.deepEqual(cpblView({...feed,cpblGames:[]},now),{current:true,games:[]}));
