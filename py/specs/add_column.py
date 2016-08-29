create_table_stmt = """
    create table t_add_column (
      id integer,
      value string
    ) with (
      number_of_replicas=0
    )
"""

drop_table_stmt = """
    drop table t_add_column
"""

class ColumnGenerator:

    def __init__(self, prefix):
        self.prefix = prefix
        # this will add a new column every time a new value is inserted
        self.stmt = 'insert into t_add_column ("{}_{}") values (?)'
        self.count = 0

    def __call__(self):
        self.count += 1
        return self.stmt.format(self.prefix, self.count)

    def __str__(self):
        return self.stmt


spec = Spec(
    setup=Instructions(
        statements=[create_table_stmt],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 't_add_column',
            }
        ]
    ),
    teardown=Instructions(
        statements=[drop_table_stmt]
    ),
    queries=[
        {
            'statement': ColumnGenerator('str_col'),
            'iterations': 5000,
            'args': ('value for new string column', ),
        },
    ]
)
