
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
            """CREATE TABLE id_int_value_str (
                id INTEGER PRIMARY KEY, 
                value STRING
            ) with (number_of_replicas=0)
            """,
        ],
        data_files=[
            {
                'source': 'data/id_int_value_str.json',
                'target': 'id_int_value_str',
            }
        ]
    ),
    teardown=Instructions(
        statements=[
            'drop table id_int_value_str',
        ]
    ),
    queries=[
        {
            'statement': 'delete from id_int_value_str where id = ?',
            'args': ArgsGenerator(n=10),
            'iterations': 40000,
        },
    ]
)
