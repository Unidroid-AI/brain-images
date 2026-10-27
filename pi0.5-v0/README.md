# pi0.5 brain image

Built once by Unidroid and reused by every challenge whose model is pi0.5. The image contains the OpenPI runtime and the architecture check. It does not contain model weights. Participants mount a submission at `/submission`.

The runtime is OpenPI at commit `215abfb217dbac7d5f1273282331b9b1866c0479`. It serves JAX orbax checkpoints. `XLA_PYTHON_CLIENT_MEM_FRACTION` defaults to 0.5 so the simulator can share the GPU. The pi0.5 sample submission replaces it with its `max_gpu_mem_gb` divided by the GPU size. The PaliGemma sentencepiece tokenizer is cached in the image, so serving a checkpoint does not contact `gs://big_vision`.

The check accepts a pi0.5 flow checkpoint (`time_mlp_in` and a 32-D `action_in_proj`) with DROID quantile norm stats. `agent.yaml` must set `policy_config` to `pi05_droid_jointpos`. That config decodes the first seven action dimensions as joint-position deltas and leaves the gripper absolute.

```
bash pi0.5-v0/build_and_push.sh   # pushes ghcr.io/unidroid-ai/brain:pi0.5-v0 and prints the digest
```

The build fetches `brain-comm` at `v1.0.0` over HTTPS, so that repository must be public. To build another ref, pass `--build-arg BRAIN_COMM_REF=<tag>`.

The script prints `repo@sha256:...`. That digest is the phase config's `brain_image`.
