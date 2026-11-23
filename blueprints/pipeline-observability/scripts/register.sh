#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

err() { echo "[register] ERROR: $*" >&2; }

if grep -q '^module_id:' module.yaml; then
  echo "[register] skipped - module.yaml already has a module_id"
  exit 0
fi

field() {
  line=$(grep "^$1:" module.yaml || true)
  echo "$line" | cut -d ':' -f 2- | sed 's/^ *//; s/ *$//'
}

name=$(field name)
meta_name=$(field meta_name)
author=$(field author)
description=$(field description)
logo_url=$(field logo_url)
category_id=$(field category_id)

for f in name meta_name author category_id; do
  if [ -z "${!f}" ]; then
    err "'$f' is missing in module.yaml"
    exit 1
  fi
done

token=$(scripts/get-token.sh)

payload=$(jq -n \
  --arg name "$name" \
  --arg meta_name "$meta_name" \
  --arg author "$author" \
  --arg description "$description" \
  --arg logo_url "$logo_url" \
  --arg category_id "$category_id" \
  '{name: $name, meta_name: $meta_name, author: $author, description: $description, logo_url: $logo_url, category_id: $category_id}')

response=$(curl --silent --show-error --fail-with-body \
  --header "content-type: application/json" \
  --header "authorization: Bearer $token" \
  --data "$payload" \
  "$HELIN_INSTANCE/api/v1/modules") \
  || { err "POST /modules failed: $response"; exit 1; }

module_id=$(jq -r '.id' <<<"$response")
module_uuid=$(jq -r '.uuid' <<<"$response")

if [ -z "$module_id" ] || [ "$module_id" = "null" ] || [ -z "$module_uuid" ] || [ "$module_uuid" = "null" ]; then
  err "unexpected response from POST /modules: $response"
  exit 1
fi

printf 'module_id: %s\nmodule_uuid: %s\n' "$module_id" "$module_uuid" >> module.yaml

echo "[register] Module '$name' registered (module_id: $module_id)."
echo "[register] module.yaml was updated - commit it so CI can publish versions."
