#!/usr/bin/env bash
# Build the GR00T N1.7 brain image from this folder and print its digest.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-brain-gr00t-n17-v0}"

DOCKER_BUILDKIT=1 docker build -f "${root}/Dockerfile" -t "${tag}" "${root}"
docker push "${tag}"
docker image inspect --format '{{index .RepoDigests 0}}' "${tag}"
