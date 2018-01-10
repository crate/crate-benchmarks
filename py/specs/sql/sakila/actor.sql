-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE actor (
  actor_id INTEGER PRIMARY KEY,
  first_name STRING NOT NULL,
  last_name STRING NOT NULL,
  last_update TIMESTAMP NOT NULL
) CLUSTERED INTO 2 SHARDS;
