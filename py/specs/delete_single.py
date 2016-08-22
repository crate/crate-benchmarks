
class ArgsGenerator:

    def __init__(self, n=1):
        self.count = 0
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [x]


spec = Spec(
    setup=Instructions(
        statements=[
            'create table t_delete_single (id integer primary key, value string) with (number_of_replicas=0)',
        ],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 't_delete_single',
            }
        ]
    ),
    teardown=Instructions(
        statements=[
            'drop table t_delete_single',
        ]
    ),
    queries=[
        {
            'statement': 'delete from t_delete_single where id = ?',
            'args': ArgsGenerator(n=10),
            'iterations': 20000,
        },
    ]
)
