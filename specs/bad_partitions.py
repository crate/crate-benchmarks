#!/usr/bin/env python3

"""cr8 spec to create too many partitions."""

from cr8.bench_spec import Spec, Instructions  # type: ignore
from itertools import cycle
from uuid import uuid4


CREATE_TABLE = '''
CREATE TABLE tp (
    id STRING PRIMARY KEY,
    p INTEGER PRIMARY KEY
) CLUSTERED INTO 10 SHARDS PARTITIONED BY (p)
'''


def _queries():
    num = 400
    c = cycle(list(range(num)))
    yield {
        'statement': 'insert into tp (id, p) values (?, ?)',
        'args': lambda: [str(uuid4()), next(c)],
        'concurrency': 25,
        'iterations': int(1e6)
    }


spec = Spec(
    setup=Instructions(statements=[CREATE_TABLE]),
    teardown=Instructions(statements=["drop table if exists tp"]),
    queries=_queries(),
)


if __name__ == "__main__":
    for q in _queries():
        for _ in range(5):
            print(q['args']())
