#!/usr/bin/env bash
#
# Start a single CrateDB node in Docker, run a SQL file against it and stop it
# again, leaving the data behind in $DATA_ROOT/$DATA_DIR_NAME. The result can be
# reused with compare_run.py / compare_run_saved.py via `-s path.data=<that dir>`.
#
# All variables below can be overridden from the environment, e.g.:
#   VERSION=6.2 DATA_DIR_NAME=v6_2_hits_data_1M ./load_data_docker.sh
#   VERSION=nightly DATA_DIR_NAME=nightly_hits_data_1M SQL_FILE_NAME=load_hits_1M.sql ./load_data_docker.sh

set -euo pipefail

VERSION="${VERSION:-6.3}"
# Releases are published as crate:<version>, nightlies only as crate/crate:nightly*
if [[ "$VERSION" == nightly* ]]; then
    IMAGE="${IMAGE:-crate/crate:$VERSION}"
else
    IMAGE="${IMAGE:-crate:$VERSION}"
fi
DATA_ROOT=/home/haris/projects/crate/test-data
SQL_ROOT=/home/haris/Documents/Notes/CrateDB
# Name of the data dir below DATA_ROOT
DATA_DIR_NAME="${DATA_DIR_NAME:-v6_3_hits_data_1M}"
# Name of the SQL file below SQL_ROOT
SQL_FILE_NAME="${SQL_FILE_NAME:-load_hits_1M.sql}"
# Table whose row count is printed (with the CrateDB version) once loading is done
TABLE="${TABLE:-hits}"
# Directory holding the files referenced by `COPY ... FROM 'file:///...'`.
# Mounted at the same path inside the container so the paths in SQL_FILE work.
IMPORT_DIR="${IMPORT_DIR:-/home/haris/projects/crate/test-data/clickhouse}"
HEAP_SIZE="${HEAP_SIZE:-4g}"
HTTP_PORT="${HTTP_PORT:-4200}"
PG_PORT="${PG_PORT:-5432}"

for name in "$DATA_DIR_NAME" "$SQL_FILE_NAME"; do
    if [[ -z "$name" || "$name" == */* ]]; then
        echo "Expected a plain name, not a path: '$name'" >&2
        exit 1
    fi
done
DATA_DIR="$DATA_ROOT/$DATA_DIR_NAME"
SQL_FILE="$SQL_ROOT/$SQL_FILE_NAME"

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

docker pull "$IMAGE"
docker run -d --name "$CONTAINER" \
    -p "$HTTP_PORT:4200" -p "$PG_PORT:5432" \
    -e CRATE_HEAP_SIZE="$HEAP_SIZE" \
    -v "$DATA_DIR:/data" \
    -v "$IMPORT_DIR:$IMPORT_DIR:ro" \
    "$IMAGE" \
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
sql "SELECT version(), count(*) FROM $TABLE" | python3 -c '
import json, sys
version, rows = json.load(sys.stdin)["rows"][0]
print(f"version: {version}")
print(f"rows:    {rows}")'
