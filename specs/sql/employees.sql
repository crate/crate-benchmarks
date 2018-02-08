CREATE TABLE employees (
  id integer,
  name string,
  office_id integer
) CLUSTERED BY (id) INTO 3 SHARDS;
