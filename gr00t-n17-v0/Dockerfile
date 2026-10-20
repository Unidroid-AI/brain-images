# syntax=docker/dockerfile:1
# GR00T N1.7 brain image.
# One image for every challenge that uses this model. No weights are baked in.
# Python, torch, and flash-attn follow Isaac-GR00T's own lock at the pinned commit
# (requires-python == 3.10.*, torch == 2.7.1, flash-attn == 2.7.4.post1, CUDA 12.8).
# torch ships its own CUDA libraries, so the runtime stage uses the CUDA base image, not devel.

FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

ARG GROOT_REF=23ace64f17aa5015259b8609d371eb61a357c776
ARG FLASH_ATTN_WHEEL=https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.7cxx11abiFALSE-cp310-cp310-linux_x86_64.whl

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-dev git build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv

# An ABI mismatch between torch and flash-attn only shows up on import, so fail the build here.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip \
    && python -m pip install \
        torch==2.7.1 torchvision==0.22.1 \
        --index-url https://download.pytorch.org/whl/cu128 \
    && python -m pip install "${FLASH_ATTN_WHEEL}" \
    && python -c "import torch, flash_attn_2_cuda"

RUN --mount=type=cache,target=/root/.cache/pip \
    git init -q /opt/isaac-gr00t \
    && git -C /opt/isaac-gr00t fetch -q --depth 1 https://github.com/NVIDIA/Isaac-GR00T.git "${GROOT_REF}" \
    && git -C /opt/isaac-gr00t checkout -q FETCH_HEAD \
    && rm -rf /opt/isaac-gr00t/.git \
    && python -m pip install --no-deps /opt/isaac-gr00t \
    && python -m pip install \
        numpy==1.26.4 transformers==4.57.3 diffusers==0.35.1 \
        einops==0.8.1 peft==0.17.1 omegaconf==2.3.0 safetensors \
        tyro==0.9.17 click==8.1.8 albumentations==1.4.18 av==16.1.0 dm-tree \
        lmdb==1.7.5 msgpack-numpy==0.4.8 pandas==2.2.3 termcolor==3.2.0 \
        datasets==3.6.0 gitpython==3.1.46 jsonlines==4.0.0 gymnasium==1.2.2 \
        matplotlib==3.10.1 scipy==1.15.3 "opencv-python-headless>=4.5,<4.13" \
        pyzmq==27.0.1 msgpack==1.1.0 \
    && python -m pip install numpy==1.26.4

# Architecture and tokenizer only. Backbone weights stay in the submission.
# Cosmos-Reason2-2B matches Qwen3-VL-2B; the checkpoint tensors are applied later.
# The patch edits installed sources, so recompile them or every start recompiles in memory.
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-VL-2B-Instruct', local_dir='/opt/unidroid/qwen3vl', allow_patterns=['*.json', '*.txt'])" \
    && rm -rf /opt/unidroid/qwen3vl/.cache
COPY patch_offline_backbone.py /tmp/patch_offline_backbone.py
RUN python /tmp/patch_offline_backbone.py && rm /tmp/patch_offline_backbone.py \
    && python -m compileall -q /opt/venv/lib/python3.10/site-packages/gr00t

# Protocol package, built as a wheel so an update does not invalidate the environment layer.
# ADD resolves the branch or tag on every build, so a moved ref is never served from cache.
ARG BRAIN_COMM_REF=v1.0.0
ADD https://github.com/Unidroid-AI/brain-comm.git#${BRAIN_COMM_REF} /tmp/comm
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip wheel --no-deps --wheel-dir /wheels /tmp/comm


FROM nvidia/cuda:12.8.1-base-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}" \
    HF_HUB_OFFLINE=1 \
    TORCHINDUCTOR_CACHE_DIR=/cache/inductor \
    TRITON_CACHE_DIR=/cache/triton \
    BRAIN_COMM_CHECK=gr00t_n17_check:check \
    UNIDROID_QWEN3VL_DIR=/opt/unidroid/qwen3vl \
    PYTHONPATH=/opt/unidroid

# gcc and Python headers: triton builds its launcher when a kernel compiles. git: gitpython needs it.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-dev build-essential git \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/isaac-gr00t /opt/isaac-gr00t
COPY --from=builder /opt/unidroid /opt/unidroid

RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    python -m pip install --no-deps --no-index /wheels/*.whl

COPY gr00t_n17_check.py reference_signature.json /opt/unidroid/

WORKDIR /submission
CMD ["brain-comm", "serve", "--replicas", "1"]
