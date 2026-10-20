# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Architecture check for a FLUX 3 Action DROID submission.

The hook reads the policy package's config and file layout. It accepts a BF16
DROID package (three-camera layout, 8-D absolute joint actions, 32-step chunk)
with the frozen video VAE and text encoder stored locally. It does not judge
how the weights were trained, and it never imports torch.
"""

from __future__ import annotations

import json
from pathlib import Path

POLICY_CONFIG = "flux3_action_droid"
# FP8r packages need SM89 or newer, so a BF16 package is the only one every host can run.
ALLOWED_SUBFOLDERS = ("", "variants/gd", "variants/sd")
_EXPECTED = {"camera_layout": "droid", "action_dim": 8, "chunk_size": 32}
# PolicyConfig defaults. A key missing from the config falls back to these.
_DEFAULT_ACTION_PARAMETERIZATION = "absolute"


def check(submission: Path, config: dict) -> str | None:
    """Return an error string, or None when the package matches."""
    if config.get("policy_config") != POLICY_CONFIG:
        return f"agent.yaml policy_config must be {POLICY_CONFIG}"
    subfolder = str(config.get("flux_subfolder") or "")
    if "fp8r" in subfolder:
        return "FP8r packages need SM89 or newer; use the root package, variants/gd, or variants/sd"
    if subfolder not in ALLOWED_SUBFOLDERS:
        return f"flux_subfolder must be one of {list(ALLOWED_SUBFOLDERS)}"
    weights = Path(submission) / "weights"
    package = weights / "policy" / subfolder if subfolder else weights / "policy"
    for name in ("config.json", "manifest.json", "model.safetensors"):
        if not (package / name).is_file():
            return f"weights/policy/{subfolder + '/' if subfolder else ''}{name} is missing"
    try:
        policy = _policy_config(package)
    except (OSError, ValueError) as exc:
        return f"cannot read FLUX policy config: {exc}"
    for key, expected in _EXPECTED.items():
        value = policy.get(key, expected)
        if value != expected:
            return f"policy config {key} is {value!r}; expected {expected!r}"
    if policy.get("quantization") is not None:
        return "policy package is quantized; use a BF16 package"
    if policy.get("action_parameterization", _DEFAULT_ACTION_PARAMETERIZATION) != "absolute":
        return "policy package does not predict absolute joint actions"
    if not (weights / "video_vae.safetensors").is_file():
        return "weights/video_vae.safetensors is missing"
    return _text_encoder_error(weights / "text_encoder")


def _policy_config(package: Path) -> dict:
    # The loader reads the native config when a package ships one.
    native = package / "config.native.json"
    path = native if native.is_file() else package / "config.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return payload


def _text_encoder_error(directory: Path) -> str | None:
    if not (directory / "config.json").is_file():
        return "weights/text_encoder/config.json is missing"
    if not any(directory.glob("*.safetensors")):
        return "weights/text_encoder has no safetensors shards"
    return None
