create_table_stmt = """
    create table t (
        x int,
        p int
    )
    clustered into 1 shards
    partitioned by (p)
    with (number_of_replicas=0, refresh_interval=0)
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


spec = Spec(
    setup=Instructions(statements=[create_table_stmt]),
    teardown=Instructions(statements=["drop table if exists t"]),
    queries=[
        {
            'statement': 'insert into t (x, p) values (?, ?)',
            'bulk_args': BulkArgsGenerator(20),
            'iterations': 30,
        }
    ]
)
