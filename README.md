<p align="center">
  <strong>UNIDROID</strong><br>
  Training general and custom robot brains through challenges.
</p>

<h1 align="center">brain-images</h1>

<p align="center">
  One Docker image per model family. Each image runs a submission through <code>brain-comm</code>.
</p>

```
model family  ──brain image──  /submission
              brain-comm v1.0.0
```

## Families

```
gr00t-n17-v0/       GR00T N1.7
pi0.5-v0/           pi0.5
flux3-action-v0/    FLUX 3 Action
```

The folder names the runtime and its version. An incompatible runtime is a new folder, such as `gr00t-n17-v1`. It does not add a repository. Challenges pull the image by digest.

## Build

BuildKit is required. It has been the default since Docker 23.

```bash
DOCKER_BUILDKIT=1 docker build -f gr00t-n17-v0/Dockerfile -t brain-gr00t-n17-v0 gr00t-n17-v0
DOCKER_BUILDKIT=1 docker build -f pi0.5-v0/Dockerfile -t brain-pi0.5-v0 pi0.5-v0
DOCKER_BUILDKIT=1 docker build -f flux3-action-v0/Dockerfile -t brain-flux3-action-v0 flux3-action-v0
```

Each image is two stages: a builder with compilers and git, and a CUDA runtime that receives only the environment. The framework wheels bring their own CUDA libraries.

Mount `-v brain-cache:/cache` so a restarted brain does not recompile. Without the mount the JIT caches are lost on exit.

## Publish

All families live in one public GHCR package, `ghcr.io/unidroid-ai/brain`, with one tag per folder (`brain:gr00t-n17-v0`). Tags are labels; the platform and validators use the digest, `ghcr.io/unidroid-ai/brain@sha256:...`.

Either run the **publish** workflow (Actions → publish → pick the folder; the digest is in the job summary), or push by hand:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <user> --password-stdin   # token with write:packages
bash gr00t-n17-v0/build_and_push.sh
```

After the first push, set the package to **public** (GitHub → Packages → brain → Package settings). Validators pull without credentials, and a private package answers them with 401. Then paste the digest into Admin → Brains.

## Adding a family

A new model family, or an incompatible runtime for an existing one, is ready for a challenge when all of these hold:

1. **Folder.** `<family>-v<N>/` with a two-stage `Dockerfile`, a `build_and_push.sh` that prints `repo@sha256:...`, and a README covering the base checkpoint and how to seal any reference.
2. **Runtime.** The image pins `brain-comm` to a tag (`BRAIN_COMM_REF`) and runs `/submission` through `brain-comm serve`. It downloads nothing at serve time: validators run with no network.
3. **Submission check.** `BRAIN_COMM_CHECK=module:function` rejects a submission whose weights do not fit the architecture (shapes, dtypes, missing tensors). If it compares against a reference signature, the committed one must be sealed (see `gr00t-n17-v0`).
4. **Reference submission.** A minimal submission built from the base checkpoint passes `brain-comm check` and `brain-comm smoke` against the built image, and scores above zero on one public benchmark with `udcli eval local`. Keep its Hugging Face repo as the example in the Brain tab.
5. **Platform record.** Admin → Brains has the id (the folder name), family, model type, the image **digest** (not a tag), base checkpoint, checkpoint format, action space and dimension, and `max_gpu_mem_gb` measured on the reference submission.
6. **Allowed files.** `submission_code` stays off unless the family must ship its own code (world models). Then validators run it in the split sandbox (PROTOCOL.md, section 7), and the evaluator must be tested in all three stages.
7. **Miner notes.** The Brain tab description lists the `agent.yaml` settings and required files. `udcli check` passes on the reference repo.

Add the family to a challenge only after a test-mode challenge (whitelisted accounts) has scored the reference submission end to end with at least two validators.

## License

BSD-3-Clause. Copyright (c) 2026 Unidroid. See [LICENSE](LICENSE).
