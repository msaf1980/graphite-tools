import argparse
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

# aggregate in timestamp (in seconds)
roundTo = 30


def p95(g):
    return np.percentile(g, 95)


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
    if x.startswith("Non HTTP response code: "):
        s = x[24:]
        loc = s.rfind('.')
        if loc >= 0:
            s = s[loc + 1:]
        if s.endswith('Exception'):
            s = s[:-9]
        return s
    else:
        return x


def saveSummary(dfs, statusCodes, colorCodes):
    resultSum = dict()
    for code in statusCodes:
        resultSum[code] = pd.pivot_table(
            dfs[dfs.responseCode == code],
            values=['Latency', 'bytes'],
            #index=['time', 'threadName', 'responseCode'],
            index=['time'],
            aggfunc={
                'bytes': [min, max, np.mean, p95],
                'Latency': [len, min, max, np.mean, p95]
            })

        #print(resultSum[code])

    markerfmt = '.'

    ################################
    # RPS

    plt.xlabel('time')
    plt.ylabel('RPS')

    # Turn on the minor TICKS, which are required for the minor GRID
    plt.minorticks_on()
    # Customize the major grid
    plt.grid(which='major', linestyle='-', linewidth=0.5)
    # Customize the minor grid
    plt.grid(which='minor', linestyle=':', linewidth=0.5)

    for k in resultSum:
        markerline, stemlines, baseline = plt.stem(
            resultSum[k].index,
            resultSum[k]['Latency'].len / roundTo,
            markerfmt=markerfmt)
        plt.setp(baseline, 'markerfacecolor', colorCodes[k])
        plt.setp(markerline, 'markerfacecolor', colorCodes[k])

        plt.setp(stemlines, 'linestyle', 'dotted')

    plt.legend(statusCodes, loc='upper left')

    plt.savefig("rps.png", dpi=300)
    plt.close()

    # RPS
    ################################


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

    dfs.index = pd.to_datetime(dfs.index, unit='ms')

    dfs['time'] = dfs.index.round("%ds" % roundTo)  # rounded time
    #rpsLegend = ["Total"]

    #print(resultSum)

    #print(dfs.to_string())

    statusCodes = dfs['responseCode'].unique()
    colorCodes = dict()
    for code in statusCodes:
        if code == '200':
            colorCodes[code] = 'green'
        elif code == 'ConnectTimeout':
            colorCodes[code] = 'red'

    saveSummary(dfs, statusCodes, colorCodes)


if __name__ == "__main__":
    main()
