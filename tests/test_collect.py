import sys
import unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import parse_feed,canonical,merge

class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.start=datetime(2026,10,14,1,tzinfo=timezone.utc)
        self.end=self.start+timedelta(days=1)
    def feed(self,date,link='https://example.org/paper/',extra=''):
        return f'<rss><channel><item><title>Agent safety research</title><link>{link}</link><pubDate>{date}</pubDate><description>AI agents and prompt injection security.</description>{extra}</item></channel></rss>'.encode()
    def test_window_boundaries(self):
        self.assertEqual(len(parse_feed(self.feed('Wed, 14 Oct 2026 01:00:00 GMT'),'Test','研究',self.start,self.end)[0]),1)
        self.assertEqual(len(parse_feed(self.feed('Thu, 15 Oct 2026 01:00:00 GMT'),'Test','研究',self.start,self.end)[0]),0)
    def test_unknown_date_not_new(self):
        items,status=parse_feed(self.feed('unknown'),'Test','研究',self.start,self.end)
        self.assertEqual(items,[]);self.assertEqual(status['missingDate'],1)
    def test_unsafe_link_rejected(self):
        self.assertEqual(canonical('javascript:alert(1)'),'')
        self.assertEqual(canonical('https://arxiv.org/abs/2610.12345v2?x=1'),'https://arxiv.org/abs/2610.12345')
    def test_arxiv_replacement_not_new(self):
        items,_=parse_feed(self.feed('Wed, 14 Oct 2026 02:00:00 GMT',extra='<announce_type>replace</announce_type>'),'arXiv cs.AI','研究',self.start,self.end)
        self.assertEqual(items,[])
    def test_idempotence_and_history(self):
        items,status=parse_feed(self.feed('Wed, 14 Oct 2026 02:00:00 GMT'),'Test','研究',self.start,self.end)
        old={'date':'2026-10-14','articles':[]}
        data=merge({'issues':[old]},items,[status],self.start,self.end,self.end)
        self.assertEqual(len(data['issues']),2)
        data=merge(data,items,[status],self.start,self.end,self.end)
        self.assertEqual(len(data['issues'][0]['articles']),1);self.assertEqual(data['collection']['newItems'],0)
        self.assertIs(data['issues'][1],old)

if __name__=='__main__':unittest.main()
