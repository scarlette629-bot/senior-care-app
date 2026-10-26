import test from 'node:test';
import assert from 'node:assert/strict';
import { freshSeries } from '../src/seriesFeed.js';
const now=Date.parse('2026-10-26T17:00:00+08:00');
test('automatic titles expire after seven days while manual titles remain',()=>{
 assert.equal(freshSeries({autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00'},now),true);
 for(const verifiedAt of [undefined,'bad','2026-10-18T16:00:00+08:00','2026-10-27T16:00:00+08:00'])assert.equal(freshSeries({autoDiscovered:true,verifiedAt},now),false);
 assert.equal(freshSeries({},now),true);
});
