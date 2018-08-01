#!/usr/bin/env python3

"""
Compare two JSONL files containing the results from cr8 runs (run-spec, timeit..)
"""

import argparse
import json
from compare_measures import Diff, print_diff


def read_results(path):
    with open(path, 'r') as f:
        return [json.loads(l) for l in f]


def compare(path_old, path_new):
    results_old = {(r['statement'], r['concurrency']): r
                   for r in read_results(path_old)}
    results_new = {(r['statement'], r['concurrency']): r
                   for r in read_results(path_new)}
    for k, result_old in results_old.items():
        result_new = results_new[k]
        print(f'Q: {k[0]}')
        print(f'C: {k[1]}')
        print_diff(Diff(result_old['runtime_stats'], result_new['runtime_stats']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=str, help='Path to file with "old" results')
    parser.add_argument('--new', type=str, help='Path to file with "new" results')
    args = parser.parse_args()
    compare(args.old, args.new)


if __name__ == "__main__":
    main()
