create_table_stmt = """
    create table t_any (
        id integer primary key,
        value string
    ) with (number_of_replicas=0)
"""

drop_table_stmt = """
    drop table t_any
"""

spec = Spec(
    setup=Instructions(
        statements=[create_table_stmt],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 't_any',
            }
        ]
    ),
    teardown=Instructions(
        statements=[drop_table_stmt]
    ),
    queries=[
        {
            'statement': 'select * from t_any where value = any(?)',
            'args': ([str(i) for i in range(500)], ),
            'iterations': 5000,
        },
        {
            'statement': 'select * from t_any where value != any(?)',
            'args': ([str(i) for i in range(500)], ),
            'iterations': 5000,
        },
    ]
)
