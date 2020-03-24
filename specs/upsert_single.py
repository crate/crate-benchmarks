
from cr8.bench_spec import Spec, Instructions


class ArgsGenerator:

    def __init__(self, n=1):
        self.count = 0
        self.n = n

    def __call__(self):
        x = self.count
        self.count += self.n
        return [x, "crate", 1]


spec = Spec(
    setup=Instructions(
        statement_files=["sql/articles.sql"],
        statements=[
            "copy articles from 'https://cdn.crate.io/downloads/datasets/benchmarks/articles_0.json.gz' with (compression = 'gzip')",
            "refresh table articles"
        ]
    ),
    teardown=Instructions(statements=["drop table articles"]),
    queries=[
        {
            'statement': """insert into articles (id, name, price) values ($1, $2, $3)
                            on conflict (id) do update set name = $2, price = $3""",
            'args': ArgsGenerator(n=10),
            'iterations': 1000,
        },
        {
            'statement': """insert into articles (id, name, price) values (?, ?, ?)
                            on conflict (id) do update set price = excluded.price + price""",
            'args': ArgsGenerator(n=10),
            'iterations': 1000,
        }
    ]
)
