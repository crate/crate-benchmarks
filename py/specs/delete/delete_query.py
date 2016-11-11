import random
from functools import partial

spec = Spec(
    setup=Instructions(
        statements=['create table t (x int)'],
        data_files=[
            {
                'source': '../data/t_0.json',
                'target': 't',
                'bulk_size': 10000,
                'num_records': 5000000
            }
        ]
    ),
    teardown=Instructions(statements=['drop table t']),
    queries=[
        {
            'statement': 'delete from t where x = ?',
            'args': lambda: [random.randint(a=0, b=9999)],
            'iterations': 5000,
            'concurrency': 100
        }
    ]
)
