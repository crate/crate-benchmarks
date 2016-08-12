create_table_stmt = """
create table t (
    x int,
    p int
)
clustered into 1 shards
partitioned by (p)
with (number_of_replicas = 0)"""

spec = Spec(
    setup=Instructions(statements=[create_table_stmt]),
    teardown=Instructions(statements=["drop table t"]),
    queries=[
        {
            'statement': 'insert into t (x, p) values (?, ?)',
            'bulk_args': [[i, i] for i in range(500)]
        }
    ]
)
