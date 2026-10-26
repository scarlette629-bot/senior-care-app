import datetime as dt
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('weekly',Path(__file__).resolve().parents[1]/'scripts/weekly_hot.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
NOW=dt.datetime(2026,10,26,20,tzinfo=w.TZ)
def rss():
 return '<rss><channel><item><title>本週陸劇熱播</title><link>https://example.com/current</link><pubDate>Mon, 26 Oct 2026 02:00:00 GMT</pubDate><source>來源</source></item><item><title>上週</title><link>https://example.com/old</link><pubDate>Sun, 25 Oct 2026 02:00:00 GMT</pubDate></item></channel></rss>'
class Tests(unittest.TestCase):
 def test_only_current_week_and_success_timestamp(self):
  x=w.refresh({},NOW,lambda url:rss());self.assertEqual(x['status'],'success');self.assertEqual(len(x['items']),1);self.assertEqual(x['items'][0]['title'],'本週陸劇熱播');self.assertEqual(x['weekStart'],'2026-10-26')
 def test_failure_does_not_recycle_last_week_or_advance_success(self):
  def fail(url):raise OSError('timeout')
  old={'lastSuccessfulAt':'old','items':[{'type':'陸劇','observedAt':'2026-10-25T10:00:00+08:00','sourceUrl':'https://example.com'}]}
  x=w.refresh(old,NOW,fail);self.assertEqual(x['items'],[]);self.assertEqual(x['status'],'failed');self.assertEqual(x['lastSuccessfulAt'],'old')
 def test_empty_success_differs_from_failure(self):
  x=w.refresh({},NOW,lambda url:'<rss><channel/></rss>');self.assertEqual(x['status'],'success');self.assertEqual(x['items'],[])
