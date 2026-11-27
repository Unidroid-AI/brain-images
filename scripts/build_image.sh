#!/usr/bin/env bash
# Build one brain image with the brain-comm pinned in brain-comm.lock, check what it contains, push it and print
# its digest. Each family's build_and_push.sh calls this.
# Usage: build_image.sh <family folder> <repo:tag>
# Needs: docker login ghcr.io (a token with write:packages). The printed repo@sha256:... goes in Admin -> Brains.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
family="$1"
tag="$2"
repo="${tag%:*}"

eval "$("${root}/scripts/resolve_brain_comm.sh" | sed 's/^/export /')"
echo "brain-comm ${BRAIN_COMM_COMMIT}, protocol ${BRAIN_COMM_PROTOCOL}" >&2

DOCKER_BUILDKIT=1 docker build -f "${root}/${family}/Dockerfile" \
    --build-arg "BRAIN_COMM_COMMIT=${BRAIN_COMM_COMMIT}" --build-arg "BRAIN_COMM_PROTOCOL=${BRAIN_COMM_PROTOCOL}" \
    --label org.opencontainers.image.source=https://github.com/Unidroid-AI/brain-images \
    -t "${tag}" "${root}/${family}"

# The label is what the backend and validators compare; make sure it is what the image really runs.
actual="$(docker run --rm --entrypoint python "${tag}" -c 'import brain_comm; print(brain_comm.PROTOCOL_VERSION)' | tail -n 1)"
label="$(docker image inspect --format '{{index .Config.Labels "ai.unidroid.brain-comm.protocol"}}' "${tag}")"
if [ "${actual}" != "${BRAIN_COMM_PROTOCOL}" ] || [ "${label}" != "${BRAIN_COMM_PROTOCOL}" ]; then
    echo "protocol mismatch: image runs '${actual}', label '${label}', expected '${BRAIN_COMM_PROTOCOL}'" >&2
    exit 1
fi

docker push "${tag}"
# The image can carry several tags or repos; pick the digest that belongs to the one just pushed.
docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "${tag}" | grep -m1 "^${repo}@"
