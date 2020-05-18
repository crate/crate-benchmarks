#!/usr/bin/env python3

"""
Script that compares measures read from two files:

    ./compare.py --old measures.txt --new measures.txt

The measures files should contain 1 number per line
"""

import argparse
import numpy as np
from scipy import stats
from cr8 import metrics


# critical value for a confidence level of 99% - assuming a normal distribution
# See also: http://stattrek.com/statistics/dictionary.aspx?definition=critical_value
CRITICAL_VALUE = stats.norm.ppf([0.99])[0]


def perc_diff(v1, v2):
    return (abs(v1 - v2) / ((v1 + v2) / 2)) * 100


class Diff:
    def __init__(self, r1, r2):
        self.r1 = r1
        self.r2 = r2
        r1_samples = np.array(r1.get('samples', [r1['mean']]))
        r2_samples = np.array(r2.get('samples', [r2['mean']]))
        ind = stats.ttest_ind(r1_samples, r2_samples)
        self.r1_ci = stats.norm.interval(0.95, loc=r1_samples.mean(), scale=r1_samples.std(ddof=1))
        self.r2_ci = stats.norm.interval(0.95, loc=r2_samples.mean(), scale=r2_samples.std(ddof=1))
        self.mean_diff = perc_diff(r1['mean'], r2['mean'])
        self.median_diff = perc_diff(r1['percentile']['50'], r2['percentile']['50'])
        probability = (1 - ind.pvalue) * 100.0
        self.ptext = f'There is a {probability:.2f}% probability that the observed difference is not random or due to noise, and the best estimate of that difference is {self.mean_diff:.2f}%'
        if abs(ind.statistic) >= CRITICAL_VALUE:
            self.significance = 'The test has statistical significance'
        else:
            self.significance = 'The test has no statistical significance'

    def __str__(self):
        return json.dumps(self.__dict__)


def print_diff(diff):
    mean_prefix = '+' if diff.r1['mean'] < diff.r2['mean'] else '-'
    median_prefix = '+' if diff.r1['percentile']['50'] < diff.r2['percentile']['50'] else '-'
    print(f'| Version |         Mean ±    Stdev |        Min |     Median |         Q3 |        Max |')
    print(f"|   V1    |   {diff.r1['mean']:10.3f} ± {diff.r1['stdev']:8.3f} | {diff.r1['min']:10.3f} | {diff.r1['percentile']['50']:10.3f} | {diff.r1['percentile']['75']:10.3f} | {diff.r1['max']:10.3f} |")
    print(f"|   V2    |   {diff.r2['mean']:10.3f} ± {diff.r2['stdev']:8.3f} | {diff.r2['min']:10.3f} | {diff.r2['percentile']['50']:10.3f} | {diff.r2['percentile']['75']:10.3f} | {diff.r2['max']:10.3f} |")
    print(f'├---------┴-------------------------┴------------┴------------┴------------┴------------┘')
    print(f"|               {mean_prefix}{diff.mean_diff:7.2f}%                           {median_prefix}{diff.median_diff:7.2f}%   ")
    print(f'| V1 mean is within {diff.r1_ci[0]:.2f} - {diff.r1_ci[1]:.2f}')
    print(f'| V2 mean is within {diff.r2_ci[0]:.2f} - {diff.r2_ci[1]:.2f}')
    print(f'{diff.ptext}')
    print(f'{diff.significance}')
    print('')


def main(path_old, path_new):
    r1 = metrics.Stats()
    r2 = metrics.Stats()
    with open(path_old) as f:
        for l in f:
            r1.measure(float(l))
    with open(path_new) as f:
        for l in f:
            r2.measure(float(l))
    print_diff(Diff(r1.get(), r2.get()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=str, help='Path to file with old measures')
    parser.add_argument('--new', type=str, help='Path to file with new measures')
    args = parser.parse_args()
    main(args.old, args.new)
