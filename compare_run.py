#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to launch two different crate nodes, run a spec against both nodes and
compare the results
"""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from functools import partial
from uuid import uuid4
from typing import Optional, Dict, Any

from cr8.run_crate import get_crate, CrateNode
from cr8.run_spec import do_run_spec
from cr8.log import Logger
from compare_measures import Diff, print_diff
from util import dict_from_kw_args


def compare_results(results_v1,
                    metrics_v1,
                    stat_resultv1: Dict[str, Any],
                    results_v2,
                    metrics_v2,
                    stat_resultv2: Dict[str, Any],
                    show_plot):
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
        print(f'Q: {k[0]}')
        print(f'C: {k[1]}')
        print_diff(Diff(result_v1.runtime_stats, result_v2.runtime_stats), show_plot)

    ns_to_ms = 0.000001
    v1_gcy_cnt = metrics_v1['gc']['young']['count']
    v2_gcy_cnt = metrics_v2['gc']['young']['count']
    v1_gcy_avg = metrics_v1['gc']['young']['avg_duration_ns'] * ns_to_ms
    v2_gcy_avg = metrics_v2['gc']['young']['avg_duration_ns'] * ns_to_ms
    v1_gcy_max = metrics_v1['gc']['young']['max_duration_ns'] * ns_to_ms
    v2_gcy_max = metrics_v2['gc']['young']['max_duration_ns'] * ns_to_ms

    v1_gco_cnt = metrics_v1['gc']['old']['count']
    v2_gco_cnt = metrics_v2['gc']['old']['count']
    v1_gco_avg = metrics_v1['gc']['old']['avg_duration_ns'] * ns_to_ms
    v2_gco_avg = metrics_v2['gc']['old']['avg_duration_ns'] * ns_to_ms
    v1_gco_max = metrics_v1['gc']['old']['max_duration_ns'] * ns_to_ms
    v2_gco_max = metrics_v2['gc']['old']['max_duration_ns'] * ns_to_ms

    byte_to_mb = 0.000001
    v1_heap_used = metrics_v1['heap']['used'] * byte_to_mb
    v2_heap_used = metrics_v2['heap']['used'] * byte_to_mb
    v1_heap_init = metrics_v1['heap']['initial'] * byte_to_mb
    v2_heap_init = metrics_v2['heap']['initial'] * byte_to_mb

    v1_alloc_rate = metrics_v1['alloc']['rate'] * byte_to_mb
    v2_alloc_rate = metrics_v2['alloc']['rate'] * byte_to_mb
    v1_alloc_total = metrics_v1['alloc']['total'] * byte_to_mb
    v2_alloc_total = metrics_v2['alloc']['total'] * byte_to_mb
    print(f'''
System/JVM Metrics (durations in ms, byte-values in MB)
    |    YOUNG GC            |       OLD GC           |      HEAP         |     ALLOC     
    |  cnt      avg      max |  cnt      avg      max |  initial     used |     rate      total
 V1 | {v1_gcy_cnt:4.0f} {v1_gcy_avg:8.2f} {v1_gcy_max:8.2f} | {v1_gco_cnt:4.0f} {v1_gco_avg:8.2f} {v1_gco_max:8.2f} | {v1_heap_init:8.0f} {v1_heap_used:8.0f} | {v1_alloc_rate:8.2f} {v1_alloc_total:10.0f}
 V2 | {v2_gcy_cnt:4.0f} {v2_gcy_avg:8.2f} {v2_gcy_max:8.2f} | {v2_gco_cnt:4.0f} {v2_gco_avg:8.2f} {v2_gco_max:8.2f} | {v2_heap_init:8.0f} {v2_heap_used:8.0f} | {v2_alloc_rate:8.2f} {v2_alloc_total:10.0f}
    ''')
    print('Top allocation frames')
    print('  V1')
    for frame in metrics_v1['alloc']['top_frames_by_alloc']:
        print('    ' + frame)
    print('  V2')
    for frame in metrics_v2['alloc']['top_frames_by_alloc']:
        print('    ' + frame)

    print('')
    print('Top frames (by count)')
    print('  V1')
    for frame in metrics_v1['alloc']['top_frames_by_count']:
        print('    ' + frame)
    print('  V2')
    for frame in metrics_v2['alloc']['top_frames_by_count']:
        print('    ' + frame)

    if metrics_v1:
        print("")
        print("perf stat")
        print("  v1")
        max_digits = max(
            len(str(int(float(x.get("metric-value", x.get("counter-value", 0))))))
            for x in stat_resultv1.values()
        )
        max_keylen = max(
            len(x)
            for x in stat_resultv1.keys()
        )
        for k, v in stat_resultv1.items():
            print("    " + format_perf_stat_value(k, v, max_digits, max_keylen))
        print("  v2")
        for k, v in stat_resultv2.items():
            print("    " + format_perf_stat_value(k, v, max_digits, max_keylen))


def format_perf_stat_value(k: str, v: Dict[str, Any], max_digits: int, max_keylen: int) -> str:
    max_digits += 4
    parts = [
        f"{k:<{max_keylen}}: "
    ]
    if "metric-value" in v:
        parts.append(f"{float(v["metric-value"]): {max_digits}.2f}")
    elif "counter-value" in v:
        parts.append(f"{float(v["counter-value"]): {max_digits}.2f}")
    unit = v.get("unit", "")
    if unit:
        parts.append(unit)
    return "".join(parts)


def jfr_start(pid, tmpdir):
    java_home = os.environ.get('JAVA_HOME')
    jcmd = java_home and os.path.join(java_home, 'bin', 'jcmd') or 'jcmd'
    filename = os.path.join(tmpdir, str(uuid4()) + '.jfr')
    subprocess.check_call([
        jcmd,
        str(pid),
        'JFR.start',
        f'filename="{filename}"',
        'name=rec',
        'settings=profile',
        'maxsize=50m',
        'maxage=10m'
    ])
    return filename


def jfr_stop(pid):
    java_home = os.environ.get('JAVA_HOME')
    jcmd = java_home and os.path.join(java_home, 'bin', 'jcmd') or 'jcmd'
    subprocess.check_call([jcmd, str(pid), 'JFR.stop', 'name=rec'])


def jfr_extract_metrics(filename) -> Dict[str, Any]:
    java_home = os.environ.get('JAVA_HOME')
    java = java_home and os.path.join(java_home, 'bin', 'java') or 'java'
    cmd = [java, 'JfrOverview.java', filename]
    output = subprocess.check_output(cmd, universal_newlines=True)
    return json.loads(output)


def perf_stat(pid: int) -> Optional[subprocess.Popen]:
    cmd = [
        "perf",
        "stat",
        "-j",
        "-d",
        "-e", "branches,cache-misses,instructions,faults,context-switches",
        "-p", str(pid)
    ]
    try:
        return subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        return None


def perf_stat_results(proc: subprocess.Popen) -> Dict[str, Any]:
    # perf stat -j returns json lines like:
    # {"counter-value" : "0.445654", "unit" : "msec", "event" : "task-clock", "event-runtime" : 445654, "pcnt-running" : 100.00, "metric-value" : "0.575812", "metric-unit" : "CPUs utilized"}
    stdout, stderr = proc.communicate()
    metrics = {}
    for line in stderr.split("\n"):
        if line:
            event_metrics = json.loads(line)
            metrics[event_metrics["event"]] = event_metrics
    return metrics


def _run_spec(version, spec, result_hosts, env, settings, tmpdir, protocol):
    crate_dir = get_crate(version)
    settings.setdefault('cluster.name', str(uuid4()))
    results = []
    with Logger() as log, CrateNode(crate_dir=crate_dir, settings=settings, env=env) as n:
        n.start()
        benchmark_hosts = n.http_url
        if protocol == 'pg':
            pg_address = n.addresses['psql']
            benchmark_hosts = f'asyncpg://{pg_address.host}:{pg_address.port}'
        print(f'Running benchmark using protocol={protocol}, benchmark_hosts={benchmark_hosts}')
        do_run_spec(
            spec=spec,
            benchmark_hosts=benchmark_hosts,
            log=log,
            result_hosts=result_hosts,
            sample_mode='reservoir',
            action='setup'
        )
        jfr_file = jfr_start(n.process.pid, tmpdir)
        perf_proc = perf_stat(n.process.pid)
        log.result = results.append
        do_run_spec(
            spec=spec,
            benchmark_hosts=n.http_url,
            log=log,
            result_hosts=result_hosts,
            sample_mode='reservoir',
            action=['queries', 'load_data']
        )
        jfr_stop(n.process.pid)
        do_run_spec(
            spec=spec,
            benchmark_hosts=n.http_url,
            log=log,
            result_hosts=result_hosts,
            sample_mode='reservoir',
            action='teardown'
        )
    return (results, jfr_extract_metrics(jfr_file), perf_proc and perf_stat_results(perf_proc) or {})


def run_compare(v1,
                v2,
                spec,
                result_hosts,
                forks,
                env_v1,
                env_v2,
                settings_v1,
                settings_v2,
                show_plot,
                protocol):
    tmpdir = tempfile.mkdtemp()
    run_v1 = partial(_run_spec, v1, spec, result_hosts, env_v1, settings_v1, tmpdir, protocol)
    run_v2 = partial(_run_spec, v2, spec, result_hosts, env_v2, settings_v2, tmpdir, protocol)
    try:
        for _ in range(forks):
            results_v1, jfr_metrics1, stat_result1 = run_v1()
            results_v2, jfr_metrics2, stat_result2 = run_v2()
            compare_results(
                results_v1,
                jfr_metrics1,
                stat_result1,
                results_v2,
                jfr_metrics2,
                stat_result2,
                show_plot
            )
    finally:
        shutil.rmtree(tmpdir, True)


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
    p.add_argument('--env-v1', action='append',
                   help='Like --env but only applied to v1')
    p.add_argument('--env-v2', action='append',
                   help='Like --env but only applied to v2')
    p.add_argument('-s', '--setting', action='append',
                   help='Crate setting. E.g. -s path.data=/tmp/c1/')
    p.add_argument('--setting-v1', action='append',
                   help='Crate setting. Only applied to v1')
    p.add_argument('--setting-v2', action='append',
                   help='Crate setting. Only applied to v2')
    p.add_argument('--show-plot', type=bool, default=False)
    p.add_argument('--protocol', type=str, default='http',
                   help='Define which protocol to use, choices are (http, pg). Defaults to: http')
    args = p.parse_args()
    env = dict_from_kw_args(args.env)
    env_v1 = env.copy()
    env_v1.update(dict_from_kw_args(args.env_v1))
    env_v2 = env.copy()
    env_v2.update(dict_from_kw_args(args.env_v2))
    settings = dict_from_kw_args(args.setting)
    settings_v1 = settings.copy()
    settings_v1.update(dict_from_kw_args(args.setting_v1))
    settings_v2 = settings.copy()
    settings_v2.update(dict_from_kw_args(args.setting_v2))
    try:
        run_compare(
            args.v1,
            args.v2,
            args.spec,
            args.result_hosts,
            forks=max(1, args.forks),
            env_v1=env_v1,
            env_v2=env_v2,
            settings_v1=settings_v1,
            settings_v2=settings_v2,
            show_plot=args.show_plot,
            protocol=args.protocol,
        )
    except KeyboardInterrupt:
        print('Exiting..')


if __name__ == "__main__":
    main()
