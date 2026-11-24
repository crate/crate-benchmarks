CREATE SERVER pq FOREIGN DATA WRAPPER parquet
OPTIONS (files ['s3://datasets-documentation/uk-house-prices/parquet/house_prices.parquet']);

CREATE FOREIGN TABLE houseprices (
  "price" INT,
  "date" INT,
  "postcode1" TEXT,
  "postcode2" TEXT,
  "type" int,
  "is_new" int,
  "duration" int,
  "addr1" TEXT,
  "addr2" TEXT,
  "street" TEXT,
  "locality" TEXT,
  "town" TEXT,
  "district" TEXT,
  "county" TEXT
) SERVER pq;
