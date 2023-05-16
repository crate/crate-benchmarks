#!/usr/bin/env bash
set -Eeuo pipefail

echo "$1" | cat - "$2" | csvjson -y 0 -d "," -p \\ --stream
