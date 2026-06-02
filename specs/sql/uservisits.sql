CREATE TABLE uservisits (
   "sourceIP" STRING PRIMARY KEY,
   "destinationURL" STRING,
   "visitDate" TIMESTAMP,
   "adRevenue" FLOAT,
   "UserAgent" STRING INDEX USING FULLTEXT,
   "cCode" varchar(3),
   "lCode" STRING NOT NULL,
   "searchWord" STRING,
   "duration" INTEGER,
   INDEX uagent_plain USING PLAIN("UserAgent")
   -- ^^ used for regex matching ^^ --
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
