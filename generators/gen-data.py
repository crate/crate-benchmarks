#!/usr/bin/env python

"""
CLI to generate JSON records containing bigints with specified probability distribution
"""

import argparse
import json
import numpy as np

def uniform(n):
    values = np.random.randint(low=-1e10, high=1e10, size=n)
    for i in values:
        print(json.dumps({"x": str(i)}))

def normal(n):
    values = np.random.normal(loc=0, scale=1e10, size=n).astype(long)
    for i in values:
        print(json.dumps({"x": str(i)}))

def poisson(n):
    # Poisson distribution with a larger value for the mean (loc parameter)
    # will exhibit a bell shape just like normal distribution. Since normal
    # distribution is covered by a different data set generating function,
    # we use a small value for the loc to get a different shape (skewed to the right side).

    #Also, loc should not be 1 in order not to get a shape similar to exponential distribution.
    values = np.random.poisson(lam=2, size=n)
    for i in values:
        print(json.dumps({"x": str(i)}))

def exponential(n):
    values = np.random.exponential(scale=1e10, size=n).astype(long)
    for i in values:
        print(json.dumps({"x": str(i)}))

SUPPORTED_DISTRIBUTIONS = {
    'uniform': uniform,
    'normal': normal,
    'poisson': poisson,
    'exponential': exponential
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--num', type=int, help='Number of records to generate')
    parser.add_argument('--distribution', type=str, help='Probability distribution')
    args = parser.parse_args()
    try:
        generator_func = SUPPORTED_DISTRIBUTIONS[args.distribution]
        generator_func(args.num)
    except KeyError:
        print("distribution '" + args.distribution + "' is not supported.")

if __name__ == "__main__":
    main()
