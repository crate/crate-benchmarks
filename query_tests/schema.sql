-- dbext:type=CRATE:host=localhost:port=4200:dbname=doc

CREATE TABLE benchmarks.query_tests (
  id string primary key,
  sboolean boolean,
  sbyte byte,
  sshort short,
  sinteger integer,
  slong long,
  sfloat float,
  sdouble double,
  sstring string,
  sip ip,
  stimestamp timestamp,
  sgeo_point geo_point,
  sgeo_shape geo_shape,
  aboolean array(boolean),
  abyte array(byte),
  ashort array(short),
  ainteger array(integer),
  along array(long),
  afloat array(float),
  adouble array(double),
  astring array(string),
  aip array(ip),
  atimestamp array(timestamp),
  ageo_point array(geo_point),
  ageo_shape array(geo_shape)
) CLUSTERED INTO 2 SHARDS WITH (number_of_replicas = 0);
