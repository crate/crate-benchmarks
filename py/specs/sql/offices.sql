CREATE TABLE offices (
  id integer,
  name string
) CLUSTERED BY (id) INTO 4 SHARDS;
