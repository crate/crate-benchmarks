#!/usr/bin/env python3

import os
import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict
from util import format_byte_size


KNOWN_EXTENSIONS = {
    'si',
    'fnm',
    'fdx',
    'fdt',
    'tim',
    'tip',
    'doc',
    'pos',
    'pay',
    'nvd',
    'nvm',
    'dvd',
    'dvm',
    'tvx',
    'tvd',
    'liv',
    'dii',
    'dim',
}


def gather_sizes(path):
    sizes = defaultdict(int)
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            path = Path(dirpath, filename)
            size = path.stat().st_size
            ext = path.suffix.lstrip('.')
            if ext in KNOWN_EXTENSIONS:
                sizes[ext] += size
    return sizes


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', type=str, choices=('json', 'text'), default='json')
    parser.add_argument(
        '--path',
        type=str,
        help='Path to CrateDB data folder',
        required=True
    )
    parser.add_argument('--outfile', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args(argv)
    sizes = gather_sizes(args.path)

    # https://lucene.apache.org/core/8_9_0/core/org/apache/lucene/codecs/lucene87/package-summary.html#package.description
    if args.format == 'json':
        args.outfile.write(json.dumps(sizes, indent=4))
    else:
        args.outfile.write(f'''
Segment Info:        {format_byte_size(sizes['si'])}
Fields:              {format_byte_size(sizes['fnm'])}
Field Index:         {format_byte_size(sizes['fdx'])}
Field Data:          {format_byte_size(sizes['fdt'])}
Term Dictionary:     {format_byte_size(sizes['tim'])}
Term Index:          {format_byte_size(sizes['tip'])}
Frequencies:         {format_byte_size(sizes['doc'])}
Positions:           {format_byte_size(sizes['pos'])}
Payloads:            {format_byte_size(sizes['pay'])}
Norms:               {format_byte_size(sizes['nvd'])}
                     {format_byte_size(sizes['nvm'])}
Per-Document Values: {format_byte_size(sizes['dvd'])}
                     {format_byte_size(sizes['dvm'])}
Term Vector Index:   {format_byte_size(sizes['tvx'])}
Term Vector Data:    {format_byte_size(sizes['tvd'])}
Live Documents:      {format_byte_size(sizes['liv'])}
Point values:        {format_byte_size(sizes['dii'])}
                     {format_byte_size(sizes['dim'])}
''')


if __name__ == '__main__':
    main()
