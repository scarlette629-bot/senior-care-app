import test from 'node:test';
import assert from 'node:assert/strict';
import { freshSeries } from '../src/seriesFeed.js';
const now=Date.parse('2026-10-26T17:00:00+08:00');
test('automatic titles expire after seven days while manual titles remain',()=>{
 assert.equal(freshSeries({autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00'},now),true);
 for(const verifiedAt of [undefined,'bad','2026-10-18T16:00:00+08:00','2026-10-27T16:00:00+08:00'])assert.equal(freshSeries({autoDiscovered:true,verifiedAt},now),false);
 assert.equal(freshSeries({},now),true);
});
import { selectDailySeries } from '../src/seriesFeed.js';
const feed={recommendations:[{id:'tw',title:'新手上路',type:'台劇',platform:'Netflix',description:'synopsis',verified:true,autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00'},{id:'kr',title:'韓劇新片',type:'韓劇',platform:'Netflix',description:'synopsis',verified:true,autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00'}]};
test('default daily list shows all new titles for no interests, sports only, and empty-category interests',()=>{
 for(const interests of [[],['棒球'],['陸劇']])assert.equal(selectDailySeries(feed,'all',interests,now).items.length,2);
});
test('explicit category filters preserve valid empty states and can return to all titles',()=>{
 assert.equal(selectDailySeries(feed,'陸劇',['陸劇'],now).items.length,0);
 assert.equal(selectDailySeries(feed,'mine',['台劇'],now).items[0].title,'新手上路');
 assert.equal(selectDailySeries(feed,'all',['陸劇'],now).items.length,2);
});
