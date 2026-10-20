# FLUX 3 Action brain image

Built once by Unidroid and reused by every challenge whose model is FLUX 3 Action. The image contains the [flux-action](https://github.com/black-forest-labs/flux-action) runtime at a pinned commit and the architecture check. It does not contain model weights. Participants mount a submission at `/submission`.

The runtime is Python 3.12 with torch 2.10 (CUDA 12.8) and transformers 5.16.1 from flux-action's lock, plus NATTEN 0.21.6 for the video VAE. The host driver must be 570 or newer. `HF_HUB_OFFLINE` is 1, so the video VAE and text encoder must be stored under `weights/`.

The check accepts a BF16 DROID package: `agent.yaml` sets `policy_config` to `flux3_action_droid`, and `flux_subfolder` is empty (the root package), `variants/gd`, or `variants/sd`. FP8r packages are rejected because they need an SM89 or newer GPU. The package config must use the `droid` camera layout, 8-D absolute actions, and a 32-step chunk.

Expected `weights/` layout:

```
policy/             # config.json, manifest.json, model.safetensors (variants/ for gd or sd)
video_vae.safetensors
text_encoder/       # Qwen3-VL-4B: config.json and safetensors shards
```

```
bash flux3-action-v0/build_and_push.sh registry.example/brain-flux3-action-v0:phase
```

The build fetches `brain-comm` at `v1.0.0` over HTTPS, so that repository must be public. To build another ref, pass `--build-arg BRAIN_COMM_REF=<tag>`.

The script prints `repo@sha256:...`. That digest is the phase config's `brain_image`.
