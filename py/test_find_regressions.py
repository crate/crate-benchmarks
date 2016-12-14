#!/usr/bin/env python3

import find_regressions
import doctest


def main():
    doctest.testmod(find_regressions)


if __name__ == "__main__":
    main()
