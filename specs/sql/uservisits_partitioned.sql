CREATE TABLE uservisits (
       "sourceIP" STRING,
       "destinationURL" STRING,
       "visitDate" TIMESTAMP,
       "adRevenue" FLOAT,
       "UserAgent" STRING INDEX USING FULLTEXT,
       "cCode" STRING,
       "lCode" STRING,
       "searchWord" STRING,
       "duration" INTEGER,
       "y" GENERATED ALWAYS AS date_trunc('year', "visitDate") / 1000000000000,
       INDEX uagent_plain USING PLAIN("UserAgent")
       -- ^^ used for regex matching ^^ --
    ) CLUSTERED INTO 1 shards PARTITIONED BY("y") WITH (
        number_of_replicas = 0
    );
