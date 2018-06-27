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
import time
from functools import partial
from argparse import ArgumentParser, RawTextHelpFormatter
from cr8.insert_fake_data import DataFaker
from cr8.misc import parse_table
from cr8.bench_spec import Spec, Instructions
from crate.client import connect


def generate_one_param_function_clause(function_name,
                                       column,
                                       provider,
                                       abs_column=False):
    compare_to = provider()
    if abs_column is True:
        return f"{function_name}(abs({column}/({column} + 1))) != {compare_to}"
    else:
        return f"{function_name}({column}) != {compare_to}"


def generate_arc_function_clause(function_name, column, provider):
    """ Arc sin/cos/tan functions need the input to be in the [-1.0,1.0]
    interval. This generates a function clause that makes sure the arc
    functions are not called with invalid input.
    """

    compare_to = provider()
    return f"{function_name}(random()) != {compare_to}"


def generate_two_param_function_clause(function_name,
                                       column,
                                       provider,
                                       abs_column=False):
    second_arg = provider()
    compare_to = provider()
    if abs_column is True:
        return f"{function_name}(abs({column}/({column} + 1)), {second_arg}) != {compare_to}"
    else:
        return f"{function_name}({column}, {second_arg}) != {compare_to}"


# Array functions


def array_cat(data_faker, column, provider):
    generate_two_param_function_clause('ARRAY_CAT', column, provider)


def array_unique(data_faker, column, provider):
    generate_two_param_function_clause('ARRAY_UNIQUE', column, provider)


def array_difference(data_faker, column, provider):
    generate_two_param_function_clause('ARRAY_DIFFERENCE', column, provider)

# Geo functions


def within(data_faker, column, provider):
    arg2 = provider()
    return f"WITHIN({column}, {arg2})"


def distance(data_faker, column, provider):
    other_point = provider()
    dist = data_faker.fake.random_int(min=1, max=4000)
    return f"DISTANCE({column}, {other_point}) < {dist}"


def intersects(data_faker, column, provider):
    other_shape = provider()
    return f"INTERSECTS({column}, {other_shape})"


def latitude(data_faker, column, provider):
    gen_lat = data_faker.fake.random_int(min=1, max=90)
    return f"LATITUDE({column}) < {gen_lat}"


def longitude(data_faker, column, provider):
    gen_long = data_faker.fake.random_int(min=1, max=180)
    return f"LONGITUDE({column}) < {gen_long}"


def geohash(data_faker, column, provider):
    other_point = provider()
    return f"GEOHASH({column}) != GEOHASH({other_point})"

# Numbers functions


def any(data_faker, column, provider):
    gen_array = random.sample(range(0, 10), 6)
    return f"{column} = ANY({gen_array})"


def abs(data_faker, column, provider):
    compare_to = provider()
    return f"abs({column}/({column} + 1)) != {compare_to}"

def ceil(data_faker, column, provider):
    return generate_one_param_function_clause('CEIL', column, provider)


def floor(data_faker, column, provider):
    return generate_one_param_function_clause('FLOOR', column, provider)


def ln(data_faker, column, provider):
    return generate_one_param_function_clause('LN', column, provider, True)


def log(data_faker, column, provider):
    return generate_one_param_function_clause('LOG', column, provider, True)


def power(data_faker, column, provider):
    return generate_two_param_function_clause('POWER', column, provider)


def crate_random(data_faker, column, provider):
    gen_value = random.random()
    return f"RANDOM() < {gen_value}"


def round(data_faker, column, provider):
    return generate_one_param_function_clause('ROUND', column, provider)


def sqrt(data_faker, column, provider):
    return generate_one_param_function_clause('SQRT', column, provider, True)


def sin(data_faker, column, provider):
    return generate_one_param_function_clause('SIN', column, provider)


def asin(data_faker, column, provider):
    return generate_arc_function_clause('ASIN', column, provider)


def cos(data_faker, column, provider):
    return generate_one_param_function_clause('COS', column, provider)


def acos(data_faker, column, provider):
    return generate_arc_function_clause('ACOS', column, provider)


def tan(data_faker, column, provider):
    return generate_one_param_function_clause('TAN', column, provider)


def atan(data_faker, column, provider):
    return generate_arc_function_clause('ATAN', column, provider)

# String functions


def concat(data_faker, column, provider):
    return generate_two_param_function_clause('CONCAT', column, provider)


def format(data_faker, column, provider):
    return f"FORMAT('%s', {column}) = {column}"


def substr(data_faker, column, provider):
    return f"SUBSTR({column},0,1) < {column}"


def char_length(data_faker, column, provider):
    gen_length = data_faker.fake.random_int(min=1, max=80)
    return f"CHAR_LENGTH({column}) < {gen_length}"


def bit_length(data_faker, column, provider):
    gen_length = data_faker.fake.random_int(min=1, max=64)
    return f"BIT_LENGTH({column}) < {gen_length}"


def octet_length(data_faker, column, provider):
    gen_length = data_faker.fake.random_int(min=1, max=8)
    return f"OCTET_LENGTH({column}) < {gen_length}"


def lower(data_faker, column, provider):
    return generate_one_param_function_clause('LOWER', column, provider)


def upper(data_faker, column, provider):
    return generate_one_param_function_clause('UPPER', column, provider)


def sha1(data_faker, column, provider):
    return generate_one_param_function_clause('SHA1', column, provider)


def md5(data_faker, column, provider):
    return generate_one_param_function_clause('MD5', column, provider)


def match(data_faker, column, provider):
    match_value = provider()
    match_type = random.choice(MATCH_TYPES)
    return f"MATCH({column}, {match_value}) USING {match_type}"


def regexp_matches(data_faker, column, provider):
    compare_to = provider()
    return f"REGEXP_MATCHES({column}, '(a(.+)z)') = [{compare_to}]"

# Date/Time functions


def date_trunc(data_faker, column, provider):
    return f"DATE_TRUNC('day', {column}) < 30"


def date_format(data_faker, column, provider):
    return f"DATE_FORMAT('%e', {column}) != 13"


def every(x):
    return random.randint(1, x) == 1


def type_is_number(type):
    return type in NUMBER_TYPES


def operator_expresion_generator(op):
    def gen(column, val, dimensions):
        if dimensions:
            return f'{val} {op} ANY ("{column}")'
        return f'"{column}" {op} {val}'
    return gen


CONJUNCTIONS = ('AND', 'OR')
OP_SYMBOLS = (
    (operator_expresion_generator('=')),
    (operator_expresion_generator('!=')),
    (operator_expresion_generator('>')),
    (operator_expresion_generator('>=')),
    (operator_expresion_generator('<')),
    (operator_expresion_generator('<=')),
)
NUMBER_TYPES = (
    'byte',
    'short',
    'integer',
    'long',
    'float',
    'double',
)


def regex_generator(op):
    def gen(column, val, dimensions, quote_val=False):
        if dimensions:
            # regex operations are not supported with arrays so use an equality
            # expression with ANY instead
            return f'{val} = ANY ("{column}")'
        val = val.strip("'")  # strings are pre-quoted
        regexp_val = f"'.*{val}.*'"
        return f'"{column}" {op} {regexp_val}'
    return gen


LIKE_WILDCARDS = (
    '',
    '%',
    '_',
)


def like_generator(op):
    def gen(column, val, dimensions, quote_val=False):
        if dimensions:
            # LIKE is not supported with arrays so use an equality expression
            # with ANY instead
            return f'{val} = ANY ("{column}")'
        prefix = random.choice(LIKE_WILDCARDS)
        suffix = random.choice(LIKE_WILDCARDS)
        val = val.strip("'")  # strings are pre-quoted
        like_val = f"'{prefix}{val}{suffix}'"
        return f'"{column}" {op} {like_val}'
    return gen


ADDITIONAL_STRING_OPERATORS = (
    (regex_generator('~')),
    (like_generator('LIKE')),
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
    'string': OP_SYMBOLS + ADDITIONAL_STRING_OPERATORS,
    'boolean': OP_SYMBOLS,
}
SCALARS_BY_TYPE = {
    'array': (array_cat, array_unique, array_difference,),
    'geo_shape': (within, intersects,),
    'geo_point': (distance, latitude, longitude, geohash,),
    'number': (abs, ceil, floor, ln, log, power, crate_random, round, sqrt, sin,
               asin, cos, acos, tan, atan, any,),
    'string': (concat, format, substr, char_length, bit_length, octet_length,
               lower, upper, sha1, md5, match, regexp_matches,),
    'timestamp': (date_trunc, date_format,),
}
MATCH_TYPES = (
    'best_fields',
    'most_fields',
    'cross_fields',
    'phrase',
    'phrase_prefix'
)

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
) CLUSTERED INTO 2 SHARDS WITH (number_of_replicas = 0, refresh_interval = 0)
'''
IMPORT_DATA = "COPY benchmarks.query_tests FROM 's3://crate-stresstest-data/query-tests/*.json'"
TYPE_REQUIRES_QUOTES = ('string', 'ip', 'geo_shape')


def expr_with_operator(column, provider, inner_type, dimensions):
    val = provider()
    operators = OPERATORS_BY_TYPE.get(inner_type)
    if not operators or every(20):
        return f'{column} IS NULL'
    else:
        op = random.choice(operators)
        expr = op(column, val, dimensions)
        return expr


def add_quotes(f):
    return f"'{f()}'"


def rnd_expr(data_faker, columns):
    inner_type = None
    while not inner_type:
        column = random.choice(list(columns.keys()))
        data_type = columns[column]
        inner_type, *dimensions = data_type.split('_array')
    provider = data_faker.provider_for_column(column, inner_type)
    if inner_type in TYPE_REQUIRES_QUOTES:
        provider = partial(add_quotes, provider)
    use_scalar = every(15)
    if type_is_number(data_type):
        scalars = SCALARS_BY_TYPE.get('number', [])
    else:
        scalars = SCALARS_BY_TYPE.get(data_type, [])
    scalar = scalars and random.choice(scalars)
    if use_scalar and scalar:
        expr = scalar(data_faker, column, provider)
    else:
        expr = expr_with_operator(column, provider, inner_type, dimensions)
    if every(10):
        if every(2):
            return f'NOT {expr}'
        else:
            return f'NOT ignore3vl({expr})'
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


def generate_queries(data_faker, columns, schema, table, duration):
    start = time.time()
    while (time.time() - start < duration):
        yield generate_query(data_faker, columns, schema, table)


def queries_for_spec(columns):
    data_faker = DataFaker()
    queries = generate_queries(
        data_faker, columns, 'benchmarks', 'query_tests', duration=5 * 60 * 60)
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
    p.add_argument(
        '--duration', metavar='DURATION', type=int, help='duration in seconds',
        default=18000)
    return p.parse_args()


def main():
    args = parse_args()
    schema, table = parse_table(args.table)
    with connect(args.hosts) as conn:
        cursor = conn.cursor()
        columns = get_columns(cursor, schema, table)
        data_faker = DataFaker()
        for query in generate_queries(data_faker, columns, schema, table, args.duration):
            print(query)


spec = Spec(
    setup=Instructions(statements=[
        CREATE_TABLE,
        IMPORT_DATA,
        "refresh table benchmarks.query_tests",
        "optimize table benchmarks.query_tests"
    ]),
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
