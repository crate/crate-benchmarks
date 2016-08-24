create table uservisits (
    "sourceIP" string primary key,
    "destinationURL" string,
    "visitDate" timestamp,
    "adRevenue" float,
    "UserAgent" string INDEX using fulltext,
    "cCode" string,
    "lCode" string,
    "searchWord" string,
    "duration" int
) with (number_of_replicas = 0);
