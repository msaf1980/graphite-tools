#!/usr/bin/python

# Extract queries in graphite-clickhouse logs

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
    return datetime.fromtimestamp(t, tz).timestamp()


def parse_line(line):
    m = access_p.search(line)
    if m:
        dt = dateutil.parser.parse(m.group(1))
        json_line = json.loads(m.group(2))
        json_line['time'] = dt.timestamp()

        parsed = urlparse.urlparse(json_line['url'])
        params = urlparse.parse_qs(parsed.query)
        time_from = timestamp_tz(params.get('from'), dt.tzinfo)
        time_until = timestamp_tz(params.get('until'), dt.tzinfo)
        time_now = timestamp_tz(params.get('now'), dt.tzinfo)

        if time_from is not None:
            json_line['url'] = from_p.sub(
                "from=${TIMESTAMP}%s" %
                timestamp_diff_format(time_from, json_line['time']),
                json_line['url'])
        if time_until is not None:
            json_line['url'] = until_p.sub(
                "until=${TIMESTAMP}%s" %
                timestamp_diff_format(time_until, json_line['time']),
                json_line['url'])
        if time_now is not None:
            json_line['url'] = now_p.sub(
                "now=${TIMESTAMP}%s" %
                timestamp_diff_format(time_now, json_line['time']),
                json_line['url'])

        url_count = urls.get(json_line['url'])
        if url_count is None:
            urls[json_line['url']] = 1
        else:
            urls[json_line['url']] += 1


def main():
    for line in sys.stdin:
        parse_line(line)

    for k in urls:
        print("%d %s" % (urls[k], k))


if __name__ == "__main__":
    main()
