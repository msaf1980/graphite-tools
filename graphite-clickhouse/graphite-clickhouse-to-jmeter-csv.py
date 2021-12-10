#!/usr/bin/python3

# Extract queries in graphite-clickhouse logs to JMeter csv file for later analyze
# Python 3.3 or greater required

import sys
import os
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


def get_exception_loc():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    return (filename, lineno)


MINITES = 600.0
HOUR = 3600.0
DAY = HOUR * 24
WEEK = DAY * 7
MONTH = DAY * 30
YEAR = DAY * 365

class Stat:
    def __init__(self, dt, elapsed):
        self.dt = dt
        self.elapsed = elapsed
        self.bytes = 0

queries = dict()
queriesDict = dict()

def durations(duration):
    d = round(duration / YEAR)
    if d > 0:
        return "%d years" % d
    d = round(duration / MONTH)
    if d > 0:
        return "%d months" % d
    d = round(duration / WEEK)
    if d > 0:
        return "%d weeks" % d
    d = round(duration / DAY)
    if d > 0:
        return "%d days" % d
    d = round(duration / HOUR)
    if d > 0:
        return "%d hours" % d
    d = int(round(duration / MINITES) * MINITES)
    return "%d minutes" % d


def parse_line(line):
    bytes = 0
    sentBytes = 0

    json_line = json.loads(line)
    label = "RENDER"
    if json_line['level'] is None or json_line['level'] != 'INFO':
        return
    if json_line['message'] is None:
        return
    elif json_line['message'] == 'query':
        try:
            id = json_line['request_id']
            query = json_line['query']
        except:
            pass
        dt = int(dateutil.parser.parse(json_line['timestamp']).timestamp() * 1000)
        if query.startswith('SELECT Path FROM '):
            # SELECT Path FROM graphite_index WHERE (Level = 10004) AND (Path = 'total.activity.test.cloud' OR Path = 'total.activity.zebra.KE-cloud.') AND (Date >='2020-06-05' AND Date <= '2020-06-05') GROUP BY Path
            # SELECT Path FROM graphite_index WHERE (Level = 20007) AND (Path LIKE 'TEST.apps.namespaces.PAYMENT.%') AND (Date = '1970-02-12') GROUP BY Path
            queriesDict[id] = Stat(dt, int(1000 * float(json_line['time'])))

        return
    elif json_line['message'] == 'render':
        try:
            id = json_line['request_id']
            bytes = int(json_line['read_bytes'])
            queries[id] = bytes
        except:
            pass
        return
    elif json_line['message'] == 'finder':
        # {"level":"INFO","timestamp":"2020-06-05T07:20:12.088+0300","message":"finder","request_id":"a69e4339110ccc360f22c47183e956fe","metrics":20}
        try:
            id = json_line['request_id']
            queriesDict[id].bytes = int(json_line['metrics'])
        except:
            pass
        return
    elif json_line['message'] != 'access':
        return
   
    try:
        if json_line['url'].startswith('/metrics/find/?'):
            label = "FIND (METRICS)"
        elif not json_line['url'].startswith('/render/?'):
            return

        id = json_line['request_id']
        dt = int(dateutil.parser.parse(json_line['timestamp']).timestamp() * 1000)
        elapsed = int(1000 * float(json_line['time']))
        responceCode = int(json_line['status'])
        if responceCode == 200:
            responceMsg = "OK"
            success = "true"
        elif responceCode == 403:
            responceMsg = "Forbidden"
            success = "false"
        elif responceCode == 404:
            responceMsg = "Not found"
            success = "false"
        else:
            responceMsg = "Error"
            success = "false"

        url = json_line['url']
        parsed = urlparse.urlparse(url)
        params = urlparse.parse_qs(parsed.query)

        p = []
        if len(params) > 0:

            if label == "FIND (METRICS)":
                for q in params['query']:
                    p.append(q)
                try:
                    bytes = queriesDict[id].bytes
                    del queriesDict[id]
                except:
                    bytes = 0
                url = "&".join(p)
            elif label == "RENDER":
                # NonExistingTarget
                if params['target'][0] != 'NonExistingTarget':
                    next
                #query = urlparse.quote_plus(params['target'][0])
                fromTime = int(params['from'][0])
                untilTime = int(params['until'][0])
                try:
                    bytes = queries[id]
                    del queries[id]
                except:
                    bytes = 0

                fromTime = int(params['from'][0])
                untilTime = int(params['until'][0])
                d = durations(untilTime - fromTime)
                label += " " + d

                try:
                    stat = queriesDict[id]
                    labelFind = "FIND " + d
                    sys.stdout.write("%s,%s,%s,%s,%s,Live,,%s,,%d,%d,1,1,\"%s\",%s,0,0\n" % (
                        stat.dt, stat.elapsed, labelFind, "200", "OK",
                        "true",
                        stat.bytes, 0,
                        url, stat.elapsed
                    ))
                except:
                    pass
            else:
                next

            #ts,elapsed,label,respCode,respMsg,threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect
            sys.stdout.write("%s,%s,%s,%s,%s,Live,,%s,,%d,%d,1,1,\"%s\",%s,0,0\n" % (
                dt, elapsed, label, responceCode, responceMsg,
                success,
                bytes, sentBytes,
                url, elapsed
            ))

    except BrokenPipeError as e:
        raise e
    except Exception as e:
        filename, line = get_exception_loc()
        sys.stderr.write("ERROR (%s): %s: %s\n" % (line, str(e), line))
        next


def main():
    # PrintCSV header
    print('timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect')
    for line in sys.stdin:
        parse_line(line)


if __name__ == "__main__":
    main()
