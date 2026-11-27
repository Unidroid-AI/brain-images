<p align="center">
  <strong>UNIDROID</strong><br>
  Training general and custom robot brains through challenges.
</p>

<h1 align="center">brain-images</h1>

<p align="center">
  One Docker image per model family. Each image runs a submission through <code>brain-comm</code>.
</p>

```
model family  â”€â”€brain imageâ”€â”€  /submission
              brain-comm v1.0.0
```

## Families

```
gr00t-n17-v0/       GR00T N1.7
pi0.5-v0/           pi0.5
flux3-action-v0/    FLUX 3 Action
```

The folder names the runtime and its version. An incompatible runtime is a new folder, such as `gr00t-n17-v1`. It does not add a repository. Challenges pull the image by digest.

## brain-comm

All families install the same brain-comm: the ref in `brain-comm.lock`. `scripts/resolve_brain_comm.sh` turns it into a commit and reads `PROTOCOL_VERSION` at that commit. The build scripts and the publish workflow pass both to the Dockerfile, which installs exactly that commit, fails when the package reports another protocol, and labels the image:

| Label | Value |
|---|---|
| `ai.unidroid.brain-comm.commit` | the brain-comm commit installed in the image |
| `ai.unidroid.brain-comm.protocol` | `PROTOCOL_VERSION` at that commit |

A challenge pins no brain-comm. Its brain image is the server and its sandbox image is the client, and their protocol labels must be equal. A brain-comm release that keeps `PROTOCOL_VERSION` needs no rebuild. A new `PROTOCOL_VERSION` means rebuilding every family, registering each digest as a new brain in Admin, and publishing a new sandbox (unidroid-sandbox).

## Build

BuildKit is required. It has been the default since Docker 23. Build through the family's script, which adds the brain-comm commit and protocol (see brain-comm above), checks the image against its label and pushes it (see Publish).

Each image is two stages: a builder with compilers and git, and a CUDA runtime that receives only the environment. The framework wheels bring their own CUDA libraries.

Mount `-v brain-cache:/cache` so a restarted brain does not recompile. Without the mount the JIT caches are lost on exit.

## Publish

All families live in one public GHCR package, `ghcr.io/unidroid-ai/brain`, with one tag per folder (`brain:gr00t-n17-v0`). Tags are labels; the platform and validators use the digest, `ghcr.io/unidroid-ai/brain@sha256:...`.

Either run the **publish** workflow (Actions â†’ publish â†’ pick the folder; the digest is in the job summary), or push by hand:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <user> --password-stdin   # token with write:packages
bash gr00t-n17-v0/build_and_push.sh
```

After the first push, set the package to **public** (GitHub â†’ Packages â†’ brain â†’ Package settings). Validators pull without credentials, and a private package answers them with 401. Then paste the digest into Admin â†’ Brains.

## Adding a family

A new model family, or an incompatible runtime for an existing one, is ready for a challenge when all of these hold:

1. **Folder.** `<family>-v<N>/` with a two-stage `Dockerfile`, a `build_and_push.sh` that prints `repo@sha256:...`, and a README covering the base checkpoint and how to seal any reference.
2. **Runtime.** The image installs the `brain-comm` commit that `brain-comm.lock` resolves to, labels itself `ai.unidroid.brain-comm.commit` and `ai.unidroid.brain-comm.protocol`, and runs `/submission` through `brain-comm serve`. It downloads nothing at serve time: validators run with no network.
3. **Submission check.** `BRAIN_COMM_CHECK=module:function` rejects a submission whose weights do not fit the architecture (shapes, dtypes, missing tensors). If it compares against a reference signature, the committed one must be sealed (see `gr00t-n17-v0`).
4. **Reference submission.** A minimal submission built from the base checkpoint passes `brain-comm check` and `brain-comm smoke` against the built image, and scores above zero on one public benchmark with `udcli submission eval`. Keep its Hugging Face repo as the example in the Brain tab.
5. **Platform record.** Admin â†’ Brains has the id (the folder name), family, model type, the image **digest** (not a tag), base checkpoint, checkpoint format, action space and dimension, and `max_gpu_mem_gb` measured on the reference submission.
6. **Allowed files.** `submission_code` stays off unless the family must ship its own code (world models). Then validators run it in the split sandbox (PROTOCOL.md, section 7), and the evaluator must be tested in all three stages.
7. **Miner notes.** The Brain tab description lists the `agent.yaml` settings and required files. `udcli submission check` passes on the reference repo.
8. **Submission template.** Every brain has a template repo, `template-<brain>`, in the Unidroid-AI GitHub organization (`README.md`, `agent.yaml`, `brain/`, `train/`, `tests/`, and a script that fetches the base checkpoint into `weights/`). Add it to `TEMPLATES` in `unidroid-cli/src/unidroid_cli/templates.py` and set `template_repo` on the brain in Admin â†’ Brains. The Brain tab and `udcli submission init` use them.

Add the family to a challenge only after a test-mode challenge (whitelisted accounts) has scored the reference submission end to end with at least two validators.

## License

BSD-3-Clause. Copyright (c) 2026 Unidroid. See [LICENSE](LICENSE).
