# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "gr00t-n17-v0" / "patch_offline_backbone.py"
_spec = importlib.util.spec_from_file_location("patch_offline_backbone", _PATH)
patch = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(patch)

_BACKBONE = """\
import logging

class Qwen3Backbone:
    def __init__(self, select_layer, load_bf16, transformers_loading_kwargs):
        extra_kwargs = {}
        if load_bf16:
            extra_kwargs["torch_dtype"] = 1

        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_name,
            **extra_kwargs,
            **transformers_loading_kwargs,
        ).eval()
"""

_PROCESSOR = """\
import logging

def build_processor(model_name, transformers_loading_kwargs):
    if missing:
        raise ImportError(
            "missing"
        )
    return Qwen3VLProcessor.from_pretrained(model_name, **transformers_loading_kwargs)
"""


def test_patch_keeps_valid_indentation(tmp_path: Path):
    package = tmp_path / "gr00t"
    backbone = package / "model" / "modules" / "qwen3_backbone.py"
    processor = package / "model" / "gr00t_n1d7" / "processing_gr00t_n1d7.py"
    backbone.parent.mkdir(parents=True)
    processor.parent.mkdir(parents=True)
    backbone.write_text(_BACKBONE, encoding="utf-8")
    processor.write_text(_PROCESSOR, encoding="utf-8")

    patch._patch_backbone(package)
    patch._patch_processor(package)

    backbone_text = backbone.read_text(encoding="utf-8")
    processor_text = processor.read_text(encoding="utf-8")
    compile(backbone_text, str(backbone), "exec")
    compile(processor_text, str(processor), "exec")
    assert "\n        from transformers import Qwen3VLConfig\n" in backbone_text
    assert "\n    local_dir = os.environ.get(" in processor_text
