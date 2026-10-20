# syntax=docker/dockerfile:1
# pi0.5 brain image.
# One image for every challenge that uses this model. No weights are baked in.
# Python and JAX follow openpi's lock at the pinned commit
# (requires-python >= 3.11, jax[cuda12] == 0.5.3). Checkpoints are JAX orbax params.
# jax[cuda12] ships CUDA, cuDNN, and ptxas as wheels, so the runtime stage uses the CUDA base image.

FROM ubuntu:22.04 AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.1 /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/openpi/.venv \
    VIRTUAL_ENV=/opt/openpi/.venv \
    OPENPI_DATA_HOME=/opt/openpi/cache

ARG OPENPI_REF=215abfb217dbac7d5f1273282331b9b1866c0479

RUN apt-get update && apt-get install -y --no-install-recommends \
        git git-lfs build-essential clang ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git init -q /opt/openpi \
    && git -C /opt/openpi fetch -q --depth 1 https://github.com/Physical-Intelligence/openpi.git "${OPENPI_REF}" \
    && git -C /opt/openpi checkout -q FETCH_HEAD

WORKDIR /opt/openpi

# Inference extras (LeRobot, wandb) come from the lock. Dev tools stay out.
# The editable sources are not covered by UV_COMPILE_BYTECODE, so compile them explicitly.
RUN --mount=type=cache,target=/root/.cache/uv \
    GIT_LFS_SKIP_SMUDGE=1 uv venv --python 3.11.9 /opt/openpi/.venv \
    && GIT_LFS_SKIP_SMUDGE=1 uv sync --frozen --no-install-project --no-dev \
    && GIT_LFS_SKIP_SMUDGE=1 uv pip install --no-deps -e . \
    && /opt/openpi/.venv/bin/python -m compileall -q /opt/openpi/src \
    && rm -rf /opt/openpi/.git

# Sentencepiece model used by the pi0.5 tokenizer. Cached here so serving stays offline.
RUN /opt/openpi/.venv/bin/python -c "import openpi.shared.download as download; download.maybe_download('gs://big_vision/paligemma_tokenizer.model', gs={'token': 'anon'})"

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install "msgpack>=1.0"

# Protocol package, built as a wheel so an update does not invalidate the environment layer.
# ADD resolves the branch or tag on every build, so a moved ref is never served from cache.
ARG BRAIN_COMM_REF=v1.0.0
ADD https://github.com/Unidroid-AI/brain-comm.git#${BRAIN_COMM_REF} /tmp/comm
RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel --out-dir /wheels /tmp/comm


FROM nvidia/cuda:12.2.2-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/openpi/.venv \
    PATH="/opt/openpi/.venv/bin:${PATH}" \
    OPENPI_DATA_HOME=/opt/openpi/cache \
    XLA_PYTHON_CLIENT_MEM_FRACTION=0.5 \
    JAX_COMPILATION_CACHE_DIR=/cache/jax \
    GIT_PYTHON_REFRESH=quiet \
    HF_HUB_OFFLINE=1 \
    BRAIN_COMM_CHECK=pi05_check:check \
    PYTHONPATH=/opt/unidroid

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/python /opt/python
COPY --from=builder /opt/openpi /opt/openpi

RUN --mount=from=ghcr.io/astral-sh/uv:0.5.1,source=/uv,target=/bin/uv \
    --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    UV_COMPILE_BYTECODE=1 uv pip install --no-cache --no-deps /wheels/*.whl

COPY pi05_check.py /opt/unidroid/

WORKDIR /submission
CMD ["brain-comm", "serve", "--replicas", "1"]
