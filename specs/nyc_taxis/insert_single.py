import os
from inspect import getsourcefile
from os.path import abspath, join
from urllib import request

from fastparquet import ParquetFile
from pandas import Timestamp

FILE_URI = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"
FILE = 'yellow_tripdata_2025-01.parquet'
CURRENT_PATH = abspath(join(getsourcefile(lambda: 0), os.pardir))
FILE_PATH = join(CURRENT_PATH, FILE)

class DataProvider:

    def __init__(self, n=1):
        if not os.path.exists(FILE_PATH):
            print(f"Downloading {FILE_URI} to {FILE_PATH}...")
            request.urlretrieve(FILE_URI, FILE_PATH)
            print("Download completed.")
        self.pf = ParquetFile(FILE_PATH)
        self.generator = self.read()

    def __call__(self):
        return next(self.generator)

    def insert_statement(self):
        cols = ', '.join([f'"{col}"' for col in self.pf.columns])
        placeholders = ', '.join(['?' for _ in self.pf.columns])
        return f"INSERT INTO nyc_taxi.trips ({cols}) VALUES ({placeholders})"

    def read(self):
        for df in self.pf.iter_row_groups():
            for _, row in df.iterrows():
                yield [self.format_val(row[col]) for col in df.columns]

    @staticmethod
    def format_val(val):
        if isinstance(val, Timestamp):
            return val.strftime('%Y-%m-%d %H:%M:%S')
        return val

data_provider = DataProvider()


spec = Spec(
    setup=Instructions(
        statement_files=["nyc_taxis_schema.sql"]
    ),
    teardown=Instructions(statements=["drop table if exists nyc_taxi.trips"]),
    queries=[
        {
            "statement": data_provider.insert_statement(),
            "args": data_provider,
            "concurrency": 10,
            "iterations": 100000
        }
    ]

)
