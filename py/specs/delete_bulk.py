
class BulkArgsGenerator:

    def __init__(self, bulk_size):
        self.count = 0
        self.bulk_size = bulk_size

    def __call__(self):
        start = self.count * self.bulk_size
        end = start + self.bulk_size
        self.count += 1
        return [[x] for x in range(start, end)]


spec = Spec(
    setup=Instructions(
        statements=[
            'create table t_delete_bulk (id integer primary key, value string) with (number_of_replicas=0)',
        ],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 't_delete_bulk',
            }
        ]
    ),
    teardown=Instructions(
        statements=[
            'drop table t_delete_bulk',
        ]
    ),
    queries=[
        {
            'statement': 'delete from t_delete_bulk where id = ?',
            'bulk_args': BulkArgsGenerator(200),
            'iterations': 1000,
        },
    ]
)
