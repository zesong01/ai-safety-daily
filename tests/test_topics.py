import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect import merge, parse_feed
from topics import TOPICS, classify, migrate_topics


class TopicTests(unittest.TestCase):
    def setUp(self):
        self.end = datetime(2026, 10, 16, 1, tzinfo=timezone.utc)
        self.start = self.end - timedelta(days=1)

    def test_research_sections_and_overlap(self):
        self.assertEqual(classify('Deep learning with neural networks'), ['deep-learning'])
        self.assertEqual(classify('Reinforcement learning with policy gradients'), ['rl'])
        self.assertEqual(classify('Scaling laws for pretraining large language models'), ['foundation-models'])
        self.assertEqual(set(classify('LLM safety alignment with RLHF')), {'safety', 'rl', 'foundation-models'})
        self.assertEqual(classify('Building security and staff monitoring'), [])

    def test_full_abstract_classifies_beyond_short_excerpt(self):
        raw = ('<rss><channel><item><title>A new optimization method</title>'
               '<link>https://arxiv.org/abs/2610.00001</link>'
               '<pubDate>Thu, 15 Oct 2026 03:00:00 GMT</pubDate><announce_type>new</announce_type>'
               '<description>' + 'Introduction. ' * 35 + 'Reinforcement learning with neural networks.'
               '</description></item></channel></rss>').encode()
        items, _ = parse_feed(raw, 'arXiv cs.LG', '研究', self.start, self.end)
        self.assertEqual(set(items[0]['topics']), {'rl', 'deep-learning'})

    def article(self, topic, index):
        return {'id': f'{topic}-{index}', 'topics': [topic],
                'links': [{'url': f'https://example.org/{topic}/{index}'}],
                '_published': self.start.isoformat()}

    def test_each_section_gets_capacity_and_reruns_do_not_duplicate(self):
        candidates = [self.article(topic, i) for topic in TOPICS for i in range(45)]
        result = merge({'issues': []}, candidates, [], self.start, self.end, self.end)
        self.assertEqual(len(result['issues'][0]['articles']), 120)
        for topic in TOPICS:
            self.assertEqual(sum(topic in a['topics'] for a in result['issues'][0]['articles']), 30)
        result = merge(result, candidates, [], self.start, self.end, self.end)
        self.assertEqual(result['collection']['newItems'], 0)
        self.assertEqual(len(result['issues'][0]['articles']), 120)

    def test_cross_listed_article_merges_topics_without_duplicate(self):
        first = self.article('rl', 1)
        second = copy.deepcopy(first)
        second['topics'] = ['foundation-models']
        result = merge({'issues': []}, [first, second], [], self.start, self.end, self.end)
        self.assertEqual(len(result['issues'][0]['articles']), 1)
        self.assertEqual(set(result['issues'][0]['articles'][0]['topics']), {'rl', 'foundation-models'})

    def test_migration_keeps_original_safety_membership_and_known_topics(self):
        old = {'title': 'Agent execution controls', 'summary': 'Original brief', 'tags': [], 'source': 'Test'}
        new = {'topics': ['rl']}
        result = migrate_topics({'issues': [{'articles': [old, new]}]})
        self.assertEqual(result['issues'][0]['articles'][0]['topics'], ['safety'])
        self.assertEqual(new['topics'], ['rl'])
