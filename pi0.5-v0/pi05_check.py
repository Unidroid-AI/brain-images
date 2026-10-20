# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Architecture check for a pi0.5 submission.

The hook reads the orbax parameter tree stored in ``weights/params/_METADATA``.
It accepts a pi0.5 flow model (time MLP plus a 32-D action projection) with
DROID norm stats. It does not judge how the weights were trained.
"""

from __future__ import annotations

import json
from pathlib import Path

POLICY_CONFIG = "pi05_droid_jointpos"
_ACTION_IN = "('params', 'action_in_proj', 'kernel')"
_TIME_MLP = "('params', 'time_mlp_in', 'kernel')"
_ACTION_IN_SHAPE = [32, 1024]


def check(submission: Path, config: dict) -> str | None:
    """Return an error string, or None when the checkpoint matches."""
    if config.get("policy_config") != POLICY_CONFIG:
        return f"agent.yaml policy_config must be {POLICY_CONFIG}"
    weights = Path(submission) / "weights"
    try:
        tree = _parameter_tree(weights)
        stats = _norm_stats(weights)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return f"cannot read pi0.5 checkpoint: {exc}"
    action_in = tree.get(_ACTION_IN, {}).get("value_metadata", {}).get("write_shape")
    if list(action_in or []) != _ACTION_IN_SHAPE:
        return "action_in_proj kernel does not match the pi0.5 reference"
    if _TIME_MLP not in tree:
        return "checkpoint is not pi0.5; time_mlp_in is missing"
    for name in ("state", "actions"):
        block = stats.get(name)
        if not isinstance(block, dict) or "q01" not in block or "q99" not in block:
            return f"DROID norm stats are missing quantile bounds for {name}"
    return None


def _parameter_tree(weights: Path) -> dict:
    path = weights / "params" / "_METADATA"
    if not path.is_file():
        raise ValueError("weights/params/_METADATA is missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    tree = payload.get("tree_metadata")
    if not isinstance(tree, dict):
        raise ValueError("weights/params/_METADATA has no parameter tree")
    return tree


def _norm_stats(weights: Path) -> dict:
    path = weights / "assets" / "droid" / "norm_stats.json"
    if not path.is_file():
        raise ValueError("weights/assets/droid/norm_stats.json is missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    stats = payload.get("norm_stats")
    if not isinstance(stats, dict):
        raise ValueError("norm_stats.json has no norm_stats object")
    return stats
