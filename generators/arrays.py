#!/usr/bin/env python3

"""
Script to generate & print {"xs": ARRAY} records where ARRAY is generated based
on given ratios.

The array will contain positive integers.
"""

import argparse
import random
import ast
import json

MAX_INT = 2147483647


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--num',
        type=ast.literal_eval,
        help='Number of records to generate'
    )
    parser.add_argument(
        '--population',
        type=ast.literal_eval,
        help=('Python list containing the possible array lengths.'
              'E.g. [0, 1, 42] to create arrays of length 0, 1 or 42')
    )
    parser.add_argument(
        '--weight',
        type=ast.literal_eval,
        help=('Python list containing relative weights of how often the '
              'population elements should be choosen.'
              'E.g. [90, 5, 5] would result in most arrays being empty, '
              'if the population was set to [0, 1, 2], as 0 has the highest weight')
    )
    args = parser.parse_args()
    for choice in random.choices(args.population, args.weight, k=int(args.num)):
        l = []
        for _ in range(choice):
            l.append(random.randint(0, MAX_INT))
        print(json.dumps({"xs": l}))


if __name__ == "__main__":
    main()
