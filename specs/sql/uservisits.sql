CREATE TABLE uservisits (
   "sourceIP" STRING PRIMARY KEY,
   "destinationURL" STRING,
   "visitDate" TIMESTAMP,
   "adRevenue" FLOAT,
   "UserAgent" STRING INDEX USING FULLTEXT,
   "cCode" STRING PRIMARY KEY,
   "lCode" STRING,
   "searchWord" STRING,
   "duration" INTEGER,
   INDEX uagent_plain USING PLAIN("UserAgent")
   -- ^^ used for regex matching ^^ --
) CLUSTERED INTO 5 SHARDS partitioned by ("cCode") WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
