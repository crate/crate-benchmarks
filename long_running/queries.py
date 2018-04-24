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
            'statement': 'INSERT INTO lrt.t1 (id, name, ts) VALUES (?, ?, ?)',
            'args': gen_args(),
            'concurrency': 50,
            'duration': 4 * 60 * 60
        },
        {
            'statement': 'INSERT INTO lrt.t2 (id, name, ts) VALUES (?, ?, ?)',
            'args': gen_args(),
            'concurrency': 50,
            'iterations': 5000
        },
        {
            'statement': 'SELECT * FROM lrt.t1 ORDER BY ts DESC LIMIT 50',
            'concurrency': 50,
            'duration': 1 * 60 * 60
        },
        {
            'statement': 'INSERT INTO lrt.t1 (id, name, ts) VALUES (?, ?, ?)',
            'bulk_args': gen_bulk_args(),
            'concurrency': 50,
            'duration': 2 * 60 * 60
        },
        {
            'statement': ('SELECT lrt.t1.dev, lrt.t2.name '
                          'FROM lrt.t1 INNER JOIN lrt.t2 ON lrt.t1.dev = lrt.t2.dev'
                          'WHERE lrt.t1.dev = CAST(random() * 127 AS BYTE) '
                          'ORDER BY lrt.t2.name '
                          'LIMIT 100'),
            'concurrency': 25,
            'duration': 1 * 60 * 60
        },
        {
            'statement': ('SELECT name, count(*) FROM lrt.t1 '
                          'GROUP BY name ORDER BY 2 DESC LIMIT 500'),
            'concurrency': 25,
            'duration': 1 * 60 * 60
        }
    )


spec = Spec(
    setup=Instructions(
        statements=[
            """CREATE TABLE lrt.t1 (
                id STRING PRIMARY KEY,
                name STRING,
                hour AS date_format('%Y-%m-%d_%H', ts) PRIMARY KEY,
                ts TIMESTAMP,
                dev AS CAST(random() * 127 AS BYTE)
            ) CLUSTERED INTO 5 SHARDS PARTITIONED BY (hour)""",
            """CREATE TABLE lrt.t2 (
                id STRING PRIMARY KEY,
                name STRING,
                ts TIMESTAMP,
                dev AS CAST(random() * 127 AS BYTE)
            ) CLUSTERED INTO 5 SHARDS""",
        ]
    ),
    teardown=Instructions(statements=[
        "DROP TABLE lrt.t1",
        "DROP TABLE lrt.t2",
    ]),
    queries=get_queries()
)
