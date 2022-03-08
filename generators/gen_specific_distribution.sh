#!/usr/bin/env bash

set -Eeuo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x "generators/gen-data.py"
generators/gen-data.py --num=1000000 --distribution="$1"
