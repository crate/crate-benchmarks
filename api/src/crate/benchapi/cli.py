# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

import toml
import argparse
from flask.ext.restful import Api
from .application import app, Result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf',
                        help='Path to config.toml',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('--http-port', help='HTTP port of the Flask application',
                        type=int, default=8080)
    parser.add_argument('--http-host', help='HTTP host of the Flask application',
                        type=str, default='localhost')
    parser.add_argument('--debug', help='Start HTTP server in debug mode',
                        action='store_true')
    return parser.parse_args()


def run():
    args = parse_args()
    config = toml.loads(args.conf.read())
    api = Api(app)
    api.add_resource(Result, '/result/<group>', endpoint='result')
    app.config.update(config)
    app.run(host=args.http_host, port=args.http_port, debug=args.debug)
