CREATE SERVER pq FOREIGN DATA WRAPPER parquet
OPTIONS (files ['s3://datasets-documentation/uk-house-prices/parquet/house_prices.parquet']);

CREATE FOREIGN TABLE houseprices (
  "price" INT,
  "date" DATE,
  "postcode1" TEXT,
  "postcode2" TEXT,
  "type" BYTE,
  "is_new" BOOLEAN,
  "duration" BYTE,
  "addr1" TEXT,
  "addr2" TEXT,
  "street" TEXT,
  "locality" TEXT,
  "town" TEXT,
  "district" TEXT,
  "county" TEXT
) SERVER pq;


