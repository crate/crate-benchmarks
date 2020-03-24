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
copy uservisits_small from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00000.gz' with (compression = 'gzip');
copy uservisits_small from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00001.gz' with (compression = 'gzip');
copy uservisits_small from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00002.gz' with (compression = 'gzip');
copy uservisits_small from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00003.gz' with (compression = 'gzip');
copy uservisits_small from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00004.gz' with (compression = 'gzip');

copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00000.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00001.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00002.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00003.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00004.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00005.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00006.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00007.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00008.gz' with (compression = 'gzip');
copy uservisits_large from 'https://cdn.crate.io/downloads/datasets/amplab/1node/uservisits/part-00009.gz' with (compression = 'gzip');
refresh table uservisits_large, uservisits_small;
