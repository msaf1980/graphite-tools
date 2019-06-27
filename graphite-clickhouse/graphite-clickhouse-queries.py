#!/usr/bin/python

# Extract queries in graphite-clickhouse logs
# Python 3.3 or greater required

import sys
import re
import json
import time
import dateutil.parser
import pytz
from datetime import datetime
from datetime import timedelta

try:
    import urllib.parse as urlparse
except:
    import urlparse

access_p = re.compile(
    '^\[([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+\+[0-9]+)\] INFO access ({.*})$'
)

from_p = re.compile('from=[0-9]+')
until_p = re.compile('until=[0-9]+')
now_p = re.compile('now=[0-9]+')

urls = dict()


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
    m = access_p.search(line)
    if m:
        dt = dateutil.parser.parse(m.group(1))
        json_line = json.loads(m.group(2))
        json_line['time'] = int(dt.timestamp())

        parsed = urlparse.urlparse(json_line['url'])
        params = urlparse.parse_qs(parsed.query)
        time_from = timestamp_tz(params.get('from'), dt.tzinfo)
        time_until = timestamp_tz(params.get('until'), dt.tzinfo)
        time_now = timestamp_tz(params.get('now'), dt.tzinfo)

        duration = 0
        if time_from is not None:
            json_line['url'] = from_p.sub("from=<FROM>", json_line['url'])
        if time_until is not None:
            json_line['url'] = until_p.sub("until=<UNTIL>", json_line['url'])
            duration = time_until - time_from
        if time_now is not None:
            if time_from is None:
                sys.stderr.write("error on url '%s': from not found\n" %
                                 json_line['url'])
                return
            if time_until is not None:
                sys.stderr.write("error on url %s: until and now set\n" %
                                 json_line['url'])
                return
            json_line['url'] = now_p.sub("now=<UNTIL>", json_line['url'])
            time_until = time_now
            duration = time_now - time_from

        if duration < 0:
            return

        url_count = urls.get(json_line['url'])
        if url_count is None:
            urls[json_line['url']] = URLStat(json_line['url'], time_from,
                                             time_until)
            urls[json_line['url']].duration = duration
        else:
            urls[json_line['url']].count += 1
            if duration > diff(urls[json_line['url']].time_until,
                               urls[json_line['url']].time_from):
                urls[json_line['url']].time_from = time_from
                urls[json_line['url']].time_until = time_until


def main():
    short_form = True
    if len(sys.argv) > 2 and sys.argv[1] in ("-", "--long"):
        short_form = False

    for line in sys.stdin:
        parse_line(line)

    urls_proc = set()
    for u in sorted(urls.values(),
                    key=lambda x: diff(x.time_until, x.time_from)):
        if short_form:
            if u.url not in urls_proc:
                print(u.url)
                urls_proc.add(u.url)
        else:
            print("%s %s %s" % (u.url, u.time_from, u.time_until))


if __name__ == "__main__":
    main()
