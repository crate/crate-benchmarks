
class ArgsGenerator:

    def __init__(self, start, n=1):
        self.count = start
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [x, "crate", 1]


class BulkArgsGenerator:

    def __init__(self, bulk_size):
        self.count = 0
        self.bulk_size = bulk_size

    def __call__(self):
        start = self.count * self.bulk_size
        end = start + self.bulk_size
        self.count += 1
        return [[x, "crate", 1] for x in range(start, end)]


spec = Spec(
    setup=Instructions(
        statement_files=["sql/articles.sql"],
        statements=[
            "copy articles from 's3://crate-stresstest-data/join-sample-data/articles_*' with (compression = 'gzip')",
            "refresh table articles"
        ]
    ),
    teardown=Instructions(statements=["drop table articles"]),
    queries=[
        {
            'statement': """insert into articles (id, name, price) values ($1, $2, $3)
                            on duplicate key update
                            name = $2, price = $3""",
            'args': [1, "crate", 1],
            'iterations': 1000,
        },
        {
            'statement': """insert into articles (id, name, price) values ($1, $2, $3)
                            on duplicate key update
                            name = $2, price = $3""",
            'args': ArgsGenerator(start=1000000, n=1),
            'iterations': 1000,
        },
        {
            'statement': """insert into articles (id, name, price) values (?, ?, ?)
                            on duplicate key update
                            price = VALUES(price) + price""",
            'args': [1, "crate", 1],
            'iterations': 1000,
        },
        {
            'statement': """insert into articles (id, name, price) values (?, ?, ?)
                            on duplicate key update
                            price = VALUES(price) + price""",
            'bulk_args': BulkArgsGenerator(1000),
            'iterations': 1000,
        }
    ]
)
