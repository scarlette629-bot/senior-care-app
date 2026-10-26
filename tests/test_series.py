import datetime as dt
import importlib.util
import json
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('series',Path(__file__).resolve().parents[1]/'scripts/discover_series.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
NOW=dt.datetime(2026,10,26,17,tzinfo=s.TZ)

def page(kind='Show', available=True, year=2026):
    data={'models':{'nmTitleGQL':{'data':{'metaData':{'videoId':83124329,'type':kind,'isAvailable':available},'copy':{'title':'新手上路','synopsis':'一位新手媽媽因寶寶遭挾持，與意想不到的夥伴一起展開救援任務。'},'persons':{'actors':[{'name':'陳意涵'}]}}}}}
    return '<script>netflix.reactContext = '+json.dumps(data)+';</script><li>'+str(year)+'</li><h4>類型</h4><span>台灣、喜劇節目和奇幻節目</span>'

class SeriesTests(unittest.TestCase):
    def test_official_title_fields(self):
        item=s.parse_official(page(),'83124329',NOW)
        self.assertEqual(item['title'],'新手上路');self.assertEqual(item['type'],'台劇')
        self.assertTrue(item['verified']);self.assertEqual(item['releasePrecision'],'year')
        self.assertNotIn('releaseDate',item)
    def test_scans_latest_and_leading_rows_not_old_catalogue(self):
        html='<div data-uia="locp-collections-title-row"><h2>接下來就看這部</h2><a href="https://www.netflix.com/tw/title/1">A</a></div><div data-uia="locp-collections-title-row"><h2>Netflix 最新作品</h2><a href="https://www.netflix.com/tw/title/2">B</a></div><div data-uia="locp-collections-title-row"><h2>經典舊片</h2><a href="https://www.netflix.com/tw/title/3">C</a></div>'
        self.assertEqual(s.official_ids(html),['1','2'])

    def test_movies_unavailable_old_titles_not_added(self):
        for html in [page(kind='Movie'),page(available=False),page(year=2023)]:
            self.assertIsNone(s.parse_official(html,'83124329',NOW))
    def test_cloud_region_unavailability_does_not_override_taiwan_catalogue(self):
        self.assertIsNone(s.parse_official(page(available=False),'83124329',NOW))
        item=s.parse_official(page(available=False),'83124329',NOW,listed_in_taiwan=True)
        self.assertEqual(item['title'],'新手上路')
        self.assertFalse(item['platformAvailabilityVerified'])
        self.assertEqual(item['releaseStatus'],'catalogue-listed')
        self.assertIsNone(s.parse_official(page(kind='Movie',available=False),'83124329',NOW,listed_in_taiwan=True))

    def test_release_evidence_requires_same_title_and_carries_date_source(self):
        item=s.parse_official(page(),'83124329',NOW)
        evidence={'title':'新手上路','releaseDate':'2026-10-18','releaseSourceUrl':'https://example.com/date'}
        self.assertEqual(s.apply_release_evidence(item,evidence)['releasePrecision'],'day')
        self.assertEqual(s.apply_release_evidence(item,{**evidence,'title':'別部作品'})['releasePrecision'],'year')

    def test_wrong_title_and_changed_layout_fail(self):
        for html,title_id in [(page(),'999'),('<html>blocked</html>','83124329')]:
            with self.assertRaises((ValueError,KeyError)):s.parse_official(html,title_id,NOW)
        with self.assertRaises(ValueError):s.official_ids('blocked')
    def test_success_empty_is_not_source_failure(self):
        def load(url):
            if '/browse/' in url:return '<a href="https://www.netflix.com/tw/title/83124329">title</a>'
            if '/title/' in url:return page(kind='Movie')
            return '<rss><channel></channel></rss>'
        result=s.discover({},NOW,load)
        self.assertEqual(result['status'],'success');self.assertEqual(result['verified'],[])
    def test_discovered_title_automatically_enters_recommendations(self):
        def load(url):
            if '/browse/' in url:return '<a href="https://www.netflix.com/tw/title/83124329">title</a>'
            if '/title/' in url:return page()
            return '<rss><channel></channel></rss>'
        result=s.discover({},NOW,load)
        feed=s.merge({'recommendations':[]},result,NOW,reviewed=[])
        self.assertEqual([x['title'] for x in feed['recommendations']],['新手上路'])
        self.assertEqual(len(feed['recommendations']),1)
        self.assertEqual(result['status'],'success')

    def test_source_failure_preserves_real_verification_time_then_expires(self):
        old=s.parse_official(page(),'83124329',NOW-dt.timedelta(days=1))
        def fail(url):raise OSError('HTTP 404')
        result=s.discover({'verified':[old]},NOW,fail)
        self.assertEqual(result['status'],'failed');self.assertNotEqual(result.get('lastSuccessfulAt'),NOW.isoformat(timespec='seconds'))
        self.assertEqual(result['verified'][0]['verifiedAt'],old['verifiedAt'])
        result=s.discover({'verified':[old]},NOW+dt.timedelta(days=8),fail)
        self.assertEqual(result['verified'],[])
    def test_merge_deduplicates_and_does_not_lose_manual_or_other_data(self):
        item=s.parse_official(page(),'83124329',NOW)
        feed={'recommendations':[{'title':'新手上路','platform':'Netflix','id':'manual'}],'cpblGames':[{'id':'keep'}]}
        out=s.merge(feed,{'verified':[item]},NOW,reviewed=[])
        self.assertEqual(len(out['recommendations']),1);self.assertEqual(out['cpblGames'],[{'id':'keep'}])
        out=s.merge({'recommendations':[]},{'verified':[item]},NOW+dt.timedelta(days=8),reviewed=[])
        self.assertEqual(out['recommendations'],[])

if __name__=='__main__':unittest.main()
