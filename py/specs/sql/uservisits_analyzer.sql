CREATE TABLE uservisits (
   "sourceIP" STRING PRIMARY KEY,
   "destinationURL" STRING,
   "visitDate" TIMESTAMP,
   "adRevenue" FLOAT,
   "UserAgent" STRING,
   "cCode" STRING,
   "lCode" STRING,
   "searchWord" STRING,
   "duration" INTEGER,
    INDEX uagent_idx USING FULLTEXT("UserAgent") with (analyzer='english')
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
