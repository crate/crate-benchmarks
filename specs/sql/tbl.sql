CREATE TABLE IF NOT EXISTS tbl (
    id INTEGER PRIMARY KEY,
    col_a_100 INTEGER,
    col_b_100 INTEGER,
    col_a_90 INTEGER,
    col_b_90 INTEGER,
    col_a_80 INTEGER,
    col_b_80 INTEGER,
    col_a_70 INTEGER,
    col_b_70 INTEGER,
    col_a_60 INTEGER,
    col_b_60 INTEGER,
    col_a_50 INTEGER,
    col_b_50 INTEGER,
    col_a_40 INTEGER,
    col_b_40 INTEGER,
    col_a_30 INTEGER,
    col_b_30 INTEGER,
    col_a_20 INTEGER,
    col_b_20 INTEGER,
    col_a_10 INTEGER,
    col_b_10 INTEGER
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
