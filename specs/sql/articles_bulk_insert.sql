create table articles_bulk_insert (
  id integer primary key,
  name string,
  price float
) with (number_of_replicas=0);
