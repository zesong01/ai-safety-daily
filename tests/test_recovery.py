import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from recover_arxiv import parse_listing


class RecoveryTests(unittest.TestCase):
    def test_only_requested_date_with_provenance_and_no_invented_abstract(self):
        page = '''<h3>Fri, 16 Oct 2026 (showing 2 of 2 entries)</h3>
        <dt><a href="/abs/2610.12345">arXiv:2610.12345</a></dt><dd><div class='list-title mathjax'><span>Title:</span> Reinforcement Learning for LLM Safety</div></dd>
        <dt><a href="/abs/2610.12346v2">arXiv:2610.12346v2</a></dt><dd><div class='list-title mathjax'><span>Title:</span> LLM safety replacement</div></dd>
        <h3>Mon, 19 Oct 2026 (showing 1 of 1 entries)</h3>
        <dt><a href="/abs/2610.12347">arXiv:2610.12347</a></dt><dd><div class='list-title mathjax'><span>Title:</span> LLM safety</div></dd>'''
        items = parse_listing(page, {'2026-10-16'}, 'arXiv cs.LG', 'https://arxiv.org/list/cs.LG/recent')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['publishedDate'], '2026-10-16')
        self.assertIn('未补采摘要', items[0]['summary'])
        self.assertIn('仅日期', items[0]['points'][0])
