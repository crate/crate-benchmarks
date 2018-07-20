#!/usr/bin/env python

"""
CLI to generate JSON records with a given cardinality ratio
"""

import argparse
import random
import json
import ast
from itertools import cycle


def to_int(s):
    """ converts a string to an integer

    >>> to_int('1_000_000')
    1000000

    >>> to_int('1e6')
    1000000

    >>> to_int('1000')
    1000
    """
    try:
        return int(s.replace('_', ''))
    except ValueError:
        return int(ast.literal_eval(s))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--num', type=to_int, help='Number of records to generate')
    parser.add_argument('--ratio', type=float, help='Cardinality ratio')
    args = parser.parse_args()
    num_unique = args.num * args.ratio
    values = cycle(range(int(num_unique)))
    for _ in range(args.num):
        print(json.dumps({"x": str(next(values))}))


if __name__ == "__main__":
    main()
