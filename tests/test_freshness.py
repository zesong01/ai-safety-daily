import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_freshness import expected_window_end, is_current, needs_update


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 16, 3, tzinfo=timezone.utc)
        self.data = {
            'issues': [{'date': '2026-10-16', 'articles': []}],
            'collection': {'windowEnd': '2026-10-16T09:00:00+08:00',
                           'sources': [{'ok': True}, {'ok': True}]},
        }

    def test_published_empty_issue_is_valid(self):
        self.assertTrue(is_current(self.data, self.now))

    def test_yesterday_and_future_window_need_recovery(self):
        for date in ('2026-10-15', '2026-10-17'):
            self.data['collection']['windowEnd'] = date + 'T09:00:00+08:00'
            self.assertFalse(is_current(self.data, self.now))

    def test_missing_issue_or_insufficient_sources_need_recovery(self):
        self.data['issues'] = []
        self.assertFalse(is_current(self.data, self.now))
        self.data['issues'] = [{'date': '2026-10-16'}]
        self.data['collection']['sources'][1]['ok'] = False
        self.assertFalse(is_current(self.data, self.now))

    def test_invalid_payload_needs_recovery(self):
        for data in ({}, None, {'collection': None}):
            self.assertFalse(is_current(data, self.now))

    def test_nine_am_boundary(self):
        before = datetime(2026, 10, 16, 0, 59, tzinfo=timezone.utc)
        at = datetime(2026, 10, 16, 1, tzinfo=timezone.utc)
        self.assertEqual(expected_window_end(before).date().isoformat(), '2026-10-15')
        self.assertEqual(expected_window_end(at).date().isoformat(), '2026-10-16')

    @patch('check_freshness.urlopen', side_effect=TimeoutError('timeout'))
    def test_unreachable_site_does_not_skip_retry(self, _):
        self.assertTrue(needs_update(self.now))
