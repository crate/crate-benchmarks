# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

import toml
import json
import argparse
import contextlib
from datetime import datetime
from urllib.request import urlopen
from crate.client import connect


def update_commit_date(cursor, row):
    url = 'https://api.github.com/repos/crate/crate/commits/' + row[0]
    with contextlib.closing(urlopen(url)) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        date_str = data['commit']['author']['date']
        assert date_str
        commit_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').date()
        print('Updating hash {} with date {}'.format(row[0], commit_date))
        cursor.execute('''
            UPDATE benchmarks
            SET version_info['date'] = ?
            WHERE version_info['hash'] = ?
        ''', (commit_date, row[0], ))


def add_timestamp(ns, config={}):
    with connect(config.get('crate_hosts')) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT distinct(version_info['hash']) as hash
            FROM benchmarks
            WHERE version_info['date'] IS NULL
        ''')
        for row in cur.fetchall():
            update_commit_date(cur, row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf',
                        help='Path to config.toml',
                        type=argparse.FileType('r'), required=True)
    subparsers = parser.add_subparsers()

    parser_add_ts = subparsers.add_parser('add-timestamp')
    parser_add_ts.set_defaults(func=add_timestamp)

    args = parser.parse_args()
    config = toml.loads(args.conf.read())
    args.func(args, config)
