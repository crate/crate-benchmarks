#!/usr/bin/env bash
set -Eeuo pipefail

# This script is useful to do ad-hoc profiling against a running CrateDB instance

PID=$(jps | awk '/CrateDB/ { print $1 }')
jcmd $PID JFR.start name=recording duration=1m filename=$(pwd)/profile.jfr settings=profile


# Some examples, uncomment and adjust as needed


#cr8 timeit  -w 0 -c 5 -r 50 <<EOF
#SELECT
#    floor(extract(epoch FROM "enqueuedTimeUtc") / 60) * 60 AS "time",
#    module AS metric,
#    count(payload) AS "payload"
#FROM
#    iothub.rawdata
#GROUP BY
#    1,
#    device,
#    module,
#    2
#ORDER BY
#    1,
#    2
#limit 20
#EOF

#cr8 timeit -s "select 1" -w 0 -r 50000 -c 50
#cr8 timeit --hosts asyncpg://localhost:5432 -s "select 1" -w 0 -r 200000 -c 55

#cr8 run-spec specs/select/huge_arrays.toml localhost:4200 --action queries


jcmd $PID JFR.stop name=recording
