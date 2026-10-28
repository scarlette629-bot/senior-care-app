import test from 'node:test';
import assert from 'node:assert/strict';
import { freshSeries } from '../src/seriesFeed.js';
const now=Date.parse('2026-10-26T17:00:00+08:00');
test('automatic titles expire after seven days while manual titles remain',()=>{
 assert.equal(freshSeries({autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00',releasePrecision:'day',releaseDate:'2026-10-18',releaseSourceUrl:'https://example.com/release'},now),true);
 for(const verifiedAt of [undefined,'bad','2026-10-18T16:00:00+08:00','2026-10-27T16:00:00+08:00'])assert.equal(freshSeries({autoDiscovered:true,verifiedAt},now),false);
 assert.equal(freshSeries({},now),true);
});
import { selectDailySeries } from '../src/seriesFeed.js';
const feed={recommendations:[{id:'tw',title:'新手上路',type:'台劇',platform:'Netflix',description:'synopsis',verified:true,autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00',releasePrecision:'day',releaseDate:'2026-10-18',releaseSourceUrl:'https://example.com/release'},{id:'kr',title:'韓劇新片',type:'韓劇',platform:'Netflix',description:'synopsis',verified:true,autoDiscovered:true,verifiedAt:'2026-10-26T16:00:00+08:00',releasePrecision:'day',releaseDate:'2026-10-18',releaseSourceUrl:'https://example.com/release'}]};
test('no drama interest means no recommendations or candidates even with all filter',()=>{
 for(const interests of [[],['棒球'],['棒球','籃球']]){
  const result=selectDailySeries(feed,'all',interests,now);
  assert.equal(result.all.length,0);assert.equal(result.items.length,0);assert.equal(result.candidates.length,0);
 }
});
test('single and multiple interests are a strict boundary for every filter',()=>{
 assert.equal(selectDailySeries(feed,'mine',['陸劇'],now).items.length,0);
 assert.deepEqual(selectDailySeries(feed,'mine',['台劇'],now).items.map(x=>x.type),['台劇']);
 assert.deepEqual(selectDailySeries(feed,'韓劇',['台劇'],now).items.map(x=>x.type),['台劇']);
 assert.equal(selectDailySeries(feed,'mine',['台劇','韓劇'],now).items.length,2);
 assert.deepEqual(selectDailySeries(feed,'韓劇',['台劇','韓劇'],now).items.map(x=>x.type),['韓劇']);
 const data={...feed,seriesDiscovery:{candidates:[{title:'陸劇線索',type:'陸劇',sourceUrl:'https://example.com/news',publishedAt:'2026-10-26T16:00:00+08:00'},{title:'台劇線索',type:'台劇',sourceUrl:'https://example.com/news',publishedAt:'2026-10-26T16:00:00+08:00'}]}};
 assert.deepEqual(selectDailySeries(data,'all',['陸劇'],now).candidates.map(x=>x.type),['陸劇']);
});
test('current-year manual titles join the unified list and title duplicates/news are removed',()=>{
 const data={recommendations:[...feed.recommendations,{id:'manual',title:'陸劇作品',type:'陸劇',platform:'愛奇藝',description:'synopsis',verified:true,releasePrecision:'day',releaseDate:'2026-10-19',releaseSourceUrl:'https://example.com/release'},{...feed.recommendations[0],id:'duplicate',platform:'其他平台'},{id:'old',title:'往年作品',type:'台劇',platform:'Netflix',description:'synopsis',verified:true,releaseDate:'2025-10-01'}],seriesDiscovery:{candidates:[{title:'新手上路',type:'台劇',sourceUrl:'https://example.com/news',publishedAt:'2026-10-26T16:00:00+08:00'},{title:'新片線索',type:'陸劇',sourceUrl:'https://example.com/news',publishedAt:'2026-10-26T16:00:00+08:00'}]}};
 const result=selectDailySeries(data,'mine',['台劇','韓劇','陸劇'],now);
 assert.equal(result.items.length,3);assert.equal(result.items.filter(x=>x.title==='新手上路').length,1);
 assert.equal(selectDailySeries(data,'陸劇',['陸劇'],now).items.length,1);
 assert.deepEqual(result.candidates.map(x=>x.title),['新片線索']);
});

import {recentPremiere,currentWeeklyHot} from '../src/seriesFeed.js';
test('new means a sourced premiere in last 30 days, not this year or a fresh check',()=>{
 const base={releasePrecision:'day',releaseDate:'2026-10-16',releaseSourceUrl:'https://example.com/evidence'};
 assert.equal(recentPremiere(base,now),true);
 for(const patch of [{releaseDate:'2026-02-06'},{releaseDate:'2026-09-26'},{releaseDate:'2026-10-27'},{releaseDate:'2026-02-31'},{releasePrecision:'year'},{releaseSourceUrl:undefined}])assert.equal(recentPremiere({...base,...patch},now),false);
 assert.equal(recentPremiere({...base,releaseDate:'2026-09-27'},now),true);
});
test('weekly topics reject prior week, future reports and unrelated interests',()=>{
 const hot={weekStart:'2026-10-26',weekEnd:'2026-11-01',items:[{title:'current',type:'陸劇',sourceUrl:'https://example.com',observedAt:'2026-10-26T16:00:00+08:00'},{title:'old',type:'陸劇',sourceUrl:'https://example.com',observedAt:'2026-10-25T16:00:00+08:00'},{title:'future',type:'陸劇',sourceUrl:'https://example.com',observedAt:'2026-10-27T16:00:00+08:00'},{title:'other',type:'台劇',sourceUrl:'https://example.com',observedAt:'2026-10-26T16:00:00+08:00'}]};
 assert.deepEqual(currentWeeklyHot({weeklyHot:hot},['陸劇'],now).map(x=>x.title),['current']);
 assert.deepEqual(currentWeeklyHot({weeklyHot:{...hot,weekStart:'2026-10-19',weekEnd:'2026-10-25'}},['陸劇'],now),[]);
});

import {dailySeriesEligible} from '../src/seriesFeed.js';
test('unknown dates remain visible while known old and future releases are excluded',()=>{
 assert.equal(dailySeriesEligible({releasePrecision:'year',catalogueYear:2026},now),true);
 assert.equal(dailySeriesEligible({},now),true);
 assert.equal(dailySeriesEligible({releaseDate:'2026-09-26'},now),false);
 assert.equal(dailySeriesEligible({releaseDate:'2026-09-27'},now),true);
 assert.equal(dailySeriesEligible({catalogueYear:2025},now),false);
 assert.equal(dailySeriesEligible({releaseDate:'2026-10-27'},now),false);
 assert.equal(dailySeriesEligible({type:'綜藝',releaseDate:'2026-01-01',latestEpisodeDate:'2026-10-25'},now),true);
 assert.equal(dailySeriesEligible({type:'綜藝',latestEpisodeDate:'2026-09-01'},now),false);
 const unknown={id:'jp',title:'日劇日期待確認',type:'日劇',platform:'Netflix',description:'official',verified:true};
 assert.equal(selectDailySeries({recommendations:[unknown]},'mine',['日劇'],now).items.length,1);
 assert.equal(selectDailySeries({recommendations:[unknown]},'mine',['棒球'],now).items.length,0);
});

test('connect both candidate feeds, correct mixed-article category, keep 30 days and deduplicate verified works',()=>{
 const now=Date.parse('2026-10-28T12:00:00+08:00');
 const data={recommendations:[{title:'嫁金釵',type:'陸劇',platform:'Netflix',description:'official',verified:true,releaseDate:'2026-10-16'}],
 seriesDiscovery:{candidates:[{title:'尚公主',type:'台劇',publishedAt:'2026-10-23T12:00:00+08:00',sourceUrl:'https://example.com/news'}]},
 chinaDramaNewTitles:{items:[{title:'尚公主',publishedAt:'2026-10-23T15:00:00+08:00',sourceUrl:'https://example.com/new'},{title:'嫁金釵',publishedAt:'2026-10-23T15:00:00+08:00',sourceUrl:'https://example.com/new'},{title:'過期線索',publishedAt:'2026-09-01T15:00:00+08:00',sourceUrl:'https://example.com/old'}]}};
 const result=selectDailySeries(data,'mine',['陸劇'],now);
 assert.deepEqual(result.items.map(x=>x.title),['嫁金釵']);
 assert.deepEqual(result.candidates.map(x=>[x.title,x.type]),[['尚公主','陸劇']]);
 assert.equal(selectDailySeries(data,'mine',['台劇'],now).candidates.length,0);
 assert.equal(selectDailySeries(data,'mine',[],now).candidates.length,0);
});
