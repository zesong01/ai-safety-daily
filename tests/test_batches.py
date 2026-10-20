import sys
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect import collect_batches, parse_feed, issue_end, SHANGHAI


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.end = datetime(2026, 10, 19, 9, tzinfo=SHANGHAI)
        self.now = self.end + timedelta(hours=5)

    def article(self, stamp, id='new'):
        return {'id': id, 'title': 'LLM safety research', 'summary': 'Original source excerpt',
                'source': 'arXiv cs.LG', 'tags': ['Safety'], 'topics': ['safety'],
                '_published': stamp.isoformat(), 'links': [{'url': f'https://example.org/{id}'}]}

    def test_afternoon_feed_is_saved_then_published_after_replacement(self):
        # Reproduces the live 19 Oct feed: Eastern midnight = Beijing noon.
        raw = b'<rss><channel><item><title>LLM safety research</title><link>https://arxiv.org/abs/2610.22425</link><pubDate>Mon, 19 Oct 2026 00:00:00 -0400</pubDate><announce_type>new</announce_type><description>AI safety alignment research</description></item></channel></rss>'
        items, status = parse_feed(raw, 'arXiv cs.LG', '研究', self.end-timedelta(days=7), self.now)
        data, pending = collect_batches({'issues': []}, items, [], [status], self.end, self.now)
        self.assertEqual(data['issues'][0]['articles'], [])
        self.assertEqual(len(pending), 1)
        pending=json.loads(json.dumps(pending))
        # Tomorrow's RSS no longer has this article, but the saved batch survives.
        tomorrow = self.end + timedelta(days=1)
        data, pending = collect_batches(data, [], pending, [status], tomorrow, tomorrow+timedelta(hours=1))
        self.assertEqual(len(data['issues'][0]['articles']), 1)
        self.assertEqual(data['issues'][0]['date'], '2026-10-20')
        self.assertEqual(pending, [])

    def test_late_article_repairs_its_original_issue_not_today(self):
        stamp = self.end-timedelta(days=2)+timedelta(hours=3)
        data, _ = collect_batches({'issues': []}, [self.article(stamp)], [], [], self.end, self.now)
        issues = {issue['date']: issue for issue in data['issues']}
        self.assertEqual(len(issues['2026-10-18']['articles']), 1)
        self.assertEqual(issues['2026-10-19']['articles'], [])
        self.assertEqual(data['collection']['addedByIssue'], {'2026-10-18': 1})

    def test_boundary_future_and_duplicate_entries(self):
        self.assertEqual(issue_end(self.end), self.end+timedelta(days=1))
        self.assertEqual(issue_end(self.end-timedelta(microseconds=1)), self.end)
        article = self.article(self.end+timedelta(hours=3))
        future = self.article(self.now+timedelta(hours=1), 'future')
        old = self.article(self.end-timedelta(days=8), 'old')
        data, pending = collect_batches({'issues': []}, [article, future, old], [article], [], self.end, self.now)
        self.assertEqual(len(pending), 1)
        data, pending = collect_batches(data, [article], pending, [], self.end, self.now)
        self.assertEqual(data['collection']['newItems'], 0)
        self.assertEqual(len(pending), 1)
