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

## License

BSD-3-Clause. Copyright (c) 2026 Unidroid. See [LICENSE](LICENSE).
