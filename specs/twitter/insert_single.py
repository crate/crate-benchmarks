import json
import os
from inspect import getsourcefile
from os.path import abspath, join
from urllib import request

FILE_URI = "https://github.com/cwida/RealNest/raw/refs/heads/main/sample-data/100mib/twitter-stream-2023-01/data.jsonl"
FILE = 'twitter_data.jsonl'
CURRENT_PATH = abspath(join(getsourcefile(lambda: 0), os.pardir))
FILE_PATH = join(CURRENT_PATH, FILE)

class DataProvider:

    def __init__(self, n=1):
        if not os.path.exists(FILE_PATH):
            print(f"Downloading {FILE_URI} to {FILE_PATH}...")
            request.urlretrieve(FILE_URI, FILE_PATH)
            print("Download completed.")
        self.generator = self.read_file_content()

    def __call__(self):
        val = next(self.generator, None)
        if val is None:
            # Restart the generator if exhausted (file contains only 15360 records)
            self.generator = self.read_file_content()
            return next(self.generator)
        return val

    @staticmethod
    def read_file_content():
        with open(FILE_PATH, 'r') as file:
            for line in file:
                j = json.loads(line)
                yield [json.dumps(j['data']), json.dumps(j['includes']), json.dumps(j['errors'])]


spec = Spec(
    setup=Instructions(
        statement_files=["twitter_schema.sql"]
    ),
    teardown=Instructions(statements=["drop table if exists tweets"]),
    queries=[
        {
            "statement": "INSERT INTO tweets (data, includes, errors) VALUES (?, ?, ?)",
            "args": DataProvider(),
            "concurrency": 15,
            "iterations": 500000
        },
        # Issue a REFRESH to make sure all written segments are visible when running indexing statistic queries later
        {
            "statement": "REFRESH TABLE tweets",
            "iterations": 1
        }
    ]

)
