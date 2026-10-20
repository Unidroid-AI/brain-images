#!/usr/bin/env bash
# Build the pi0.5 brain image from this folder and print its digest.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-brain-pi0.5-v0}"

DOCKER_BUILDKIT=1 docker build -f "${root}/Dockerfile" -t "${tag}" "${root}"
docker push "${tag}"
docker image inspect --format '{{index .RepoDigests 0}}' "${tag}"
