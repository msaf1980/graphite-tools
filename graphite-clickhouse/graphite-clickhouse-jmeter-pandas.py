#!/usr/bin/env python3

import argparse
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np

try:
    import urllib.parse as urlparse
except:
    import urlparse

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

# aggregate in timestamp (in seconds)
roundTo = 10


def p95(g):
    return np.percentile(g, 95)


def p99(g):
    return np.percentile(g, 99)


def parse_cmdline():
    parser = argparse.ArgumentParser(description='Plot jmeter results')

    parser.add_argument("-f",
                        "--file",
                        dest='files',
                        type=str,
                        required=True,
                        nargs='+',
                        help='jmeter csv results file')

    return parser.parse_args()


def responce_code_clean(x):
    s = str(x)
    if s.startswith("Non HTTP response code: "):
        s = s[24:]
        loc = s.rfind('.')
        if loc >= 0:
            s = s[loc + 1:]
        if s.endswith('Exception'):
            s = s[:-9]
        return s
    else:
        return s


def url_extract_target(x):
    parsed = urlparse.urlparse(x)
    params = urlparse.parse_qs(parsed.query)
    return urlparse.unquote(params['target'][0])


def aggregate_total(dfs):
    result = pd.pivot_table(
            dfs,
            values=['Latency', 'bytes'],
            #index=['time', 'threadName', 'responseCode'],
            index=['time'],
            aggfunc={
                'bytes': [len, min, max, np.mean, p95, p99],
                'Latency': [min, max, np.mean, p95, p99],
            })

    print("Total")
    print(result)

    return result


def aggregate_by_code(dfs, statusCodes):
    result = dict()
    for code in statusCodes:
        result[code] = pd.pivot_table(
            dfs[dfs.responseCode == code],
            values=['Latency', 'bytes'],
            #index=['time', 'threadName', 'responseCode'],
            index=['time'],
            aggfunc={
                'bytes': [len, min, max, np.mean, p95, p99],
                'Latency': [min, max, np.mean, p95, p99],
            })

        print(code)
        print(result[code])

    return result


def main():
    args = parse_cmdline()

    read_csv_param = dict(index_col=['timeStamp'],
                          low_memory=False,
                          sep=",",
                          na_values=[' ', '', 'null'])
    print(args.files[0])

    dfs = pd.read_csv(args.files[0], **read_csv_param)
    for file in args.files[1:]:
        print(file)
        tempDfs = pd.read_csv(file, **read_csv_param)
        dfs = dfs.append(tempDfs)

    # Убрать из выборки все JSR223, по ним статистику строить не надо, оставить только HTTP Request Sampler.
    # У JSR223 URL пустой, у HTTP-запросов URL указан.
    dfs = dfs[(pd.isnull(dfs.URL) == False)]

    dfs['threadName'] = dfs['threadName'].apply(lambda x: x[0:x.rfind(' ')])
    dfs['responseCode'] = dfs['responseCode'].apply(
        responce_code_clean)  # cleanup responce codes
    dfs['URL'] = dfs['URL'].apply(
        url_extract_target)  # extract target


    dfs.index = pd.to_datetime(dfs.index, unit='ms')

    dfs['time'] = dfs.index.round("%ds" % roundTo)  # rounded time

    #rpsLegend = ["Total"]

    #print(dfs.to_string())

    statusCodes = dfs['responseCode'].unique()
    #colorCodes = dict()
    #for code in statusCodes:
    #    if code == '200':
    #        colorCodes[code] = 'green'
    #    elif code == 'ConnectTimeout':
    #        colorCodes[code] = 'red'

    aggregate_total(dfs)
    aggregate_by_code(dfs, statusCodes)

    #print(dfs)


if __name__ == "__main__":
    main()
