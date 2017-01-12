#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to launch two different crate nodes, run a spec against both nodes and
compare the results
"""

import argparse
import json
from uuid import uuid4
from scipy import stats

from cr8.run_crate import get_crate, CrateNode
from cr8.run_spec import do_run_spec
from cr8.log import Logger


# critical value for a confidence level of 99% - assuming a normal distribution
# See also: http://stattrek.com/statistics/dictionary.aspx?definition=critical_value
CRITICAL_VALUE = stats.norm.ppf([0.99])[0]


def perc_diff(v1, v2):
    return (abs(v1 - v2) / ((v1 + v2) / 2)) * 100


class Diff:
    def __init__(self, r1, r2):
        self.r1 = r1 = r1.runtime_stats
        self.r2 = r2 = r2.runtime_stats
        ind = stats.ttest_ind(r1['samples'], r2['samples'])
        tscore = ind.statistic
        self.mean_diff = perc_diff(r1['mean'], r2['mean'])
        if abs(tscore) >= CRITICAL_VALUE:
            self.significance = 'Likely significant'
        else:
            self.significance = 'Likely NOT significant'

    def __str__(self):
        return json.dumps(self.__dict__)


def compare_results(results_v1, results_v2):
    print('')
    print('')
    print('# Results')
    v1 = results_v1[0].version_info
    v2 = results_v2[0].version_info
    print(f"V1: {v1['number']}-{v1['hash']}")
    print(f"V2: {v2['number']}-{v2['hash']}")
    print('')

    results_v1 = {(r.statement, r.concurrency): r for r in results_v1}
    results_v2 = {(r.statement, r.concurrency): r for r in results_v2}
    for k, result_v1 in results_v1.items():
        result_v2 = results_v2[k]
        diff = Diff(result_v1, result_v2)
        print(k)
        print(f'  {diff.mean_diff:3.2f}% mean difference. {diff.significance}')
        print('             V1  →     V2')
        print(f"  mean:  {diff.r1['mean']:7.3f} → {diff.r2['mean']:7.3f}")
        print(f"  stdev: {diff.r1['stdev']:7.3f} → {diff.r2['stdev']:7.3f}")
        print(f"  max:   {diff.r1['max']:7.3f} → {diff.r2['max']:7.3f}")
        print(f"  min:   {diff.r1['min']:7.3f} → {diff.r2['min']:7.3f}")


def _run_spec(version, spec, result_hosts):
    crate_dir = get_crate(version)
    settings = {
        'cluster.name': str(uuid4())
    }
    results = []
    with Logger() as log, CrateNode(crate_dir=crate_dir, settings=settings) as n:
        n.start()
        log.result = results.append
        do_run_spec(spec, n.http_url, log, result_hosts, None)
    return results


def run_compare(v1, v2, spec, result_hosts):
    results_v1 = _run_spec(v1, spec, result_hosts)
    results_v2 = _run_spec(v2, spec, result_hosts)
    compare_results(results_v1, results_v2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        '--v1',
        help='cr8 version identifier or path to tarball (tar.gz)',
        required=True
    )
    p.add_argument(
        '--v2',
        help='cr8 version identifier or path to tarball (tar.gz)',
        required=True
    )
    p.add_argument('--spec', help='path to spec file', required=True)
    p.add_argument('--result-hosts', type=str)
    args = p.parse_args()
    try:
        run_compare(args.v1, args.v2, args.spec, args.result_hosts)
    except KeyboardInterrupt:
        print('Exiting..')


if __name__ == "__main__":
    main()
