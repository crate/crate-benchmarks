import random
from functools import partial

spec = Spec(
    setup=Instructions(
        # no pk to use query instead of pk lookups
        statements=['create table t (id int, value string)'],
        data_files=[
            {
                'source': '../data/id_int_value_str.json',
                'target': 't',
                'bulk_size': 10000,
            }
        ]
    ),
    teardown=Instructions(statements=['drop table if exists t']),
    queries=[
        {
            'statement': 'select _uid from t where id = ?',
            'args': lambda: [random.randint(a=0, b=999999)],
            'iterations': 5000,
            'concurrency': 1
        },
        {
            'statement': 'select _uid from t where id = ?',
            'args': lambda: [random.randint(a=0, b=999999)],
            'iterations': 5000,
            'concurrency': 25
        },
        {
            'statement': 'select _uid from t limit 100',
            'iterations': 5000,
            'concurrency': 1
        },
        {
            'statement': 'select _uid from t limit 10000',
            'iterations': 5000,
            'concurrency': 1
        },
    ]
)
