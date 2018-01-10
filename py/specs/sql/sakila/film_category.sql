-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE film_category (
  film_id INT PRIMARY KEY,
  category_id SHORT PRIMARY KEY,
  last_update TIMESTAMP NOT NULL
) CLUSTERED INTO 1 SHARDS;
