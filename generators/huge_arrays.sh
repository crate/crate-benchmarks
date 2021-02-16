#!/usr/bin/env bash
set -Eeuo pipefail

mkjson --num 1000 xs="replicate(randomInt(1000, 10000), randomInt())"
