#!/usr/bin/env bash

set -Eeuo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
USER_IDS_PATH="$DIR/custom_user_ids.txt"

rm "$USER_IDS_PATH" 2> /dev/null || true

if ! hash mkjson 2> /dev/null; then
  wget https://github.com/mfussenegger/mkjson/releases/download/0.3.0/mkjson-linux-x86_64 -O "$DIR/mkjson"
  chmod +x "$DIR/mkjson"
  PATH="$PATH:$DIR/"
fi

mkjson --num 500000 custom_user_id="uuid4()" | jq -r '.custom_user_id' > "$USER_IDS_PATH"
mkjson --num 5000000 custom_user_id="oneOf(fromFile('$DIR/custom_user_ids.txt'))" id="uuid4()"
