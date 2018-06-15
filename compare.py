#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to launch two different crate nodes, run a spec against both nodes and
compare the results
"""

import argparse
import json
from functools import partial
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
        r1_samples = r1.get('samples', [r1['mean']])
        r2_samples = r2.get('samples', [r2['mean']])
        ind = stats.ttest_ind(r1_samples, r2_samples)
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
    print('# Results (server side duration in ms)')
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
        print(f'Q: {k[0]}')
        print(f'C: {k[1]}')
        print(f'  {diff.mean_diff:3.2f}% mean difference. {diff.significance}')
        print('             V1    →   V2')
        print(f"  mean:  {diff.r1['mean']:7.3f} → {diff.r2['mean']:7.3f}")
        print(f"  stdev: {diff.r1.get('stdev', 0):7.3f} → {diff.r2.get('stdev', 0):7.3f}")
        print(f"  max:   {diff.r1['max']:7.3f} → {diff.r2['max']:7.3f}")
        print(f"  min:   {diff.r1['min']:7.3f} → {diff.r2['min']:7.3f}")
        print('')


def _run_spec(version, spec, result_hosts, env, settings):
    crate_dir = get_crate(version)
    settings.setdefault('cluster.name', str(uuid4()))
    results = []
    with Logger() as log, CrateNode(crate_dir=crate_dir, settings=settings, env=env) as n:
        n.start()
        log.result = results.append
        do_run_spec(spec, n.http_url, log, result_hosts, None)
    return results


def _get_best_of(r1, r2):
    if len(r1) != len(r2):
        raise ValueError("Both results, r1 and r2, must have the same size")
    best_of = []
    for i in range(len(r1)):
        if r2[i].runtime_stats['mean'] < r1[i].runtime_stats['mean']:
            best_of.append(r2[i])
        else:
            best_of.append(r1[i])
    return best_of


def run_compare(v1, v2, spec, result_hosts, forks, env, settings):
    run_v1 = partial(_run_spec, v1, spec, result_hosts, env, settings)
    run_v2 = partial(_run_spec, v2, spec, result_hosts, env, settings)
    results_v1 = run_v1()
    results_v2 = run_v2()
    for i in range(forks - 1):
        results_v1 = _get_best_of(results_v1, run_v1())
        results_v2 = _get_best_of(results_v2, run_v2())
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
    p.add_argument('--forks', type=int, default=5,
                   help='Number of times the nodes are launched and the spec re-run')
    p.add_argument('--env', action='append',
                   help='Environment variable for crate nodes. E.g. --env CRATE_HEAP_SIZE=2g')
    p.add_argument('-s', '--setting', action='append',
                   help='Crate setting. E.g. -s path.data=/tmp/c1/')
    args = p.parse_args()
    if args.env:
        env = dict(i.split('=') for i in args.env)
    else:
        env = {}
    if args.setting:
        settings = dict(i.split('=') for i in args.setting)
    else:
        settings = {}
    try:
        run_compare(
            args.v1,
            args.v2,
            args.spec,
            args.result_hosts,
            forks=max(1, args.forks),
            env=env,
            settings=settings
        )
    except KeyboardInterrupt:
        print('Exiting..')


if __name__ == "__main__":
    main()
