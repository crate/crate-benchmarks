#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

V1=/home/haris/apps/crate/crate-6.5.0-2026-09-09-09-55-e364a6d.tar.gz
V2=/home/haris/apps/crate/crate-6.5.0-2026-09-09-17-06-5e5207c.tar.gz
SPEC=specs/special.toml
PAUSE_SECONDS=30

# Ladder: decreasing column cardinality (100% unique down to 10%).
LADDER=('Q-100:' 'Q-90:' 'Q-80:' 'Q-70:' 'Q-60:' 'Q-50:' 'Q-40:' 'Q-30:' 'Q-20:' 'Q-10:')

for i in "${!LADDER[@]}"; do
    name="${LADDER[$i]}"
    echo "=== running ${name} ==="
    ./compare_run_saved.py \
        --v1 "$V1" \
        --v2 "$V2" \
        --forks 1 \
        --env CRATE_HEAP_SIZE=16g \
        --spec "$SPEC" \
        --re-name "$name"

    if [ "$i" -lt $((${#LADDER[@]} - 1)) ]; then
        echo "sleeping ${PAUSE_SECONDS}s before next ladder..."
        sleep "$PAUSE_SECONDS"
    fi
done
