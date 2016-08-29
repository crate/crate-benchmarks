import random, string

class BulkArgsGenerator:

    def __init__(self, bulk_size):
        self.count = 0
        self.bulk_size = bulk_size

    def __call__(self):
        start = self.count * self.bulk_size
        end = start + self.bulk_size
        self.count += 1
        return [[x % 100, random_string(100)] for x in range(start, end)]


create_table_stmt = """
    create table part_bulk_insert (
        id int,
        value string
    )
    partitioned by (id)
    with (number_of_replicas=0)
"""

insert_stmt = """insert into part_bulk_insert (id, value) values ({0}, '{1}')"""

def random_string(char_length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(char_length))

def setup_statements(partitions):
    setup_stmts = [create_table_stmt]
    for i in range(partitions):
        setup_stmts.append(insert_stmt.format(str(i), random_string(100)))
    return setup_stmts


spec = Spec(
    setup=Instructions(
        statements=setup_statements(100)
    ),
    teardown=Instructions(
        statements=['drop table part_bulk_insert']
    ),
    queries=[
        {
            'statement': 'insert into part_bulk_insert (id, value) values (?, ?)',
            'bulk_args': BulkArgsGenerator(1000),
            'iterations': 500, 
        }
    ]
)
