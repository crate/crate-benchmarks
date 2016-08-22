import random, string


def random_string(length=100):
    """
    Generate random string of uppercase ascii characters and digists
    of length "length".
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def gen_args(x):
    return (x+1, random_string(), )


spec = Spec(
    setup=Instructions(
        statements=[
            "create table t_bulk_insert (id integer, value string) with (number_of_replicas=0)",
        ]
    ),
    teardown=Instructions(
        statements=[
            "drop table t_bulk_insert",
        ]
    ),
    queries=[
        {
            'statement': 'insert into t_bulk_insert (id, value) values (?, ?)',
            'bulk_args': [gen_args(x) for x in range(10000)],
            'iterations': 2000,
        }
    ]
)
