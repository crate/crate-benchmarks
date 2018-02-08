    create table crate_types (
        pyfloat float,
        pystr string,
        pybool boolean,
        ean8 long,
        ipv4 ip,
        random_digit double,
        unix_time timestamp,
        pin geo_point
    ) with (number_of_replicas = 0);
