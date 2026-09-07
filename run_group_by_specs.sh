#!/usr/bin/env bash
set -Eeuo pipefail

# Runs specs/group_by.toml against a fresh CrateDB container, once per regex,
# saving each run's output to results/<regex>.log

SPEC_FILE="specs/aggregations_mixed_distinct_global.toml"
OUT_DIR="results"
CONTAINER_NAME="cratedb-scratch"
REGEXES=(
  "Q-21:"
  "Q-21a:"
  "Q-22:"
  "Q-22a:"
  "Q-23:"
  "Q-23a:"
)

mkdir -p "$OUT_DIR"

start_cratedb() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  docker run -d \
    -p 4200:4200 \
    -p 5433:5432 \
    -e CRATE_HEAP_SIZE=16g \
    --pull always \
    --rm \
    --name "$CONTAINER_NAME" \
    crate:latest >/dev/null
}

wait_for_cratedb() {
  echo "Waiting for CrateDB..."
  for _ in $(seq 1 60); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:4200/ | grep -q "200"; then
      echo "CrateDB up."
      return 0
    fi
    sleep 2
  done
  echo "CrateDB did not become ready in time." >&2
  return 1
}

stop_cratedb() {
  docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
}

for regex in "${REGEXES[@]}"; do
  safe_name=$(echo "$regex" | tr -cd '[:alnum:]_-')
  out_file="$OUT_DIR/${safe_name}.log"

  echo "=== Regex: $regex -> $out_file ==="

  start_cratedb
  wait_for_cratedb

  source venv/bin/activate
  cr8 run-spec "$SPEC_FILE" localhost:4200 --re-name "$regex" 2>&1 | tee "$out_file"
  deactivate

  stop_cratedb
done

echo "Done. Results in $OUT_DIR/"
