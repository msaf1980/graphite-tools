#!/usr/bin/python3

# Extract queries in graphite-clickhouse logs
# Python 3.3 or greater required

import sys
import re
import json
import time
import dateutil.parser
from datetime import datetime
from datetime import timedelta

try:
    import urllib.parse as urlparse
except:
    import urlparse

from_p = re.compile('from=[0-9]+')
until_p = re.compile('until=[0-9]+')
now_p = re.compile('now=[0-9]+')

urls = set()


class URLStat:
    def __init__(self, url, time_from, time_until):
        self.url = url
        self.count = 1
        self.time_from = time_from
        self.time_until = time_until


def diff(x, y):
    if x is None:
        x = 0
    if y is None:
        y = 0
    return x - y


def urlstat_compare(x, y):
    return diff(x.time_until, x.time_from) - diff(y.time_until, y.time_from)


def timestamp_diff_format(t_from, t_until):
    e = int((t_from - t_until) / 60) * 60
    if e == 0:
        return ""
    else:
        return str(e)


def timestamp_tz(param, tz):
    if param is None:
        return None
    t = int(param[0])
    return int(datetime.fromtimestamp(t, tz).timestamp())


def parse_line(line):
    json_line = json.loads(line)
    if json_line['level'] is None or json_line['level'] != 'INFO':
        return
    if json_line['message'] is None or json_line['message'] != 'access':
        return
    if not json_line['url'].startswith('/render/'):
        return

    dt = dateutil.parser.parse(json_line['timestamp'])
    json_line['time'] = int(dt.timestamp())

    parsed = urlparse.urlparse(json_line['url'])
    params = urlparse.parse_qs(parsed.query)
    if len(params) > 0:
        url = '&target=' + urlparse.quote_plus(params['target'][0])
        if url != '&target=NonExistingTarget' and url not in urls:
            urls.add(url)


def main():
    for line in sys.stdin:
        parse_line(line)

    # PrintCSV header
    print('target')

    for u in urls:
        print("%s" % u)


if __name__ == "__main__":
    main()
