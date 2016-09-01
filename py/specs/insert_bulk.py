import random, string

create_table_stmt = """
    create table t_bulk_insert (
      id integer,
      value string
    ) with (
      number_of_replicas=0
    )
"""

drop_table_stmt = """
    drop table t_bulk_insert
"""

def random_string(char_length=100):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(char_length))

def gen_args(x):
    return (x+1, random_string(), )

spec = Spec(
    setup=Instructions(
        statements=[create_table_stmt]
    ),
    teardown=Instructions(
        statements=[drop_table_stmt]
    ),
    queries=[
        {
            'statement': 'insert into t_bulk_insert (id, value) values (?,?)',
            'bulk_args': [gen_args(x) for x in range(10000)],
            'iterations': 5000,
        }
    ]
)
