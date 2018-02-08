import string

create_table_stmt = """
    create table t (
        p int
    )
    clustered into 1 shards
    partitioned by (p)
    with (number_of_replicas=0)
"""


class BulkArgsGenerator:

    def __init__(self, bulk_size):
        self.count = 0
        self.bulk_size = bulk_size

    def __call__(self):
        start = self.count * self.bulk_size
        end = start + self.bulk_size
        self.count += 1
        return [[x, x] for x in range(start, end)]


def column_names():
    n = 0
    while True:
        n += 1
        for l in string.ascii_lowercase:
            yield 'd' + (l * n)


class statements:

    def __init__(self):
        self.names = column_names()

    def __call__(self):
        column_name = next(self.names)
        return f'insert into t (p, {column_name}) values (?, ?)'

    def __repr__(self):
        return 'insert into t (p, NEWCOL) values (?, ?)'


spec = Spec(
    setup=Instructions(statements=[create_table_stmt]),
    teardown=Instructions(statements=["drop table t"]),
    queries=[
        {
            'statement': statements(),
            'bulk_args': BulkArgsGenerator(20),
            'iterations': 30,
        }
    ]
)
