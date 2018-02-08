CREATE TABLE uservisits_no_doc_values (
   "sourceIP" STRING PRIMARY KEY,
   "destinationURL" STRING,
   "visitDate" TIMESTAMP,
   "adRevenue" FLOAT,
   "UserAgent" STRING INDEX USING FULLTEXT,
   "cCode" STRING STORAGE WITH (columnstore = false),
   "lCode" STRING,
   "searchWord" STRING,
   "duration" INTEGER,
   INDEX uagent_plain USING PLAIN("UserAgent")
   -- ^^ used for regex matching ^^ --
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
