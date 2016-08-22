CREATE TABLE uservisits (
   "sourceIP" STRING PRIMARY KEY,
   "destinationURL" STRING,
   "visitDate" TIMESTAMP,
   "adRevenue" FLOAT,
   "UserAgent" STRING INDEX USING FULLTEXT,
   "cCode" STRING,
   "lCode" STRING,
   "searchWord" STRING,
   "duration" INTEGER
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
