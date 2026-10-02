#!/usr/bin/env bash
#
# Start a single CrateDB node in Docker, run a SQL file against it and stop it
# again, leaving the data behind in DATA_DIR. The result can be reused with
# compare_run.py / compare_run_saved.py via `-s path.data=$DATA_DIR`.
#
# All variables below can be overridden from the environment, e.g.:
#   VERSION=6.2 DATA_DIR=/tmp/hits ./load_data_docker.sh

set -euo pipefail

VERSION="${VERSION:-6.3}"
DATA_DIR="${DATA_DIR:-/home/haris/projects/crate/test-data/v6_3_hits_data_1M}"
SQL_FILE="${SQL_FILE:-/home/haris/Documents/Notes/CrateDB/load_hits_1M.sql}"
# Table whose row count is printed once loading is done
TABLE="${TABLE:-hits}"
# Directory holding the files referenced by `COPY ... FROM 'file:///...'`.
# Mounted at the same path inside the container so the paths in SQL_FILE work.
IMPORT_DIR="${IMPORT_DIR:-/home/haris/projects/crate/test-data/clickhouse}"
HEAP_SIZE="${HEAP_SIZE:-4g}"
HTTP_PORT="${HTTP_PORT:-4200}"
PG_PORT="${PG_PORT:-5432}"

CONTAINER="crate-load-${VERSION//./_}"

if [[ ! -f "$SQL_FILE" ]]; then
    echo "SQL file not found: $SQL_FILE" >&2
    exit 1
fi
if [[ -d "$DATA_DIR" && -n "$(ls -A "$DATA_DIR")" ]]; then
    echo "Data dir is not empty, refusing to load into it: $DATA_DIR" >&2
    exit 1
fi

# Create it ourselves, otherwise Docker creates it owned by root
mkdir -p "$DATA_DIR"

cleanup() {
    docker stop "$CONTAINER" >/dev/null 2>&1 || true
    docker rm "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker pull "crate:$VERSION"
docker run -d --name "$CONTAINER" \
    -p "$HTTP_PORT:4200" -p "$PG_PORT:5432" \
    -e CRATE_HEAP_SIZE="$HEAP_SIZE" \
    -v "$DATA_DIR:/data" \
    -v "$IMPORT_DIR:$IMPORT_DIR:ro" \
    "crate:$VERSION" \
    crate -Cdiscovery.type=single-node -Cpath.data=/data

echo "Waiting for CrateDB on port $HTTP_PORT"
for _ in $(seq 1 120); do
    curl -sf "localhost:$HTTP_PORT" >/dev/null && break
    sleep 1
done
if ! curl -sf "localhost:$HTTP_PORT" >/dev/null; then
    echo "CrateDB did not come up, logs:" >&2
    docker logs "$CONTAINER" >&2
    exit 1
fi

echo "Running $SQL_FILE"
docker exec -i "$CONTAINER" crash < "$SQL_FILE"

# The table may be created with refresh_interval = 0
sql() {
    curl -sf "localhost:$HTTP_PORT/_sql" -H 'Content-Type: application/json' \
        -d "{\"stmt\": \"$1\"}"
}
sql "REFRESH TABLE $TABLE" >/dev/null
sql "SELECT count(*) FROM $TABLE" | python3 -c 'import json, sys; print(json.load(sys.stdin)["rows"][0][0])'
