from __future__ import annotations

import yaml

from pipeline.paths import CONFIG_PATH


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
