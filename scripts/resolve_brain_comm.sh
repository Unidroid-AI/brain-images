#!/usr/bin/env bash
# Resolve the brain-comm ref in brain-comm.lock to a commit and its wire protocol.
# Prints two lines:   BRAIN_COMM_COMMIT=<40 hex>   BRAIN_COMM_PROTOCOL=<PROTOCOL_VERSION at that commit>
# BRAIN_COMM_REF in the environment overrides the lock (to try another ref).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
url="https://github.com/Unidroid-AI/brain-comm.git"
ref="${BRAIN_COMM_REF:-$(sed -n 's/^BRAIN_COMM_REF=//p' "${root}/brain-comm.lock")}"
[ -n "${ref}" ] || { echo "no BRAIN_COMM_REF in brain-comm.lock" >&2; exit 1; }

if printf '%s' "${ref}" | grep -qE '^[0-9a-f]{40}$'; then
    commit="${ref}"
else
    # An annotated tag points at a tag object; its peeled entry (^{}) is the commit.
    commit="$(git ls-remote "${url}" "refs/tags/${ref}^{}" | cut -f1 | head -n1)"
    [ -n "${commit}" ] || commit="$(git ls-remote "${url}" "refs/tags/${ref}" "refs/heads/${ref}" | cut -f1 | head -n1)"
fi
printf '%s' "${commit}" | grep -qE '^[0-9a-f]{40}$' || { echo "cannot resolve brain-comm ref '${ref}'" >&2; exit 1; }

probe="$(mktemp -d)"
trap 'rm -rf "${probe}"' EXIT
git -C "${probe}" init --quiet
git -C "${probe}" fetch --quiet --depth 1 "${url}" "${commit}"
protocol="$(git -C "${probe}" show FETCH_HEAD:brain_comm/protocol.py | sed -n 's/^PROTOCOL_VERSION = "\(.*\)"$/\1/p')"
[ -n "${protocol}" ] || { echo "brain_comm/protocol.py at ${commit} has no PROTOCOL_VERSION" >&2; exit 1; }

echo "BRAIN_COMM_COMMIT=${commit}"
echo "BRAIN_COMM_PROTOCOL=${protocol}"
