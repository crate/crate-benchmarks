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

def str_generator(char_length=100, size=10):
    val_list = []
    for i in range(0,size):
        value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(char_length))
        val_list.append(value)
    return val_list
        

def id_generator(size=10):
    return [i for i in range(1, size + 1)]

def bulk_args_generator(bulk_size=10000):
    return list(zip(id_generator(bulk_size), str_generator(size=bulk_size)))

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
            'bulk_args': bulk_args_generator(),
            'iterations': 5000,
        }
    ]
)
