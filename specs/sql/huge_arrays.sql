-- dbext:type=PGSQL:host=localhost:port=5432:dbname=crate:user=crate:passwd=:

create table huge_arrays (
  xs integer[]
) clustered into 4 shards with (number_of_replicas = 0);
