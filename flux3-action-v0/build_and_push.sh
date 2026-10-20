#!/usr/bin/env bash
# Build the FLUX 3 Action brain image from this folder and print its digest.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-brain-flux3-action-v0}"

DOCKER_BUILDKIT=1 docker build -f "${root}/Dockerfile" -t "${tag}" "${root}"
docker push "${tag}"
docker image inspect --format '{{index .RepoDigests 0}}' "${tag}"
