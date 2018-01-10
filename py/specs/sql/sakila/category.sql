-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE category (
  category_id SHORT PRIMARY KEY,
  name STRING NOT NULL,
  last_update TIMESTAMP NOT NULL
) CLUSTERED INTO 2 SHARDS;
