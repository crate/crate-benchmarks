#!/usr/bin/env python

"""
Script that will print randomly generated queries on stdout forever

Example usage:
     python generate_rnd_queries.py | head -n 5 | cr8 timeit -r 10 -w 0
"""

import random
from argparse import ArgumentParser, RawTextHelpFormatter
from cr8.insert_fake_data import DataFaker
from cr8.misc import parse_table
from crate.client import connect


CONJUNCTIONS = ('AND', 'OR')
OP_SYMBOLS = (
    '=',
    '!=',
    '>',
    '>=',
    '<',
    '<=',
)
OPERATORS_BY_TYPE = {
    'byte': OP_SYMBOLS,
    'short': OP_SYMBOLS,
    'integer': OP_SYMBOLS,
    'long': OP_SYMBOLS,
    'float': OP_SYMBOLS,
    'double': OP_SYMBOLS,
    'timestamp': OP_SYMBOLS,
    'ip': OP_SYMBOLS,
    'string': OP_SYMBOLS,
    'boolean': OP_SYMBOLS,
}


def rnd_expr(data_faker, columns):
    column = random.choice(list(columns.keys()))
    data_type = columns[column]
    inner_type, *dims = data_type.split('_array')
    operators = OPERATORS_BY_TYPE.get(inner_type)
    if not operators:
        return None
    op = random.choice(operators)
    provider = data_faker.provider_for_column(column, inner_type)
    val = provider()
    if inner_type in ('string', 'ip'):
        val = f"'{val}'"
    if dims:
        return f'{val} {op} ANY ("{column}")'
    else:
        return f'"{column}" {op} {val}'


def generate_query(data_faker, columns, schema, table):
    expr_range = range(random.randint(1, 5))
    expressions = []
    for expr in (rnd_expr(data_faker, columns) for _ in expr_range):
        if not expr:
            continue
        if expressions:
            expressions.append(random.choice(CONJUNCTIONS))
        expressions.append(expr)
    if expressions:
        filter_ = ' '.join(expressions)
    else:
        filter_ = '1 = 1'
    return f'SELECT count(*) FROM "{schema}"."{table}" WHERE {filter_};'


def generate_queries(data_faker, columns, schema, table):
    while True:
        yield generate_query(data_faker, columns, schema, table)


def get_columns(cursor, schema, table):
    """ Return a dict with column types by column name """
    cursor.execute('''
SELECT
    column_name,
    data_type
FROM
    information_schema.columns
WHERE
    table_schema = ?
    AND table_name = ?
''', (schema, table))
    return {cn: dt for (cn, dt) in cursor.fetchall()}


def parse_args():
    p = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter)
    p.add_argument(
        '--hosts', metavar='HOSTS', type=str, default='localhost:4200')
    p.add_argument(
        '--table', metavar='TABLE', type=str, default='benchmarks.query_tests')
    return p.parse_args()


def main():
    args = parse_args()
    schema, table = parse_table(args.table)
    with connect(args.hosts) as conn:
        cursor = conn.cursor()
        columns = get_columns(cursor, schema, table)
        data_faker = DataFaker()
        for query in generate_queries(data_faker, columns, schema, table):
            print(query)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
