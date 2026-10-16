#!/usr/bin/env bash
set -euo pipefail

APP_NAME="release-demo-app"
VERSION="${1:-v1.0.0}"
COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")

echo "=================================================="
echo "Building Docker image: ${APP_NAME}:${VERSION}"
echo "Commit SHA: ${COMMIT_SHA}"
echo "=================================================="

docker build \
  -f docker/Dockerfile \
  --build-arg APP_VERSION="${VERSION}" \
  --build-arg COMMIT_SHA="${COMMIT_SHA}" \
  -t "${APP_NAME}:${VERSION}" \
  -t "${APP_NAME}:${COMMIT_SHA}" \
  .

echo "Build complete. Available tags:"
docker images | grep "${APP_NAME}" || true
