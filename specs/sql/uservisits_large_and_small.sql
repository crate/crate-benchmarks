CREATE TABLE uservisits_large (
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
CREATE TABLE uservisits_small (
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
copy uservisits_small from 's3://crate.amplab/data/1node/uservisits/part-00000*' with (compression = 'gzip');
copy uservisits_small from 's3://crate.amplab/data/1node/uservisits/part-00001*' with (compression = 'gzip');
copy uservisits_small from 's3://crate.amplab/data/1node/uservisits/part-00002*' with (compression = 'gzip');
copy uservisits_small from 's3://crate.amplab/data/1node/uservisits/part-00003*' with (compression = 'gzip');
copy uservisits_small from 's3://crate.amplab/data/1node/uservisits/part-00004*' with (compression = 'gzip');
copy uservisits_large from 's3://crate.amplab/data/1node/uservisits/part-0000*' with (compression = 'gzip');
refresh table uservisits_large, uservisits_small;
