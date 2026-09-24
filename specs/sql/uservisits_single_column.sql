CREATE TABLE IF NOT EXISTS uservisits (
   "sourceIP" STRING PRIMARY KEY
) WITH (
    number_of_replicas = 0,
    refresh_interval = 0
);
