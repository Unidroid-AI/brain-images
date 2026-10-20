# Copyright (c) 2026, Unidroid
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Build the GR00T backbone from a local Qwen3-VL config.

Isaac-GR00T constructs ``Qwen3VLForConditionalGeneration`` by calling
``from_pretrained("nvidia/Cosmos-Reason2-2B")``. The submission safetensors
already contain those tensors, and Transformers loads them after ``__init__``.
This patch allocates the module from the public Qwen3-VL-2B architecture
config, which matches Cosmos-Reason2-2B, and loads the tokenizer from disk.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _site_gr00t() -> Path:
    for entry in sys.path:
        candidate = Path(entry) / "gr00t" / "model" / "modules" / "qwen3_backbone.py"
        if candidate.is_file():
            return candidate.parent.parent.parent
    raise SystemExit("installed gr00t package was not found")


def _replace(path: Path, pattern: re.Pattern[str], new: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(new, text, count=1)
    if count != 1:
        raise SystemExit(f"pattern missing in {path}")
    path.write_text(updated, encoding="utf-8")


def _patch_backbone(package: Path) -> None:
    path = package / "model" / "modules" / "qwen3_backbone.py"
    text = path.read_text(encoding="utf-8")
    if "import os\n" not in text:
        text = text.replace("import logging\n", "import logging\nimport os\n", 1)
        path.write_text(text, encoding="utf-8")
    _replace(
        path,
        re.compile(
            r"[ \t]*self\.model = Qwen3VLForConditionalGeneration\.from_pretrained\(\s*"
            r"model_name,\s*\*\*extra_kwargs,\s*\*\*transformers_loading_kwargs,\s*\)\.eval\(\)",
            re.S,
        ),
        "        from transformers import Qwen3VLConfig\n"
        "\n"
        "        local_dir = os.environ.get(\"UNIDROID_QWEN3VL_DIR\", \"/opt/unidroid/qwen3vl\")\n"
        "        backbone_config = Qwen3VLConfig.from_pretrained(local_dir, local_files_only=True)\n"
        "        full_layers = backbone_config.text_config.num_hidden_layers\n"
        "        if 0 < select_layer < full_layers:\n"
        "            backbone_config.text_config.num_hidden_layers = select_layer\n"
        "        backbone_config.tie_word_embeddings = False\n"
        "        backbone_config.text_config.tie_word_embeddings = False\n"
        "        attention = extra_kwargs.get(\"attn_implementation\")\n"
        "        if attention:\n"
        "            backbone_config._attn_implementation = attention\n"
        "            backbone_config.text_config._attn_implementation = attention\n"
        "            backbone_config.vision_config._attn_implementation = attention\n"
        "        self.model = Qwen3VLForConditionalGeneration(backbone_config)\n"
        "        dtype = extra_kwargs.get(\"torch_dtype\")\n"
        "        if dtype is not None:\n"
        "            self.model = self.model.to(dtype=dtype)\n"
        "        self.model = self.model.eval()",
    )


def _patch_processor(package: Path) -> None:
    path = package / "model" / "gr00t_n1d7" / "processing_gr00t_n1d7.py"
    text = path.read_text(encoding="utf-8")
    if "import os\n" not in text:
        text = text.replace("import logging\n", "import logging\nimport os\n", 1)
        if "import os\n" not in text:
            text = "import os\n" + text
        path.write_text(text, encoding="utf-8")
    _replace(
        path,
        re.compile(
            r"[ \t]*return Qwen3VLProcessor\.from_pretrained\(model_name, \*\*transformers_loading_kwargs\)"
        ),
        "    local_dir = os.environ.get(\"UNIDROID_QWEN3VL_DIR\", \"/opt/unidroid/qwen3vl\")\n"
        "    if \"Cosmos-Reason2\" in model_name or \"Qwen3-VL\" in model_name:\n"
        "        return Qwen3VLProcessor.from_pretrained(local_dir, local_files_only=True)\n"
        "    return Qwen3VLProcessor.from_pretrained(model_name, **transformers_loading_kwargs)",
    )


def main() -> None:
    package = _site_gr00t()
    _patch_backbone(package)
    _patch_processor(package)


if __name__ == "__main__":
    main()
