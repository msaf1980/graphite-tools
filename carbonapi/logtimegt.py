#!/usr/bin/python

import argparse
import sys
import re

parser = argparse.ArgumentParser(description='Parse graphite-clickhouse and carbonapi logs and print records with time greater or with non-OK HTTP codes')

parser.add_argument('-t', '--time', dest='time', default="time", action='store',
                         help='time field name')
parser.add_argument('-g', '--tg', dest='time_gt', type=float,
                    help='print log lines with time greate')

parser.add_argument('-s', '--status', dest='status', default="status", action='store',
                         help='HTTP status code field')
parser.add_argument('-c', '--codes', dest='statuses', type=int, nargs='+',
                    help='print log lines with HTTP status code')

args = parser.parse_args()

if args.time_gt is None and args.statuses is None:
    sys.exit("time_gt and statuses not set - what a find ?")

time_p = re.compile('"%s": *([0-9]+\.[0-9]+) *(,|})' % args.time)
status_p = re.compile('"%s": *([0-9]+) *(,|})' % args.status)

if args.statuses is None:
    statuses = None
else:
    statuses = set(args.statuses)

for line in sys.stdin:
    found = False
    if args.time_gt is not None:
        m = time_p.search(line)
        if m:
            time_log = float(m.group(1))
            if time_log > args.time_gt:
                found = True

    if not found and statuses is not None:
        m = status_p.search(line)
        if m:
            status_log = int(m.group(1))
            if status_log in statuses:
                found = True

    if found:
        sys.stdout.write(line)
