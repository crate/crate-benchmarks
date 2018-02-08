-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE film_actor (
  actor_id INTEGER PRIMARY KEY,
  film_id INTEGER PRIMARY KEY,
  last_update TIMESTAMP NOT NULL
) CLUSTERED INTO 5 SHARDS;
