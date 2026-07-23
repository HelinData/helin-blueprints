#!/usr/bin/env bash
# Print an M2M access token for the Helin Platform API.
#
# Reads the auth domain and audience from ${HELIN_INSTANCE}/api/v1/configuration/,
# then exchanges the client credentials for a token via the OAuth2
# client_credentials grant. Diagnostics go to stderr, the token to stdout:
#
#   curl -H "Authorization: Bearer $(scripts/get-token.sh)" ...
#
# Required environment variables:
#   HELIN_INSTANCE       base URL of your platform instance (https://...)
#   HELIN_CLIENT_ID      M2M client id
#   HELIN_CLIENT_SECRET  M2M client secret
set -euo pipefail

for var in HELIN_INSTANCE HELIN_CLIENT_ID HELIN_CLIENT_SECRET; do
  if [ -z "${!var:-}" ]; then
    echo "[get-token] ERROR: $var is not set" >&2
    exit 1
  fi
done

config=$(curl --silent --show-error --fail "$HELIN_INSTANCE/api/v1/configuration/")

payload=$(jq -n \
  --arg client_id "$HELIN_CLIENT_ID" \
  --arg client_secret "$HELIN_CLIENT_SECRET" \
  --arg audience "$(jq -r '.auth.audience' <<<"$config")" \
  '{client_id: $client_id, client_secret: $client_secret, audience: $audience, grant_type: "client_credentials"}')

curl --silent --show-error --fail \
  --header "content-type: application/json" \
  --data "$payload" \
  "https://$(jq -r '.auth.domain' <<<"$config")/oauth/token" | jq -r '.access_token'
