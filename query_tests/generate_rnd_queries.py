#!/usr/bin/env python

"""
Script that will print randomly generated queries on stdout forever

Example usage:
    cr8 run-spec generate_rnd_queries.py localhost:4200

or:

    cr8 run-spec generate_rnd_queries.py localhost:4200 --action setup
    python generate_rnd_queries.py | head -n 5 | cr8 timeit -r 10 -w 0
"""

import random
from argparse import ArgumentParser, RawTextHelpFormatter
from cr8.insert_fake_data import DataFaker
from cr8.misc import parse_table
from cr8.bench_spec import Spec, Instructions
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

CREATE_TABLE = '''
CREATE TABLE benchmarks.query_tests (
  id string primary key,
  sboolean boolean,
  sbyte byte,
  sshort short,
  sinteger integer,
  slong long,
  sfloat float,
  sdouble double,
  sstring string,
  sip ip,
  stimestamp timestamp,
  sgeo_point geo_point,
  sgeo_shape geo_shape,
  aboolean array(boolean),
  abyte array(byte),
  ashort array(short),
  ainteger array(integer),
  along array(long),
  afloat array(float),
  adouble array(double),
  astring array(string),
  aip array(ip),
  atimestamp array(timestamp),
  ageo_point array(geo_point),
  ageo_shape array(geo_shape)
) CLUSTERED INTO 2 SHARDS WITH (number_of_replicas = 0)
'''


def rnd_expr(data_faker, columns):
    operators = None
    while not operators:
        column = random.choice(list(columns.keys()))
        data_type = columns[column]
        inner_type, *dims = data_type.split('_array')
        operators = OPERATORS_BY_TYPE.get(inner_type)
    op = random.choice(operators)
    provider = data_faker.provider_for_column(column, inner_type)
    val = provider()
    if inner_type in ('string', 'ip'):
        val = f"'{val}'"
    if dims:
        expr = f'{val} {op} ANY ("{column}")'
    else:
        expr = f'"{column}" {op} {val}'
    if random.randint(0, 10) == 1:
        return f'NOT {expr}'
    else:
        return expr


def generate_query(data_faker, columns, schema, table):
    expr_range = range(random.randint(1, 5))
    expressions = []
    for expr in (rnd_expr(data_faker, columns) for _ in expr_range):
        if expressions:
            expressions.append(random.choice(CONJUNCTIONS))
        expressions.append(expr)
    filter_ = ' '.join(expressions)
    return f'SELECT count(*) FROM "{schema}"."{table}" WHERE {filter_};'


def generate_queries(data_faker, columns, schema, table):
    while True:
        yield generate_query(data_faker, columns, schema, table)


def queries_for_spec(columns):
    data_faker = DataFaker()
    queries = generate_queries(data_faker, columns, 'benchmarks', 'query_tests')
    for query in queries:
        yield {
            'statement': query,
            'iterations': 50
        }


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


spec = Spec(
    setup=Instructions(statements=[CREATE_TABLE]),
    teardown=Instructions(statements=[
        "DROP TABLE benchmarks.query_tests",
    ]),
    queries=queries_for_spec(columns={
        'id': 'string',
        'sboolean': 'boolean',
        'sbyte': 'byte',
        'sshort': 'short',
        'sinteger': 'integer',
        'slong': 'long',
        'sfloat': 'float',
        'sdouble': 'double',
        'sstring': 'string',
        'sip': 'ip',
        'stimestamp': 'timestamp',
        'sgeo_point': 'geo_point',
        'sgeo_shape': 'geo_shape',
        'aboolean': 'boolean_array',
        'abyte': 'byte_array',
        'ashort': 'short_array',
        'ainteger': 'integer_array',
        'along': 'long_array',
        'afloat': 'float_array',
        'adouble': 'double_array',
        'astring': 'string_array',
        'aip': 'ip_array',
        'atimestamp': 'timestamp_array',
        'ageo_point': 'geo_point_array',
        'ageo_shape': 'geo_shape_array',
    })
)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
