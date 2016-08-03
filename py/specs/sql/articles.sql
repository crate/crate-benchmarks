create table articles (
  id integer primary key,
  name string,
  price float
) with (number_of_replicas=0);