#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script that tries to detect performance regression by looking at previous
benchmark results
"""

import argparse
import math
import sys
import numpy as np
from scipy import stats
from typing import NamedTuple
from termcolor import colored
from itertools import groupby
from datetime import datetime, timedelta
from crate.client import connect


class Key(NamedTuple):
    concurrency: int
    stmt: str
    bulk_size: int
    meta_name: str


class Diff(NamedTuple):
    key: Key
    prev_version: str
    new_version: str
    prev_val: float
    new_val: float
    diff: float
    linregress_slope: float


class Row(NamedTuple):
    stmt: str
    version: str
    concurrency: int
    bulk_size: int
    meta_name: str
    ended: int
    samples: int
    minimum: int
    percentile50: float


UNSTABLE_PREDICATES = [
    # fluctuates between 8 and 18 ms
    lambda d: (d.key.stmt.startswith('insert into articles') and d.diff < 100),

    # fluctuates between 7 and 14 ms
    lambda d: (d.key.stmt.startswith('insert into id_int_value_str') and d.diff < 100),
]


def _fetch_results(c, table):
    twenty_days_ago = (datetime.today() - timedelta(days=20))
    twenty_days_ago = int(twenty_days_ago.timestamp() * 1000)
    c.execute(f'''
select
    statement,
    version_info['number'] || '-' || substr(version_info['hash'], 0, 9) as version,
    concurrency,
    bulk_size,
    meta['name'] as meta_name,
    ended,
    runtime_stats['samples'],
    runtime_stats['min'] as minimum,
    runtime_stats['percentile']['50'] as p50
from
    {table}
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
''', (twenty_days_ago,))
    return (Row(*r) for r in c.fetchall())


def find_diffs(results):
    """ Find significant performance differences in the results.

    Returns:
        list of diffs

    >>> find_diffs([
    ...     Row('select name', '0.56.0', 1, 1, 'dummy.toml', 12345789000, [11, 12, 20], 10, 11),
    ...     Row('select name', '0.57.0', 1, 1, 'dummy.toml', 12345789000, [10, 10, 20], 10, 10),
    ...     Row('select name', '0.58.0', 1, 1, 'dummy.toml', 12345789000, [25, 25, 35], 25, 25),
    ... ])
    [Diff(key=Key(concurrency=1, stmt='select name', bulk_size=1, meta_name='dummy.toml'), prev_version='0.56.0', new_version='0.58.0', prev_val=10, new_val=25, diff=150.0)]
    """
    diffs = []
    for stmt_c, group in groupby(
            results,
            lambda r: (r.stmt, r.concurrency, r.bulk_size, r.meta_name)):
        group = list(group)
        if len(group) < 3:
            continue
        x = np.array(range(len(group)))
        y = np.array([r.percentile50 or r.minimum for r in group])
        linregress = stats.linregress(x, y)
        largest_min = max((r.minimum for r in group[:-1]))
        worst_result = next((r for r in group if r.minimum == largest_min))
        last_row = list(group)[-1]
        if last_row.minimum < largest_min or math.isclose(last_row.minimum, largest_min, abs_tol=0.001):
            continue
        diff = (last_row.minimum - largest_min) * 100 / largest_min
        diffs.append(Diff(
            Key(last_row.concurrency, last_row.stmt.strip(), last_row.bulk_size, last_row.meta_name),
            worst_result.version,
            last_row.version,
            largest_min,
            last_row.minimum,
            diff,
            linregress.slope
        ))
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
                   '  {diff}%   {prev_val:.3f} → {new_val:.3f}\n'
                   '  linregress slope: {linregress_slope:.3f}').format(**values))
            print('')


def is_stable(diff):
    """Return True if the benchmark in question is expected to be stable"""
    for is_unstable in UNSTABLE_PREDICATES:
        if is_unstable(diff):
            return False
    return True


def find_regressions(hosts, table):
    with connect(hosts) as conn:
        c = conn.cursor()
        results = _fetch_results(c, table)
        diffs = find_diffs(results)
        if diffs:
            stable_regressions = filter(is_stable, diffs)
            likely_regressions = [d for d in stable_regressions
                                  if d.linregress_slope > 1.00]
            print_diffs(likely_regressions)
            if any(filter(lambda d: d.diff > 15, likely_regressions)):
                sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--hosts', type=str, default='localhost:4200')
    p.add_argument('--table', type=str, default='benchmarks')
    args = p.parse_args()
    find_regressions(hosts=args.hosts, table=args.table)


if __name__ == "__main__":
    main()
