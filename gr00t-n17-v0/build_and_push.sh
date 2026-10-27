#!/usr/bin/env bash
# Build the GR00T N1.7 brain image from this folder, push it to GHCR and print its digest.
# Usage: build_and_push.sh [repo:tag]     default ghcr.io/unidroid-ai/brain:gr00t-n17-v0
# Needs: docker login ghcr.io (a token with write:packages). The printed repo@sha256:... goes in Admin -> Brains.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-ghcr.io/unidroid-ai/brain:gr00t-n17-v0}"
repo="${tag%:*}"

DOCKER_BUILDKIT=1 docker build -f "${root}/Dockerfile" \
    --label org.opencontainers.image.source=https://github.com/Unidroid-AI/brain-images \
    -t "${tag}" "${root}"
docker push "${tag}"
# The image can carry several tags or repos; pick the digest that belongs to the one just pushed.
docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "${tag}" | grep -m1 "^${repo}@"
