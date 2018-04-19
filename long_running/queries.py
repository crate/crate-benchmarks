from time import time
from uuid import uuid4
from cr8.bench_spec import Spec, Instructions
from faker import Factory


def gen_args():
    faker = Factory.create()
    while True:
        args = (str(uuid4()), faker.name(), int(time() * 1000))
        yield args


def gen_bulk_args():
    args = gen_args()
    while True:
        bulk_args = [next(args) for i in range(200)]
        yield bulk_args


def get_queries():
    return (
        {
            'statement': 'INSERT INTO long_running_test (id, name, ts) VALUES (?, ?, ?)',
            'args': gen_args(),
            'concurrency': 50,
            'duration': 4 * 60 * 60
        },
        {
            'statement': 'SELECT * FROM long_running_test ORDER BY ts DESC LIMIT 50',
            'concurrency': 50,
            'duration': 1 * 60 * 60
        },
        {
            'statement': 'INSERT INTO long_running_test (id, name, ts) VALUES (?, ?, ?)',
            'bulk_args': gen_bulk_args(),
            'concurrency': 50,
            'duration': 2 * 60 * 60
        },
    )


spec = Spec(
    setup=Instructions(
        statements=[
            """CREATE TABLE long_running_test (
                id string primary key,
                name string,
                hour as date_format('%Y-%m-%d_%H', ts) primary key,
                ts timestamp
            ) CLUSTERED INTO 5 SHARDS PARTITIONED BY (hour)"""
        ]
    ),
    teardown=Instructions(statements=["DROP TABLE long_running_test"]),
    queries=get_queries()
)
