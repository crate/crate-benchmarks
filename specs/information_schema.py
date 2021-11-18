create_table_stmt = """create table table_{} (name string)
                       clustered into 1 shards
                       with (number_of_replicas=0)"""

drop_table_stmt = "drop table if exists table_{}"

spec = Spec(
    setup=Instructions(statements=[create_table_stmt.format(i) for i in range(150)]),
    teardown=Instructions(statements=[drop_table_stmt.format(i) for i in range(150)]),
    queries=[
        {
            'statement': "select * from information_schema.tables",
            'iterations': 100000,
        }
    ]
)
