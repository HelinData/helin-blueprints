#!/usr/bin/env bash
# Fetch an M2M access token for the Helin Platform API (User Story 24551).
#
# Reads the auth domain and audience from the instance configuration endpoint
# (${HELIN_INSTANCE}/api/v1/configuration/) — nothing hardcoded — then runs the
# OAuth2 client_credentials grant and prints the access_token to stdout.
#
# Required env vars: HELIN_INSTANCE, HELIN_CLIENT_ID, HELIN_CLIENT_SECRET
set -euo pipefail

# TODO(24551): implement
#   1. Validate HELIN_INSTANCE, HELIN_CLIENT_ID, HELIN_CLIENT_SECRET are set;
#      exit non-zero with a clear message if not.
#   2. GET ${HELIN_INSTANCE}/api/v1/configuration/ → auth domain + audience.
#   3. POST https://<auth-domain>/oauth/token with grant_type=client_credentials.
#   4. Print access_token; exit non-zero with a clear message on failure.

echo "TODO: not implemented yet (see ADO user story 24551)" >&2
exit 1
