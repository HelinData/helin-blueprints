#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

version="${1:-}"
if [ -z "$version" ]; then
  echo "[build-and-publish] ERROR: usage: scripts/build-and-publish.sh <version>" >&2
  exit 1
fi

for var in HELIN_INSTANCE HELIN_CLIENT_ID HELIN_CLIENT_SECRET REGISTRY_URL REGISTRY_USER REGISTRY_PASSWORD; do
  if [ -z "${!var:-}" ]; then
    echo "[build-and-publish] ERROR: $var is not set" >&2
    exit 1
  fi
done

meta_name=$(grep '^meta_name:' module.yaml | cut -d ':' -f 2- | sed 's/^ *//; s/ *$//')
if [ -z "$meta_name" ]; then
  echo "[build-and-publish] ERROR: meta_name is missing in module.yaml" >&2
  exit 1
fi

image="$REGISTRY_URL/$meta_name"
platforms="${PLATFORMS:-linux/amd64,linux/arm64,linux/arm/v7}"

echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY_URL" --username "$REGISTRY_USER" --password-stdin
docker buildx build --platform "$platforms" --tag "$image:$version" --push ./module
scripts/publish-version.sh "$version" "$image" "$version"
