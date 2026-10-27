# GR00T N1.7 brain image

Built once by Unidroid and reused by every challenge whose model is GR00T N1.7. The image contains the runtime and the architecture check. It does not contain model weights. Participants mount a submission at `/submission`.

The submission safetensors already include the Cosmos-Reason2 backbone. The image builds that module from the public Qwen3-VL-2B architecture config under `/opt/unidroid/qwen3vl` and then loads the submission tensors. Serving a checkpoint does not contact `nvidia/Cosmos-Reason2-2B`.

Before publishing, seal `reference_signature.json` from the base checkpoint:

```
python -c "from gr00t_n17_check import seal_from_directory; from pathlib import Path; seal_from_directory(Path('weights'), Path('reference_signature.json'))"
```

`sealed` must be true. An unsealed reference rejects every submission.

```
bash gr00t-n17-v0/build_and_push.sh   # pushes ghcr.io/unidroid-ai/brain:gr00t-n17-v0 and prints the digest
```

The build fetches `brain-comm` at `v1.0.0` over HTTPS, so that repository must be public. To build another ref, pass `--build-arg BRAIN_COMM_REF=<tag>`.

The script prints `repo@sha256:...`. That digest is the phase config's `brain_image`.
