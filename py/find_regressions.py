#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to find performance regressions by looking at benchmark runs from the
last 2 days

In order to determine if there is a significant performance difference a t-test
is done.
(https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html#scipy.stats.ttest_ind)

This is not a bullet proof approach, it is used because of a lack of (known)
better alternatives.
"""

import argparse
import math
import sys
from typing import NamedTuple
from termcolor import colored
from itertools import groupby
from datetime import datetime, timedelta
from crate.client import connect
from scipy import stats


class Key(NamedTuple):
    concurrency: int
    stmt: str
    bulk_size: int
    meta_name: str


class Diff(NamedTuple):
    key: Key
    prev_version: str
    new_version: str
    prev_p50: float
    new_p50: float
    diff: float


class Row(NamedTuple):
    stmt: str
    version: str
    concurrency: int
    bulk_size: int
    meta_name: str
    ended: int
    samples: int
    percentile50: float


UNSTABLE_PREDICATES = [
    # fluctuates between 8 and 18 ms
    lambda d: (d.key.stmt.startswith('insert into articles') and d.diff < 200),

    # fluctuates between 7 and 14 ms
    lambda d: (d.key.stmt.startswith('insert into id_int_value_str') and d.diff < 100),

    lambda d: (
        d.key.stmt == 'select extract(day from "visitDate"), count(*) from uservisits group by 1 order by 2 desc limit 20' and
        d.diff < 20),
]


def _fetch_results(c):
    two_days_ago = (datetime.today() - timedelta(days=2))
    two_days_ago = int(two_days_ago.timestamp() * 1000)
    c.execute('''
select
    statement,
    version_info['number'] || '-' || substr(version_info['hash'], 0, 9) as version,
    concurrency,
    bulk_size,
    meta['name'] as meta_name,
    ended,
    runtime_stats['samples'],
    runtime_stats['percentile']['50'] as p50
from
    benchmarks
where
    ended >= ?
order by
    statement,
    concurrency,
    bulk_size,
    meta['name'],
    version_info['number'],
    version_info['hash'],
    ended desc
''', (two_days_ago,))
    return (Row(*r) for r in c.fetchall())


# critical value for a confidence level of 99% - assuming a normal distribution
# See also: http://stattrek.com/statistics/dictionary.aspx?definition=critical_value 
critical_value = stats.norm.ppf([0.99])[0]


def find_diffs(results):
    """ Find significant performance differences in the results.

    Returns:
        list of diffs

    >>> find_diffs([
    ...     Row('select name', '0.56.0', 1, 1, 'dummy.toml', 12345789000, [11, 12, 20], 11),
    ...     Row('select name', '0.57.0', 1, 1, 'dummy.toml', 12345789000, [10, 10, 20], 10),
    ...     Row('select name', '0.58.0', 1, 1, 'dummy.toml', 12345789000, [25, 25, 35], 25),
    ... ])
    [Diff(key=Key(concurrency=1, stmt='select name', bulk_size=1, meta_name='dummy.toml'), prev_version='0.57.0', new_version='0.58.0', prev_p50=10, new_p50=25, diff=150.0)]
    """
    diffs = []
    for stmt_c, group in groupby(
            results,
            lambda r: (r.stmt, r.concurrency, r.bulk_size, r.meta_name)):
        prev = None
        for g in group:
            if not prev or prev.version == g.version:
                prev = g
                continue
            try:
                ind = stats.ttest_ind(prev.samples, g.samples)
            except TypeError:
                prev = g
                continue
            tscore = ind.statistic
            prev_p50 = prev.percentile50
            new_p50 = g.percentile50
            if new_p50 < prev_p50 or math.isclose(new_p50, prev_p50, abs_tol=0.001):
                prev = g
                continue
            diff = (new_p50 - prev_p50) * 100 / prev_p50
            if abs(tscore) >= critical_value:
                diffs.append(Diff(
                    Key(g.concurrency, g.stmt.strip(), g.bulk_size, g.meta_name),
                    prev.version,
                    g.version,
                    prev_p50,
                    new_p50,
                    diff
                ))
            prev = g
    return diffs


def print_diffs(diffs):
    print(colored('Diffs detected: ', attrs=['bold']))
    print('')

    diffs = sorted(diffs, key=lambda r: r.diff, reverse=True)
    for key, group in groupby(diffs, lambda r: r.key):
        print(str(key))
        print('')

        for g in group:
            values = g._asdict()
            diff_fmt = '{0:5.1f}'
            if g.diff > 10:
                diff_fmt = colored(diff_fmt, 'red', attrs=['bold'])
            elif g.diff > 5:
                diff_fmt = colored(diff_fmt, 'red')
            values['diff'] = diff_fmt.format(g.diff)

            print(('  {prev_version} → {new_version}\n'
                   '  {diff}%   {prev_p50:.3f} → {new_p50:.3f}').format(**values))
            print('')


def is_stable(diff):
    """Return True if the benchmark in question is expected to be stable"""
    for is_unstable in UNSTABLE_PREDICATES:
        if is_unstable(diff):
            return False
    return True


def find_regressions(hosts):
    with connect(hosts) as conn:
        c = conn.cursor()
        results = _fetch_results(c)
        diffs = find_diffs(results)
        if diffs:
            stable_regressions = list(filter(is_stable, diffs))
            print_diffs(stable_regressions)
            if any(filter(lambda d: d.diff > 10, stable_regressions)):
                sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--hosts', type=str, default='localhost:4200')
    args = p.parse_args()
    find_regressions(hosts=args.hosts)


if __name__ == "__main__":
    main()
