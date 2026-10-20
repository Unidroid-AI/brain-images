# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import importlib.util
import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "flux3-action-v0" / "flux3_check.py"
_spec = importlib.util.spec_from_file_location("flux3_check", _PATH)
hook = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hook)

_CONFIG = {"policy_config": "flux3_action_droid", "flux_subfolder": ""}


def test_matching_package_passes(tmp_path: Path):
    _submission(tmp_path)
    assert hook.check(tmp_path, _CONFIG) is None


def test_guidance_distilled_subfolder_passes(tmp_path: Path):
    _submission(tmp_path, subfolder="variants/gd")
    assert hook.check(tmp_path, {**_CONFIG, "flux_subfolder": "variants/gd"}) is None


def test_native_config_takes_precedence(tmp_path: Path):
    _submission(tmp_path, native={"camera_layout": "droid", "action_dim": 8, "chunk_size": 32})
    assert hook.check(tmp_path, _CONFIG) is None


def test_wrong_policy_config_rejects(tmp_path: Path):
    _submission(tmp_path)
    message = hook.check(tmp_path, {**_CONFIG, "policy_config": "pi05_droid_jointpos"})
    assert message is not None
    assert "policy_config" in message


def test_fp8r_subfolder_rejects(tmp_path: Path):
    _submission(tmp_path)
    message = hook.check(tmp_path, {**_CONFIG, "flux_subfolder": "variants/fp8r"})
    assert message is not None
    assert "FP8r" in message


def test_unknown_subfolder_rejects(tmp_path: Path):
    _submission(tmp_path)
    message = hook.check(tmp_path, {**_CONFIG, "flux_subfolder": "variants/other"})
    assert message is not None
    assert "flux_subfolder" in message


def test_missing_model_file_rejects(tmp_path: Path):
    _submission(tmp_path, model=False)
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "model.safetensors" in message


def test_other_camera_layout_rejects(tmp_path: Path):
    _submission(tmp_path, policy={"camera_layout": "side_by_side"})
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "camera_layout" in message


def test_action_width_mismatch_rejects(tmp_path: Path):
    _submission(tmp_path, policy={"action_dim": 6})
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "action_dim" in message


def test_quantized_config_rejects(tmp_path: Path):
    _submission(tmp_path, policy={"quantization": "fp8r"})
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "quantized" in message


def test_delta_actions_reject(tmp_path: Path):
    _submission(tmp_path, policy={"action_parameterization": "joint_delta"})
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "absolute" in message


def test_missing_video_vae_rejects(tmp_path: Path):
    _submission(tmp_path, vae=False)
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "video_vae" in message


def test_missing_text_encoder_rejects(tmp_path: Path):
    _submission(tmp_path, text_encoder=False)
    message = hook.check(tmp_path, _CONFIG)
    assert message is not None
    assert "text_encoder" in message


def _submission(
    path: Path,
    *,
    subfolder: str = "",
    policy: dict | None = None,
    native: dict | None = None,
    model: bool = True,
    vae: bool = True,
    text_encoder: bool = True,
) -> None:
    weights = path / "weights"
    package = weights / "policy" / subfolder if subfolder else weights / "policy"
    package.mkdir(parents=True)
    base = {"camera_layout": "droid", "action_dim": 8, "chunk_size": 32}
    (package / "config.json").write_text(json.dumps({**base, **(policy or {})}), encoding="utf-8")
    (package / "manifest.json").write_text("{}", encoding="utf-8")
    if native is not None:
        (package / "config.native.json").write_text(json.dumps(native), encoding="utf-8")
    if model:
        (package / "model.safetensors").write_bytes(b"")
    if vae:
        (weights / "video_vae.safetensors").write_bytes(b"")
    if text_encoder:
        encoder = weights / "text_encoder"
        encoder.mkdir()
        (encoder / "config.json").write_text("{}", encoding="utf-8")
        (encoder / "model-00001-of-00002.safetensors").write_bytes(b"")
