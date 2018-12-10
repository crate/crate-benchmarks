
from cr8.bench_spec import Spec, Instructions
from pathlib import Path
from os import path
import inspect
import json


BULK_SIZE = 1000


def args():
    file_directory = path.dirname(inspect.getfile(lambda: None))
    data_source = Path(file_directory) / 'data' / 'id_int_value_str.json'
    with open(data_source.absolute()) as f:
        ids = []
        values = []
        for idx, line in enumerate(f):
            record = json.loads(line)
            ids.append(record['id'])
            values.append(record['value'])
            if idx % BULK_SIZE == 0:
                yield (ids, values)
                ids.clear()
                values.clear()
        if ids:
            yield (ids, values)


spec = Spec(
    setup=Instructions(statement_files=["sql/id_int_value_str.sql"]),
    teardown=Instructions(statements=["drop table id_int_value_str"]),
    queries=[
        {
            "statement": "insert into id_int_value_str (id, value) (select col1, col2 from unnest(?, ?))",
            "args": args(),
            "iterations": 1000
        }
    ]
)
