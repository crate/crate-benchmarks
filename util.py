#!/usr/bin/env python3


def dict_from_kw_args(args: list[str]) -> dict[str, str]:
    """ Return a dictionary based on ['key=val'] entries

    >>> dict_from_kw_args(['x=10', 'y=foo'])
    {'x': '10', 'y': 'foo'}
    """
    if args:
        return dict(i.split('=', maxsplit=1) for i in args)
    else:
        return {}


def perc_diff(v1, v2):
    """ Return the difference between two number as percentage

    >>> perc_diff(10, 15)
    40.0

    >>> perc_diff(0, 0)
    0.0
    """

    try:
        return (abs(v1 - v2) / ((v1 + v2) / 2.0)) * 100
    except ZeroDivisionError:
        return 0.0


def human_readable_byte_size(value):
    """ Turn value into a (file_size, byte_size_unit) tuple.

    `file_size` is `value` adjusted to match the unit.

    >>> human_readable_byte_size(1024 * 17)
    (17.0, 'KB')
    """
    for count in ('Bytes', 'KB', 'MB', 'GB'):
        if value < 1024.0:
            return (value, count)
        value /= 1024.0
    return (value, 'TB')


def format_byte_size(value):
    file_size, unit = human_readable_byte_size(value)
    return f'{file_size:8.2f} {unit}'


if __name__ == '__main__':
    import doctest
    doctest.testmod()
