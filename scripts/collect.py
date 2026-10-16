"""Fetch official RSS metadata; no model API, browser session, or secrets required."""
from __future__ import annotations
import argparse
import concurrent.futures
import gzip
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from topics import TOPICS, TOPIC_LIMIT, TOPIC_LABELS, classify, migrate_topics

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'public/data/briefs.json'
SHANGHAI = timezone(timedelta(hours=8))
SOURCES = [
    ('METR', 'https://metr.org/feed.xml', '研究'),
    ('OpenAI', 'https://openai.com/news/rss.xml', '工程'),
    ('Google DeepMind', 'https://deepmind.google/blog/rss.xml', '研究'),
    ('Cisco', 'https://blogs.cisco.com/ai/feed', '工程'),
    ('arXiv cs.AI', 'https://rss.arxiv.org/rss/cs.AI', '研究'),
    ('arXiv cs.CR', 'https://rss.arxiv.org/rss/cs.CR', '研究'),
    ('arXiv cs.MA', 'https://rss.arxiv.org/rss/cs.MA', '研究'),
    ('arXiv cs.LG', 'https://rss.arxiv.org/rss/cs.LG', '研究'),
    ('arXiv stat.ML', 'https://rss.arxiv.org/rss/stat.ML', '研究'),
    ('arXiv cs.CL', 'https://rss.arxiv.org/rss/cs.CL', '研究'),
]
TERMS = {
    'Agent': r'\bagents?\b|\bagentic\b',
    'Alignment': r'\balignment\b|\bmisalign',
    'AI Safety': r'\bsafety\b|\bunsafe\b|\bharmless',
    'AI Security': r'\bsecurity\b|\bcyber',
    'Prompt Injection': r'prompt.injection|\bjailbreak',
    'Evaluation': r'\bevaluation\b|\bbenchmark\b',
    'AI Control': r'\bcontainment\b|\bsandbox\b|runtime.control|\bmonitoring\b',
    'Red Teaming': r'red.team',
}

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip: self.skip-=1
        self.parts.append(' ')
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def plain(value):
    p=TextOnly();p.feed(html.unescape(value or ''))
    return re.sub(r'\s+',' ',''.join(p.parts)).strip()

def canonical(url):
    p=urlsplit(url.strip())
    if p.scheme!='https' or not p.netloc or p.username or p.password: return ''
    path=p.path.rstrip('/')
    if p.netloc.lower()=='arxiv.org': path=re.sub(r'v\d+$','',path)
    return urlunsplit(('https',p.netloc.lower(),path,'',''))

def date_value(value):
    try: d=parsedate_to_datetime(value)
    except (ValueError,TypeError):
        try: d=datetime.fromisoformat(value.replace('Z','+00:00'))
        except (ValueError,TypeError): return None
    # A missing timezone must not silently inherit the machine's local timezone.
    return d if d.tzinfo else None

def field(item,name):
    return next((c.text or '' for c in item if c.tag.split('}')[-1]==name),'')

def parse_feed(raw,name,category,start,end):
    if raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
    root=ET.fromstring(raw)
    if root.tag.split('}')[-1] not in ('rss','RDF','feed'): raise ValueError('Response is not a feed')
    entries=[i for i in root.iter() if i.tag.split('}')[-1] in ('item','entry')]
    results=[]; missing_date=0
    for item in entries:
        title=plain(field(item,'title'));link=field(item,'link')
        if not link: link=next((c.attrib.get('href','') for c in item if c.tag.split('}')[-1]=='link' and c.attrib.get('rel','alternate')=='alternate'),'')
        link=canonical(link)
        if not title or not link: continue
        date=date_value(field(item,'pubDate') or field(item,'published') or field(item,'date'))
        if date is None: missing_date+=1;continue
        if not start<=date<end: continue
        # RSS announces replacements too. Do not turn paper revisions into new papers.
        if name.startswith('arXiv') and field(item,'announce_type') not in ('new','cross'): continue
        description=plain(field(item,'description') or field(item,'summary') or field(item,'encoded'))
        corpus=title+' '+description
        tags=[tag for tag,pattern in TERMS.items() if re.search(pattern,corpus,re.I)]
        topics=classify(corpus,name)
        if not topics: continue
        tags=list(dict.fromkeys([*[TOPIC_LABELS[t] for t in topics], *tags]))
        # Keep the title plus excerpt short; the full source remains at the linked page.
        words=description.split();remaining=max(0,24-len(title.split()))
        excerpt=' '.join(words[:remaining])
        if len(words)>remaining and excerpt:excerpt+='…'
        summary=('原文摘要节选：'+excerpt) if excerpt else '此条为官方 RSS 收录的相关更新，点击原文查看完整内容。'
        stamp=date.astimezone(SHANGHAI)
        limitation='自动采集 RSS 元数据，未人工核验全文；分类来自关键词，不代表安全结论。'
        if name.startswith('arXiv'):limitation+=' 所示时间为 RSS 公告时间，不等于首次投稿时间；预印本不代表同行评审。'
        else:limitation+=' 厂商公告或演示不等于独立验证，也不等于真实事故。'
        results.append({'id':'feed-'+hashlib.sha256(link.encode()).hexdigest()[:16],
            'title':title[:200],'category':category,'topics':topics,'source':name,'publishedDate':stamp.date().isoformat(),
            'importance':3,'summary':summary,'why':'仅自动整理来源，不生成研究判断。',
            'limitations':limitation,'points':[f'RSS 发布时间：{stamp.isoformat()}'],'tags':tags[:6],
            'evidence':'自动采集 · 未人工核验','links':[{'label':'阅读原始来源','url':link}],
            'automatic':True,'_published':date.isoformat()})
    return results,{'name':name,'ok':True,'count':len(entries),'matched':len(results),'missingDate':missing_date}

def fetch_source(source,start,end):
    name,url,category=source
    for attempt in range(2):
        try:
            req=Request(url,headers={'User-Agent':'AI-Safety-Daily/1.0 (+https://github.com/zesong01/ai-safety-daily)','Accept-Encoding':'identity'})
            with urlopen(req,timeout=30) as response:
                raw=response.read(20_000_001)
            if len(raw)>20_000_000:raise ValueError('Feed exceeds size limit')
            return parse_feed(raw,name,category,start,end)
        except Exception as e:
            if attempt==0: time.sleep(2)
            else:return [],{'name':name,'ok':False,'count':0,'error':f'{type(e).__name__}: {str(e)[:180]}'}

def merge(data,articles,statuses,start,end,now):
    migrate_topics(data)
    day=end.astimezone(SHANGHAI).date().isoformat()
    # De-duplicate all historic and current issue links, including imported briefs.
    known={canonical(l['url']):a for i in data['issues'] for a in i['articles'] for l in a['links']}
    fresh=[]
    for article in sorted(articles,key=lambda a:datetime.fromisoformat(a['_published']),reverse=True):
        url=article['links'][0]['url']
        if url in known:
            previous=known[url]
            previous['topics']=list(dict.fromkeys([*previous['topics'],*article['topics']]))
            continue
        cleaned={k:v for k,v in article.items() if k!='_published'}
        known[url]=cleaned;fresh.append(cleaned)
    current=next((i for i in data['issues'] if i['date']==day),None)
    if current is None:
        current={'date':day,'title':f'{day} AI 研究日报',
            'intro':'收录 Safety、Deep Learning、RL 与基座模型研究；保留原文标题与短摘要，不生成中文分析。',
            'window':f'{start.astimezone(SHANGHAI):%Y-%m-%d %H:%M} — {end.astimezone(SHANGHAI):%Y-%m-%d %H:%M}（北京时间；RSS 发布时间）',
            'note':'自动采集不等于人工核验。arXiv 以 RSS 公告时间筛选，不把它称为首次投稿时间。','articles':[], 'automatic':True}
        data['issues'].append(current)
    # Round-robin across sections: a busy ML feed must not crowd out Safety or RL.
    included=[];picked=set()
    counts={topic:sum(topic in a['topics'] for a in current['articles']) for topic in TOPICS}
    queues={topic:iter([a for a in fresh if topic in a['topics']]) for topic in TOPICS}
    while len(current['articles'])+len(included)<TOPIC_LIMIT*len(TOPICS):
        added=False
        for topic in TOPICS:
            if len(current['articles'])+len(included)>=TOPIC_LIMIT*len(TOPICS):break
            if counts[topic]>=TOPIC_LIMIT:continue
            candidate=next((a for a in queues[topic] if a['id'] not in picked),None)
            if candidate is None:continue
            included.append(candidate);picked.add(candidate['id']);added=True
            for membership in candidate['topics']:counts[membership]+=1
        if not added:break
    # Keep the RSS ordering after selection; articles shared by sections appear once.
    included=[a for a in fresh if a['id'] in picked]
    current['articles'].extend(included)
    current['updatedAt']=now.isoformat()
    if current.get('automatic'):
        current['title']=f'{day} AI 研究日报'
        current['intro']='收录 Safety、Deep Learning、RL 与基座模型研究；保留原文标题与短摘要，不生成中文分析。'
    if not current.get('automatic') and '自动采集补充' not in current['note']:
        current['note']+=' 自动采集补充按每日北京时间 09:00 截止的 24 小时 RSS 公告窗口筛选，未经人工核验。'
    if not current['articles']:current['intro']='本窗口未收录到符合筛选条件的新增条目；这不代表全球没有相关进展。'
    data['issues'].sort(key=lambda i:i['date'],reverse=True)
    data['schedule']={'enabled':True,'time':'09:00','timezone':'Asia/Shanghai','mode':'feeds','verified':True}
    data['collection']={'completedAt':now.isoformat(),'windowStart':start.isoformat(),'windowEnd':end.isoformat(),'sources':statuses,'newItems':len(included),'omittedForLimit':len(fresh)-len(included),'mode':'rss'}
    return data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');parser.add_argument('--date');args=parser.parse_args()
    now=datetime.now(timezone.utc)
    end=datetime.fromisoformat(args.date).replace(hour=9,tzinfo=SHANGHAI) if args.date else now.astimezone(SHANGHAI).replace(hour=9,minute=0,second=0,microsecond=0)
    if not args.date and end>now:end-=timedelta(days=1)
    start=end-timedelta(days=1)
    data=json.loads(DATA.read_text(encoding='utf-8-sig'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda s:fetch_source(s,start,end),SOURCES))
    articles=[a for result,_ in results for a in result];statuses=[s for _,s in results]
    print(json.dumps({'windowStart':start.isoformat(),'windowEnd':end.isoformat(),'sources':statuses},ensure_ascii=False))
    if sum(s['ok'] for s in statuses)<2:raise SystemExit('Too few sources available; preserving the last published data.')
    merged=merge(data,articles,statuses,start,end,now)
    print(json.dumps({'newItems':merged['collection']['newItems'],'issues':len(merged['issues']),'dryRun':args.dry_run},ensure_ascii=False))
    if not args.dry_run:
        temp=DATA.with_suffix('.tmp');temp.write_text(json.dumps(merged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(DATA)

if __name__=='__main__':main()
