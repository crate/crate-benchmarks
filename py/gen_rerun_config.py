# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

import os
import re
import sys
import toml
import argparse
from urllib import request


NIGHTLY_RE = re.compile('.*>(?P<filename>crate-\d+\.\d+\.\d+-\d{12}-[a-z0-9]{7,}\.tar\.gz)<.*')

def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='')
    subparsers = parser.add_subparsers()
    parser.add_argument('--infile', '-i',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='base configuration file')
    parser.add_argument('--outfile', '-o',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='base configuration file')
    nightlies = subparsers.add_parser('nightlies')
    nightlies.add_argument('--num-releases', '-n',
                           type=int, required=True,
                           metavar='NUM',
                           help='number of releases')
    nightlies.set_defaults(func=gen_nightlies)
    versions = subparsers.add_parser('versions')
    versions.add_argument('--versions', '-v',
                          type=str, nargs='+', required=True,
                          metavar='VERSION',
                          help='list of version numbers')
    versions.set_defaults(func=gen_versions)
    return parser.parse_args()


def _read(fp):
    """
    Read base configuration file in toml format
    """
    return toml.loads(fp.read())


def _write(fp, data):
    """
    Write configuration file in toml format
    """
    return fp.write(toml.dumps(data))


def _extract_nightly_uri(base_uri, line):
    """
    Extract full URL from line
    """
    m = NIGHTLY_RE.match(line)
    if m:
        return base_uri + m.group('filename')


def gen_nightlies(ns):
    """
    Load URLs for nightly builds
    Returns a list of n nightly build URLs
    """
    base_uri = 'https://cdn.crate.io/downloads/releases/nightly/'
    versions = []
    with request.urlopen(base_uri) as r:
        versions = [_extract_nightly_uri(base_uri, line.decode('utf-8')) for line in r]
    return [v for v in reversed(versions) if v][:ns.num_releases]


def gen_versions(ns):
    """
    Returns the list provided by the CLI argument
    """
    return ns.versions


def main():
    ns = parse_args()
    conf = _read(ns.infile)
    conf['versions'] = ns.func(ns)
    _write(ns.outfile, conf)


if __name__ == '__main__':
    """
    Example usage:
    python gen_rerun_conf.py < tracks/latest.toml versions 0.55.4 0.55.5
    or:
    python gen_rerun_conf.py -i tracks/latest.toml -o tracks/rerun.toml nightlies -n 10

    For help run:
    python gen_rerun_conf.py --help
    """
    main()
