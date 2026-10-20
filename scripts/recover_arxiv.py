"""One-off recovery of titles/dates from arXiv's official recent listing.

Does not invent abstracts or claim the original RSS publication time was recovered.
"""
import argparse
import hashlib
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

from collect import DATA, SHANGHAI, canonical, merge, plain, save_json
from topics import classify, TOPIC_LABELS
import json


def parse_listing(text, wanted, source, listing_url):
    day=None;articles=[]
    for match in re.finditer(r'<h3\b[^>]*>(.*?)</h3>|<dt\b[^>]*>(.*?)</dt>\s*<dd\b[^>]*>(.*?)</dd>', text, re.S):
        if match.group(1) is not None:
            stamp=re.search(r'\b\w{3}, (\d{1,2} \w{3} \d{4})', plain(match.group(1)))
            day=datetime.strptime(stamp[1], '%d %b %Y').date().isoformat() if stamp else None
            continue
        if day not in wanted:continue
        dt,dd=match.group(2),match.group(3)
        link=re.search(r'href\s*=\s*[\'\"](/abs/[^\'\"]+)', dt)
        title=re.search(r'<div\b[^>]*class=[\'\"][^\'\"]*list-title[^\'\"]*[\'\"][^>]*>(.*?)</div>', dd, re.S)
        revision=re.search(r'v(\d+)\b', plain(dt))
        if not link or not title or (revision and int(revision[1])>1) or re.search(r'replac', plain(dt), re.I):continue
        url=canonical('https://arxiv.org'+link[1]);title=plain(title[1]).removeprefix('Title:').strip()
        topics=classify(title,source)
        if not topics:continue
        articles.append({'id':'feed-'+hashlib.sha256(url.encode()).hexdigest()[:16],
            'title':title[:200],'category':'研究','topics':topics,'source':source,'publishedDate':day,
            'importance':3,'summary':'从 arXiv 官方历史列表补采的标题与链接；未补采摘要，请打开原文阅读。',
            'why':'仅自动整理来源，不生成研究判断。','limitations':'历史补采，仅有官方列表标题及公告日期；未恢复原 RSS 时间或摘要。关键词分类未经人工核验，预印本不代表同行评审。',
            'points':[f'arXiv 官方列表公告日期：{day}（仅日期）'],
            'tags':[TOPIC_LABELS[t] for t in topics],'evidence':'自动采集 · 未人工核验',
            'links':[{'label':'阅读论文原文','url':url},{'label':'arXiv 官方列表（滚动更新）','url':listing_url}],
            'automatic':True,
            # Sorting only. No synthetic timestamp is written to the published article.
            '_published':day+'T12:00:00+08:00'})
    return articles


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--announcement-date',action='append',required=True)
    args=parser.parse_args();now=datetime.now(timezone.utc)
    data=json.loads(DATA.read_text(encoding='utf-8-sig'));batches={day:[] for day in args.announcement_date}
    for category in ('cs.AI','cs.CR','cs.MA','cs.LG','stat.ML','cs.CL'):
        url=f'https://arxiv.org/list/{category}/recent?skip=0&show=2000'
        with urlopen(Request(url,headers={'User-Agent':'AI-Safety-Daily/1.0 (historical recovery)'}),timeout=30) as response:
            articles=parse_listing(response.read(20_000_000).decode('utf-8'),batches,'arXiv '+category,url)
        for article in articles:batches[article['publishedDate']].append(article)
        print(category,len(articles));time.sleep(3)
    collection=data.get('collection',{}).copy()
    for day,batch in sorted(batches.items()):
        end=datetime.fromisoformat(day).replace(hour=9,tzinfo=SHANGHAI)+timedelta(days=1)
        merge(data,batch,[],end-timedelta(days=1),end,now)
        added=data['collection']['newItems']
        print('Recovered',end.date().isoformat(),added)
        if added:
            issue=next(i for i in data['issues'] if i['date']==end.date().isoformat())
            note=' 已从 arXiv 官方历史列表补采标题和公告日期；这些补采条目未恢复摘要或原 RSS 时间。'
            if note not in issue['note']:issue['note']+=note
    data['collection']=collection
    save_json(DATA,data)


if __name__=='__main__':main()
