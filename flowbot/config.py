import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONFIG = {
    "quantity": {"type": "uniform", "min": 1.0, "max": 10.0},
    "interval": {"type": "uniform", "min": 3, "max": 15},
    "p_buy": 0.5,
    "max_spend_per_market": 5.0,  # USDC budget cap per market
}


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    """Load YAML config if present, otherwise return default values."""
    path = Path(path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            user_conf = yaml.safe_load(f) or {}
    else:
        user_conf = {}

    config = DEFAULT_CONFIG.copy()
    # deep merge dictionaries (simple)
    for key, val in user_conf.items():
        if isinstance(val, dict) and key in config and isinstance(config[key], dict):
            config[key].update(val)
        else:
            config[key] = val

    # markets list fallback from env TOKEN_IDS
    if "markets" not in config:
        env_ids = os.getenv("TOKEN_IDS", "")
        if env_ids:
            config["markets"] = [tid.strip() for tid in env_ids.split(",") if tid.strip()]

    # market ids list from env MARKET_IDS
    if "market_ids" not in config:
        env_mid = os.getenv("MARKET_IDS", "")
        if env_mid:
            config["market_ids"] = [mid.strip() for mid in env_mid.split(",") if mid.strip()]

    return config 