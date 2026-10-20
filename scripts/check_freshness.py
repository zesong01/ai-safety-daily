"""Skip duplicate checks briefly; an empty published issue never stops polling."""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

SITE_DATA = 'https://zesong01.github.io/ai-safety-daily/data/briefs.json'
SHANGHAI = timezone(timedelta(hours=8))


def expected_window_end(now):
    end = now.astimezone(SHANGHAI).replace(hour=9, minute=0, second=0, microsecond=0)
    return end if end <= now else end - timedelta(days=1)


def is_current(data, now):
    try:
        expected = expected_window_end(now)
        collection = data['collection']
        return (
            datetime.fromisoformat(collection['windowEnd']) == expected
            and collection.get('collectorVersion') == 2
            and timedelta(0) <= now-datetime.fromisoformat(collection['completedAt']) < timedelta(minutes=50)
            and any(issue['date'] == expected.date().isoformat() for issue in data['issues'])
            and sum(source.get('ok') is True for source in collection['sources']) >= 2
        )
    except (KeyError, TypeError, ValueError):
        return False


def needs_update(now):
    try:
        request = Request(f'{SITE_DATA}?freshness={time.time_ns()}', headers={
            'Cache-Control': 'no-cache', 'User-Agent': 'ai-safety-daily-freshness/1.0',
        })
        with urlopen(request, timeout=30) as response:
            return not is_current(json.load(response), now)
    except Exception as error:
        # A failed deployment or unavailable public endpoint must not suppress recovery.
        print(f'Public freshness check unavailable; retry collection and deployment: {error}')
        return True


def main():
    required = needs_update(datetime.now(timezone.utc))
    print('Public issue is missing/stale; updating.' if required else 'Public issue is current; skipping.')
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a', encoding='utf-8') as handle:
            handle.write(f'needed={str(required).lower()}\n')


if __name__ == '__main__':
    main()
