#!/usr/bin/env bash
# One-time module registration (User Story 24553).
#
# Reads name, meta_name, author, category_id from module.yaml, POSTs /modules,
# and writes the returned module_id back into module.yaml.
# Idempotent: if module.yaml already contains a module_id, this is a no-op.
set -euo pipefail

# TODO(24553): implement
#   1. If module.yaml already has module_id → print notice and exit 0 (no-op).
#   2. Obtain token via scripts/get-token.sh.
#   3. POST ${HELIN_INSTANCE}/api/v1/modules with fields from module.yaml.
#   4. Write returned module_id back into module.yaml.

echo "TODO: not implemented yet (see ADO user story 24553)" >&2
exit 1
