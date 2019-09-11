#!/usr/bin/python

import argparse
import sys
import re
import json

parser = argparse.ArgumentParser(
    description=
    'Parse graphite-clickhouse and carbonapi logs and print records with time greater or with non-OK HTTP codes'
)

parser.add_argument('-t',
                    '--time',
                    dest='time',
                    type=float,
                    help='print log lines with time greate')
parser.add_argument('-s',
                    '--size',
                    dest='size',
                    type=int,
                    help='print log lines with time greate')
parser.add_argument('-m',
                    '--metrics',
                    dest='metrics',
                    type=int,
                    help='print log lines with time greate')

parser.add_argument('-c',
                    '--codes',
                    dest='statuses',
                    type=int,
                    nargs='+',
                    help='print log lines with HTTP status code')

args = parser.parse_args()

if args.time is None and args.statuses is None and args.size is None and args.metrics is None:
    sys.exit("what a find ?")

if args.statuses is None:
    statuses = None
else:
    statuses = set(args.statuses)


req_ids = set()
reqs = dict()
queries = dict()

for line in sys.stdin:
    data = json.loads(line)
    if data.get('level') != 'INFO':
        continue

    message = data.get('message')
    if message == 'finder':
        if args.metrics:
            request_id = data.get('request_id')
            metrics = data.get('metrics')
            if metrics and request_id:
                metrics = int(metrics)
                if metrics >= args.metrics:
                    #found = True
                    try:
                        query = queries[request_id]
                        print(query)
                        del query
                    except:
                        pass

                    sys.stdout.write(line)
    elif message == 'render':
        size = data.get('read_bytes')
        if size:
            size = int(size)
            request_id = data.get('request_id')
            if request_id:
                if args.size and size >= args.size:
                    req_ids.add(request_id)
                reqs[request_id] = line
    elif message == 'access':
        found = False
        request_id = data.get('request_id')
        req = reqs.get(request_id)

        #print("'%s'" % req)

        if not found and request_id in req_ids:
            req_ids.remove(request_id)
            found = True

        if not found and args.time:
            time = data.get('time')
            if time:
                if float(time) >= args.time:
                    found = True

        if not found and statuses:
            status = data.get('status')
            if status:
                status = int(status)
                if status in statuses:
                    found = True

        if found:
            try:
                query = queries[request_id]
                sys.stdout.write(query)
            except:
                pass

            if req != "":
                sys.stdout.write(req)

            sys.stdout.write(line)

        try:
            del queries[request_id]
        except:
            pass
        if req:
            del req
    elif message == 'query':
        if len(queries) < 1000:  # Overflow check
            request_id = data.get('request_id')
            if request_id:
                queries[request_id] = line
        else:
            sys.stderr.write("OVERFLOW\n")

    #if found:
    #    sys.stdout.write(line)

