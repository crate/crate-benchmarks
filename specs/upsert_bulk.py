
from cr8.bench_spec import Spec, Instructions


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
        statement_files=["sql/articles_bulk_insert.sql"],
        statements=[
            "copy articles_bulk_insert from 'https://cdn.crate.io/downloads/datasets/benchmarks/articles_0.json.gz' with (compression = 'gzip')",
            "refresh table articles_bulk_insert"
        ]
    ),
    teardown=Instructions(statements=["drop table articles_bulk_insert"]),
    queries=[
        {
            'statement': """insert into articles_bulk_insert (id, name, price) values ($1, $2, $3)
                            on conflict (id) do update set name = $2, price = $3""",
            'bulk_args': BulkArgsGenerator(1000),
            'iterations': 1000,
        },
        {
            'statement': """insert into articles_bulk_insert (id, name, price) values (?, ?, ?)
                            on conflict (id) do update set price = excluded.price + price""",
            'bulk_args': BulkArgsGenerator(1000),
            'iterations': 1000,
        }
    ]
)
