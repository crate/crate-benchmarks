class ArgsGenerator:

    def __init__(self, n=1):
        self.count = 0
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [x, str(x)]

spec = Spec(
    setup=Instructions(
        statements=[
            """CREATE TABLE id_int_value_str(
                id integer primary key,
                value string
            ) with (number_of_replicas=0)
            """
        ]
    ),
    teardown=Instructions(statements=["drop table id_int_value_str"]),
    queries=[
        {
            "statement": "insert into id_int_value_str (id, value) values (?, ?)",
            "args": ArgsGenerator(),
            "iterations": 100000
        }
    ]

)
