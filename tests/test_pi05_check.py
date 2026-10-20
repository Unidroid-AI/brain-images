# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import importlib.util
import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "pi0.5-v0" / "pi05_check.py"
_spec = importlib.util.spec_from_file_location("pi05_check", _PATH)
hook = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hook)


def test_matching_checkpoint_passes(tmp_path: Path):
    _submission(tmp_path)
    assert hook.check(tmp_path, {"policy_config": "pi05_droid_jointpos"}) is None


def test_wrong_policy_config_rejects(tmp_path: Path):
    _submission(tmp_path)
    message = hook.check(tmp_path, {"policy_config": "pi05_droid"})
    assert message is not None
    assert "policy_config" in message


def test_velocity_checkpoint_rejects(tmp_path: Path):
    _submission(tmp_path, time_mlp=False)
    message = hook.check(tmp_path, {"policy_config": "pi05_droid_jointpos"})
    assert message is not None
    assert "time_mlp_in" in message


def test_action_shape_mismatch_rejects(tmp_path: Path):
    _submission(tmp_path, action_shape=[8, 1024])
    message = hook.check(tmp_path, {"policy_config": "pi05_droid_jointpos"})
    assert message is not None
    assert "action_in_proj" in message


def test_missing_norm_stats_rejects(tmp_path: Path):
    _submission(tmp_path, norm_stats=False)
    message = hook.check(tmp_path, {"policy_config": "pi05_droid_jointpos"})
    assert message is not None
    assert "norm_stats" in message


def _submission(
    path: Path,
    *,
    action_shape: list[int] | None = None,
    time_mlp: bool = True,
    norm_stats: bool = True,
) -> None:
    weights = path / "weights"
    params = weights / "params"
    params.mkdir(parents=True)
    tree = {
        "('params', 'action_in_proj', 'kernel')": {
            "value_metadata": {"write_shape": action_shape or [32, 1024]},
        }
    }
    if time_mlp:
        tree["('params', 'time_mlp_in', 'kernel')"] = {
            "value_metadata": {"write_shape": [1024, 1024]},
        }
    (params / "_METADATA").write_text(json.dumps({"tree_metadata": tree}), encoding="utf-8")
    if norm_stats:
        stats_dir = weights / "assets" / "droid"
        stats_dir.mkdir(parents=True)
        payload = {"norm_stats": {"state": {"q01": [0], "q99": [1]}, "actions": {"q01": [0], "q99": [1]}}}
        (stats_dir / "norm_stats.json").write_text(json.dumps(payload), encoding="utf-8")
