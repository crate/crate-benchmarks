-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE film (
  film_id INT PRIMARY KEY,
  title STRING NOT NULL,
  description STRING,
  release_year INTEGER,
  language_id SHORT NOT NULL,
  original_language_id SHORT,
  rental_duration SHORT NOT NULL,
  rental_rate DOUBLE NOT NULL,
  length SHORT,
  replacement_cost DOUBLE NOT NULL,
  rating STRING,
  special_features STRING,
  last_update TIMESTAMP NOT NULL
) CLUSTERED INTO 1 SHARDS;
