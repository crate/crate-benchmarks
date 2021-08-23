#!/usr/bin/env python3

"""
Script to launch two different CrateDB nodes, run the setup of a spec file and
compare the disk space requirements.
"""

import argparse
from uuid import uuid4
from cr8.run_crate import get_crate, CrateNode
from cr8.run_spec import do_run_spec
from cr8.log import Logger
from crate.client import connect
from crate.crash.tabulate import tabulate

from util import dict_from_kw_args, perc_diff, human_readable_byte_size
from lucene_disk_usage import gather_sizes


def optimize_tables(cursor):
    cursor.execute('''
SELECT
    table_schema,
    table_name
FROM
    information_schema.tables
WHERE
    table_schema NOT IN ('sys', 'blob', 'pg_catalog', 'information_schema')
''')
    rows = list(cursor.fetchall())
    for schema, table in rows:
        cursor.execute(f'optimize table "{schema}"."{table}" with (flush = true, max_num_segments = 1)')


def run(version, spec, env, settings):
    crate_dir = get_crate(version)
    settings.setdefault('cluster.name', str(uuid4()))
    with Logger() as log, CrateNode(crate_dir=crate_dir, settings=settings, env=env) as n:
        n.start()
        do_run_spec(
            spec=spec,
            log=log,
            sample_mode='reservoir',
            benchmark_hosts=n.http_url,
            action='setup'
        )
        with connect(n.http_url) as conn:
            optimize_tables(conn.cursor())
        return gather_sizes(n.data_path)


def run_comparison(version1,
                   version2,
                   spec,
                   result_hosts,
                   env_v1,
                   env_v2,
                   settings_v1,
                   settings_v2):
    v1 = run(version1, spec, env_v1, settings_v1)
    v2 = run(version2, spec, env_v2, settings_v2)
    print(f'Version1: {version1}')
    print(f'Version2: {version2}')
    headers = ('Description', 'Version 1', 'Unit', 'Version 2', 'Unit', 'Diff')
    keys = [
        ('Segment Info', 'si'),
        ('Fields', 'fnm'),
        ('Field Index', 'fdx'),
        ('Field Data', 'fdt'),
        ('Term Dictionary', 'tim'),
        ('Term Index', 'tip'),
        ('Frequencies', 'doc'),
        ('Positions', 'pos'),
        ('Payloads', 'pay'),
        ('Norms (nvd)', 'nvd'),
        ('Norms (nvm)', 'nvm'),
        ('Per-Doc Values (dvd)', 'dvd'),
        ('Per-Doc Values (dvm)', 'dvm'),
        ('Term Vector Index', 'tvx'),
        ('Term Vector Data', 'tvd'),
        ('Live Documents', 'liv'),
        ('Point values', 'dii')
    ]

    def mk_row(key):
        description, ext = key
        val1 = v1[ext]
        val2 = v2[ext]
        v1_size, v1_unit = human_readable_byte_size(val1)
        v2_size, v2_unit = human_readable_byte_size(val2)
        return (description, v1_size, v1_unit, v2_size, v2_unit, perc_diff(val1, val2))
    rows = [mk_row(key) for key in keys]
    print(tabulate(rows, headers=headers, floatfmt=".2f"))


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

    run_comparison(
        args.v1,
        args.v2,
        args.spec,
        args.result_hosts,
        env_v1=env_v1,
        env_v2=env_v2,
        settings_v1=settings_v1,
        settings_v2=settings_v2
    )


if __name__ == '__main__':
    main()
