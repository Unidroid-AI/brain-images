#!/usr/bin/env bash
# Build the pi0.5 brain image from this folder, push it to GHCR and print its digest.
# Usage: build_and_push.sh [repo:tag]     default ghcr.io/unidroid-ai/brain:pi0.5-v0
# Needs: docker login ghcr.io (a token with write:packages). The printed repo@sha256:... goes in Admin -> Brains.
# brain-comm comes from ../brain-comm.lock; the image is labelled with its commit and protocol.
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
exec "${root}/../scripts/build_image.sh" "$(basename "${root}")" "${1:-ghcr.io/unidroid-ai/brain:pi0.5-v0}"
