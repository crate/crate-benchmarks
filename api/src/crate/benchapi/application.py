# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

import json
import toml
from time import mktime
from datetime import datetime, strptime
from flask import Flask, g as app_globals, make_response, jsonify, request
from flask.ext.restful import Resource
from flask.ext.cors import CORS
from crate.client import connect
from crate.client.exceptions import ProgrammingError


app = Flask(__name__)
# apply CORS headers to all responses
CORS(app)


class CrateResource(Resource):

    def __init__(self):
        super().__init__()
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.cursor.close()

    @property
    def connection(self):
        if not 'conn' in app_globals:
            app_globals.conn = connect(app.config.get('crate_hosts', []),
                                       error_trace=app.config.get('debug', False))
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
    Resource for doc.benchmarks
    Supported method: GET
    """

    def get(self, group):
        param_from = request.args.get('from')
        param_to = request.args.get('to')
        params = []
        where_clause = []
        time_from = datetime.utcnow()
        time_to = datetime.utcnow()
        mapping = app.config.get('groups')

        if group and group in mapping:
            params.append(group)
            where_clause.append("WHERE meta['name'] = ANY(?)")
            params.append(mapping[group])
        else:
            return self.error('No or invalid benchmark group specified')

        if param_from:
            try:
                time_from = datetime.strptime(param_from, '%Y-%m-%d')
                where_clause.append("AND version_info['date'] >= ?")
                params.append(param_from)
            except ValueError as err:
                return self.error('Wrong date-time format in "from" parameter: {}'.format(err))

        if param_to:
            try:
                time_to = datetime.strptime(param_to, '%Y-%m-%d')
                where_clause.append("AND version_info['date'] <= ?")
                params.append(param_to)
            except ValueError as err:
                return self.error('Wrong date-time format in "to" parameter: {}'.format(err))

        timediff = time_to - time_from
        if timediff.days > 365:
            return self.error('Timespan is limited to 365 days', status=400)

        sql_query = """
                    SELECT ? as benchmark_group,
                           meta['name'] as spec_name,
                           version_info['number'] as build_version,
                           version_info['date'] as build_timestamp,
                           runtime_stats['min'] as min,
                           runtime_stats['median'] as median,
                           runtime_stats['max'] as max,
                           runtime_stats['stdev'] as stdev,
                           runtime_stats['variance'] as variance,
                           statement
                    FROM doc.benchmarks
                    {}
                    ORDER BY build_timestamp, spec_name, statement
                    """.format(" ".join(where_clause))

        try:
            app.logger.debug(sql_query)
            app.logger.debug(params)
            self.cursor.execute(sql_query, tuple(params))
        except ProgrammingError as e:
            return self.error(e.error_trace, 500)
        else:
            response = self.convert(self.cursor.description,
                                    self.cursor.fetchall())
            return (response, 200)


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

