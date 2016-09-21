
class ArgsGenerator:

    def __init__(self, start, n=1):
        self.count = start
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [x, "crate", 1]


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
            'args': ArgsGenerator(n=10),
            'iterations': 1000,
        },
        {
            'statement': """insert into articles (id, name, price) values (?, ?, ?)
                            on duplicate key update
                            price = VALUES(price) + price""",
            'args': ArgsGenerator(n=10),
            'iterations': 1000,
        }
    ]
)
