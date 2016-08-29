class ArgsGenerator:

    def __init__(self, n=1):
        self.count = 0
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [str(x), x]

spec = Spec(
    setup=Instructions(
        statements=[
            """create table t_update_single (id integer primary key, value string)
               with (number_of_replicas=0)"""
        ],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 't_update_single',
            }
        ]
    ),
    teardown=Instructions(statements=["drop table t_update_single"]),
    queries=[
        {
            'statement': 'update t_update_single set value = ? where id = ?',
            'args': ArgsGenerator(),
            'iterations': 100000,
        },
    ]
)
