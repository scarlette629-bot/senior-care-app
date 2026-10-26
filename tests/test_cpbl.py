import datetime as dt
import importlib.util
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('cpbl', Path(__file__).resolve().parents[1] / 'scripts/cpbl.py')
cpbl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpbl)


def fixture(date='2026-10-26T15:05:00', kind='C', status='SCHEDULED'):
    return {'GameId': '2026-C-6', 'KindCode': kind, 'PreExeDate': date, 'Visiting': {'Team': {'Name': '中信兄弟'}}, 'Home': {'Team': {'Name': '味全龍'}}, 'Field': {'Abbe': '大巨蛋'}, 'GameStatus': status}


class ScheduleTests(unittest.TestCase):
    now = dt.datetime(2026, 10, 26, 16, tzinfo=cpbl.TZ)

    def loader(self, rows):
        def load(url):
            return {'Data': {'Games': rows if 'kindCode=C&year=2026&month=10' in url else []}}
        return load

    def test_official_time_and_no_yesterday_or_rescheduled_duplicate(self):
        rows = [fixture('2026-10-25T17:05:00', status='POSTPONED'), fixture(), fixture('2026-10-27T18:35:00')]
        games = cpbl.fetch_games(self.now, self.loader(rows))
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['date'], '2026-10-27')
        game = cpbl.fetch_games(self.now, self.loader([fixture()]))[0]
        self.assertEqual(game['timeTW'], '15:05')
        self.assertEqual(game['match'], '中信兄弟（客） vs 味全龍（主）')

    def test_failure_never_republishes_old_or_advances_success(self):
        def fail(url): raise OSError('HTTP 404')
        result = cpbl.refresh({'cpblGames': [fixture()], 'cpblLastSuccessAt': 'old'}, self.now, fail)
        self.assertEqual(result['cpblGames'], [])
        self.assertEqual(result['cpblLastSuccessAt'], 'old')
        self.assertEqual(result['cpblDataMode'], 'unavailable')
        self.assertIsNone(result['cpblValidUntil'])

    def test_empty_success_is_success_not_fallback(self):
        result = cpbl.refresh({}, self.now, self.loader([]))
        self.assertEqual(result['cpblGames'], [])
        self.assertEqual(result['cpblDataMode'], 'official')
        self.assertIsNone(result['cpblSyncError'])

    def test_partial_category_failure_and_malformed_rows_fail_closed(self):
        for payload in ({}, {'Data': {'Games': None}}, {'Data': {'Games': [{}]}}):
            result = cpbl.refresh({}, self.now, lambda url: payload)
            self.assertEqual(result['cpblDataMode'], 'unavailable')
            self.assertEqual(result['cpblGames'], [])

    def test_cross_year_queries_and_utc_conversion(self):
        urls = []
        def load(url):
            urls.append(url)
            return {'Data': {'Games': []}}
        cpbl.fetch_games(dt.datetime(2026,12,31,23,tzinfo=cpbl.TZ), load)
        self.assertEqual(len(urls), 6)
        self.assertTrue(any('year=2027&month=1' in u for u in urls))
        games = cpbl.fetch_games(self.now, self.loader([fixture('2026-10-26T07:05:00+00:00')]))
        self.assertEqual(games[0]['timeTW'], '15:05')


if __name__ == '__main__': unittest.main()
