#!/usr/bin/python

# Extract queries in graphite-clickhouse logs

import sys
import re
import json
import time
import dateutil.parser
import pytz
from datetime import datetime

try:
    import urllib.parse as urlparse
except:
    import urlparse

access_p = re.compile(
    '^\[([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+\+[0-9]+)\] INFO access ({.*})$'
)

def format_timediff(e):
    if e > 0:
        d = "+"
    else:
        d = ""
    return "now%s%dh%dm%ds" % (d, e // 3600, (e % 3600 // 60), (e % 60 // 1))

def extract_utc_datetime(param):
    if param is None:
        return None
    t = int(param[0])
    return datetime.utcfromtimestamp(t)

def parse_line(line):
    m = access_p.search(line)
    if m:
        #sys.stdout.write('{"time": %s, %s}\n' % (m.group(1), m.group(2)))
        #date_time = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f%z')
        date_time = dateutil.parser.parse(m.group(1))
        json_line = json.loads(m.group(2))
        #json_line['time'] = date_time.strftime('%s')
        json_line['time'] = (date_time.replace(tzinfo=None) - datetime(1970, 1, 1)).total_seconds()
        sys.stdout.write("%s\n" % str(json_line))

        time_query = int(json_line['time'])
        parsed = urlparse.urlparse(json_line['url'])
        params = urlparse.parse_qs(parsed.query)

        time_from = extract_utc_datetime(params.get('from'))
        time_until = extract_utc_datetime(params.get('until'))
    
        #time_until = int(params.get('until', ['0'])[0])
        #from_query = format_timediff(time_query - time_from)
        #until_query = format_timediff(time_query - time_until)
        from_query = ""
        until_query = ""
        sys.stdout.write(
            "%d %s (%s) %s (%s)\n" %
            (time_query, time_from, from_query, time_until, until_query))

        print("%s %s %s %s %s" % (m.group(1), date_time, time_from, time_until, date_time.utcoffset()))



def main():
    for line in sys.stdin:
        parse_line(line)


if __name__ == "__main__":
    main()
