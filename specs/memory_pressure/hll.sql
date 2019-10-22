-- dbext:type=PGSQL:host=localhost:port=5432:dbname=crate:user=crate:passwd=:

CREATE TABLE hll (
  id text primary key,
  custom_user_id text not null
) clustered into 5 shards with (number_of_replicas = 1);
