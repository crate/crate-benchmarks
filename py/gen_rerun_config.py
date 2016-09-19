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
    parser.add_argument('--infile', '-i',
                        type=argparse.FileType('r'), default=sys.stdin,
                        help='base configuration file')
    parser.add_argument('--outfile', '-o',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='base configuration file')
    parser.add_argument('--num-releases', '-n',
                        type=int, default=30,
                        help='number of releases')
    return parser.parse_args()


def _extract_nightly_uri(base_uri, line):
    """
    Extract full URL from line
    """
    m = NIGHTLY_RE.match(line)
    if m:
        return base_uri + m.group('filename')


def fetch(n):
    """
    Load URLs for nightly builds
    Returns a list of n nightly build URLs
    """
    base_uri = 'https://cdn.crate.io/downloads/releases/nightly/'
    versions = []
    with request.urlopen(base_uri) as r:
        versions = [_extract_nightly_uri(base_uri, line.decode('utf-8')) for line in r]
    return [v for v in reversed(versions) if v][:n]

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


def main():
    ns = parse_args()
    conf = _read(ns.infile)
    conf['versions'] = fetch(ns.num_releases)
    _write(ns.outfile, conf)


if __name__ == '__main__':
    """
    Example usage:
    python gen_rerun_conf.py < tracks/latest.toml
    or:
    python gen_rerun_conf.py -i tracks/latest.toml -o tracks/rerun.toml -n 10

    For help run:
    python gen_rerun_conf.py --help
    """
    main()
