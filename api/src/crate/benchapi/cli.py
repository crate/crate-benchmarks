# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

import toml
import json
import argparse
import contextlib
from datetime import datetime
from urllib.request import urlopen
from urllib.error import HTTPError
from flask.ext.restful import Api
from .application import app, Result
from crate.client import connect


def _fetch_commit_date(commit_hash):
    url = 'https://api.github.com/repos/crate/crate/commits/' + commit_hash
    with contextlib.closing(urlopen(url)) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        date_str = data['commit']['author']['date']
        assert date_str
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').date()


def _update_commit_date(cursor, commit_hash, commit_date):
    print('Updating hash {} with date {}'.format(commit_hash, commit_date))
    cursor.execute('''
        UPDATE benchmarks
        SET version_info['date'] = ?
        WHERE version_info['hash'] = ?
    ''', (commit_date, commit_hash, ))


def add_timestamp(ns, config={}):
    """
    Resolve timestamp of Github commit hash and store it in doc.benchmarks table.
    """
    with connect(config.get('crate_hosts')) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT distinct(version_info['hash']) as hash
            FROM benchmarks
            WHERE version_info['date'] IS NULL
        ''')
        for row in cur.fetchall():
            try:
                commit_date = _fetch_commit_date(row[0])
                _update_commit_date(cur, row[0], commit_date)
            except HTTPError:
                print('Failed to update commit date for hash {}'.format(row[0]))


def run_server(ns, config={}):
    """
    Run API that reads benchmark result data from Crate cluster.
    """
    api = Api(app)
    api.add_resource(Result, '/result/<group>', endpoint='result')
    app.config.update(config)
    app.run(host=ns.http_host, port=ns.http_port, debug=ns.debug)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf',
                        help='Path to config.toml',
                        type=argparse.FileType('r'), required=True)
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser('server')
    parser_run.add_argument('--http-port', help='HTTP port of the Flask application',
                        type=int, default=8080)
    parser_run.add_argument('--http-host', help='HTTP host of the Flask application',
                        type=str, default='localhost')
    parser_run.add_argument('--debug', help='Start HTTP server in debug mode',
                        action='store_true')
    parser_run.set_defaults(func=run_server)

    parser_add_ts = subparsers.add_parser('add-timestamp')
    parser_add_ts.set_defaults(func=add_timestamp)

    args = parser.parse_args()
    config = toml.loads(args.conf.read())
    args.func(args, config)
