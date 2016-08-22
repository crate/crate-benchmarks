# vim: set fileencodings=utf-8
# -*- coding: utf-8; -*-

import json
import argparse
from time import mktime, strptime
from datetime import datetime

from crate.client import connect

from flask import (
    Flask,
    g as app_globals,
    make_response,
    jsonify,
    request
)
from flask.ext.restful import Api, Resource
from flask.ext.cors import CORS

# Default Hosts, if no hosts are specified
STAGING_HOSTS = [
    'st1.p.fir.io:4200',
    'st2.p.fir.io:4200',
    'st3.p.fir.io:4200',
    'st4.p.fir.io:4200',
    'st5.p.fir.io:4200',
    'st6.p.fir.io:4200',
    'st7.p.fir.io:4200',
    'st8.p.fir.io:4200',
]

app = Flask(__name__)
# apply CORS headers to all responses
CORS(app)

class CrateResource(Resource):

    def __init__(self):
        super(CrateResource, self).__init__()
        self.cursor = self.connection.cursor()

    @property
    def connection(self):
        if not 'conn' in app_globals:
            app_globals.conn = connect(app.config['CRATE_HOSTS'],
                                       error_trace=app.config['DEBUG'])
        return app_globals.conn

    def error(self, message, status=404):
        return (dict(
            error=message,
            status=status,
        ), status)

    def convert(self, description, results):
        cols = [c[0] for c in description]
        return [dict(zip(cols, r)) for r in results]


class Result(CrateResource):
    """
    Resource for benchmark.history
    Supported method: GET
    """

    def get(self, benchmark_group):
        param_from = request.args.get('from')
        param_to = request.args.get('to')
        params = []
        time_from = datetime.now()
        time_to = datetime.now()

        if benchmark_group:
            where_clause = " WHERE benchmark_group = ?"
            params.append(benchmark_group)
        else:
            return self.error('No benchmark_group specified')

        if param_from:
            try:
                time_from = datetime.fromtimestamp(mktime(strptime(param_from, '%Y-%m-%d')))
                where_clause += " AND build_timestamp >= ?"
                params.append(param_from)
            except ValueError as err:
                return self.error('wrong date-time format in "from" parameter: {}'.format(err))

        if param_to:
            try:
                time_to = datetime.fromtimestamp(mktime(strptime(param_to, '%Y-%m-%d')))
                where_clause += " AND build_timestamp <= ?"
                params.append(param_to)
            except ValueError as err:
                return self.error('wrong date-time format in "to" parameter: {}'.format(err))

        timediff = time_to - time_from
        if timediff.days > 365:
            return self.error('the max. timespan is limited to 365 days', status=400)

        sql_query = """
                    SELECT benchmark_group as "group",
                           method,
                           date_trunc('day', build_timestamp) as "timestamp",
                           build_version as "version",
                           benchmark_values['round_avg'] as "avg",
                           benchmark_values['round_stddev'] as "stddev"
                    FROM benchmark.history
                    {0}
                    ORDER BY build_timestamp, method
                    """.format(where_clause)

        self.cursor.execute(sql_query, tuple(params))
        response = self.convert(self.cursor.description,
                                self.cursor.fetchall())

        return (response, 200)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

def splitter(hosts):
    return hosts.split(',')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--http-port', help='HTTP port',
                        type=int, default=8080)
    parser.add_argument('--http-host', help='HTTP host',
                        type=str, default='localhost')
    parser.add_argument('--crate-hosts', help='Crate hosts',
                        type=splitter, default=STAGING_HOSTS)
    parser.add_argument('--debug', help='Start HTTP server in debug mode',
                        action='store_true')
    return parser.parse_args()

def run():
    args = parse_args()
    api = Api(app)
    api.add_resource(Result, '/result/<benchmark_group>', endpoint='result')
    app.config.update(
        CRATE_HOSTS=args.crate_hosts,
        DEBUG=args.debug,
    )
    app.run(host=args.http_host, port=args.http_port, debug=args.debug)
