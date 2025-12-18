#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

BUILDS = {
    "translog_age_only": "branch:s/optimize-shard-flush",
    "flush_segments_only": "branch:s/indexing-flush-segments",
    "translog_age_segments_flush": "branch:s/translog_age_segments_flush",
}

RUNS = [
    ['--env', 'CRATE_HEAP_SIZE=1G'],
    ['--env', 'CRATE_HEAP_SIZE=4G']
]

BASE_ARGS = [
    '--v1', 'branch:master',
    '--spec', 'specs/twitter/insert_single.py',
    '--fork', 1,
    '--report-indexing',
]

def main():
    args = ['python', 'compare_run.py']
    for arg in BASE_ARGS:
        args.append(str(arg))
    for build_name, build in BUILDS.items():
        build_args = args.copy()
        build_args.append('--v2')
        build_args.append(build)
        for run_args in RUNS:
            print('='*60)
            print(f'Running comparison against MASTER:')
            print(f'  Label: {build_name}')
            print(f'  Image: {build}')
            print(f'  Args:')
            print(f'    {run_args}')
            print('='*60)
            per_run_args = build_args.copy()
            per_run_args.extend(run_args)
            subprocess.run(per_run_args)


if __name__ == "__main__":
    main()