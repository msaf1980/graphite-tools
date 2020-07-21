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

queries = dict()


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
    elif json_line['message'] == 'render':
        try:
            id = json_line['request_id']
            bytes = int(json_line['read_bytes'])
            queries[id] = bytes
        except:
            pass
        return
    elif json_line['message'] == 'finder':
        try:
            id = json_line['request_id']
            bytes = int(json_line['metrics'])
            queries[id] = bytes
        except:
            pass
        return
    elif json_line['message'] != 'access':
        return
    if json_line['url'].startswith('/metrics/find/?'):
      label = "FIND"
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
    
    if len(params) > 0:
        try:
            if label == "FIND":
                url = params['query'][0]
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
                label += " " + durations(untilTime - fromTime)

                #print("%s %s %d" % (fromTime, untilTime, bytes))
            else:
                # %2A
                # NonExistingTarget
                if params['query'][0] != 'NonExistingTarget':
                    next

                try:
                    fromTime = int(params['from'][0])
                    untilTime = int(params['until'][0])
                    label += " " + durations(untilTime - fromTime)
                except:
                    pass

                #query = urlparse.quote_plus(params['query'][0])


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
