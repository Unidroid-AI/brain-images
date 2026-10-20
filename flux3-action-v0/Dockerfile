# syntax=docker/dockerfile:1
# FLUX 3 Action brain image.
# One image for every challenge that uses this model. No weights are baked in.
# The runtime follows flux-action's lock at the pinned commit: Python 3.12, torch 2.10 (cu128),
# transformers 5.16.1. NATTEN is not in the lock, so its wheel is installed separately.
# CUDA 12.8 wheels need a host driver 570 or newer.
# torch ships its own CUDA and cuDNN libraries, so the runtime stage uses the CUDA base image.

FROM ubuntu:22.04 AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.1 /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/flux-action/.venv \
    VIRTUAL_ENV=/opt/flux-action/.venv

ARG FLUX_ACTION_REF=830f1ce178d7aea52f18fde31d8e8e36ce6bae21
ARG NATTEN_WHEEL=natten==0.21.6+torch2100cu128

RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git init -q /opt/flux-action \
    && git -C /opt/flux-action fetch -q --depth 1 https://github.com/black-forest-labs/flux-action.git "${FLUX_ACTION_REF}" \
    && git -C /opt/flux-action checkout -q FETCH_HEAD

WORKDIR /opt/flux-action

# --extra data is left out: the brain never reads DROID parquet or video files.
# The editable project sources are not covered by UV_COMPILE_BYTECODE, so compile them explicitly.
# That pass is best effort: scripts in the checkout that do not compile are never imported.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra encoders --extra serve \
    && uv pip install "${NATTEN_WHEEL}" -f https://whl.natten.org/ \
    && uv pip install "msgpack>=1.0" \
    && rm -rf /opt/flux-action/.git \
    && { /opt/flux-action/.venv/bin/python -m compileall -q -x '/\.venv/' /opt/flux-action || true; }

# Protocol package, built as a wheel so an update does not invalidate the environment layer.
# ADD resolves the branch or tag on every build, so a moved ref is never served from cache.
ARG BRAIN_COMM_REF=v1.0.0
ADD https://github.com/Unidroid-AI/brain-comm.git#${BRAIN_COMM_REF} /tmp/comm
RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel --out-dir /wheels /tmp/comm


FROM nvidia/cuda:12.8.1-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/flux-action/.venv \
    PATH="/opt/flux-action/.venv/bin:${PATH}" \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    TORCHINDUCTOR_CACHE_DIR=/cache/inductor \
    TRITON_CACHE_DIR=/cache/triton \
    GIT_PYTHON_REFRESH=quiet \
    BRAIN_COMM_CHECK=flux3_check:check \
    PYTHONPATH=/opt/unidroid

# build-essential: torch inductor and triton compile with gcc when a brain enables compilation.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/python /opt/python
COPY --from=builder /opt/flux-action /opt/flux-action

RUN --mount=from=ghcr.io/astral-sh/uv:0.5.1,source=/uv,target=/bin/uv \
    --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    UV_COMPILE_BYTECODE=1 uv pip install --no-cache --no-deps /wheels/*.whl

COPY flux3_check.py /opt/unidroid/

WORKDIR /submission
CMD ["brain-comm", "serve", "--replicas", "1"]
