from cr8.bench_spec import Instructions, Spec

q1 = """select * from uservisits where trim("destinationURL") = 'cjdyxltsomxeklrfgvvgedaskobqceisafwbzjgemovtszmcgnwccsv'"""
q2 = """select avg("adRevenue"), sum("adRevenue"), min("adRevenue") from uservisits group by duration"""

def queries():
    for i in range(1, 100_000):
        yield {
            "statement": i % 2 == 0 and q1 or q2,
            "iterations": 100,
            "concurrency": 50,
        }


spec = Spec(
    setup=Instructions(
        statement_files = ["sql/uservisits.sql"],
        statements=[
            f"copy uservisits from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-{i:05}.gz' with (compression = 'gzip')"
            for i in range(1, 202)
        ],
        data_files=[],
    ),
    teardown=Instructions(
        statements=[]
    ),
    queries=queries()
)
