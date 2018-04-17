#!/usr/bin/env python

import sys
import json
import numpy as np
from argparse import ArgumentParser, FileType
from scipy import stats


def get_lineregress(data):
    if not isinstance(data, list):
        raise ValueError('Input must be a list of values')
    x = np.array(range(len(data)))
    y = np.array(data)
    return stats.linregress(x, y)


def main():
    p = ArgumentParser()
    p.add_argument(
        '--input', dest='lines', type=FileType('r'), default=sys.stdin)
    args = p.parse_args()
    result = 0
    for line in args.lines:
        d = json.loads(line)
        lineregress = get_lineregress(d)
        print(json.dumps({
            'slope': lineregress.slope,
            'intercept': lineregress.intercept,
            'rvalue': lineregress.rvalue,
            'pvalue': lineregress.pvalue,
            'stderr': lineregress.stderr
        }, indent=4))
        result = 1 if (result == 1 or lineregress.slope >= 0.1) else 0
    sys.exit(result)

if __name__ == "__main__":
    main()
