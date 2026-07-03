"""Configuration loader for Mintabie agent.

Config priority:
  1. Environment variables
  2. ~/.mintabie/config.yaml
  3. Defaults
"""

import os
import yaml
from pathlib import Path

MINTABIE_HOME = Path.home() / ".mintabie"
CONFIG_PATH = MINTABIE_HOME / "config.yaml"

DEFAULT_CONFIG = {
    "model": {
        "default": "gpt-4o",
        "provider": "openai",
        "base_url": "",
        "api_key": "",
        "max_tokens": 4096,
        "context_length": 128000,
    },
    "agent": {
        "max_iterations": 90,
        "tool_delay": 0.5,
    },
    "terminal": {
        "timeout": 180,
    },
    "compression": {
        "enabled": True,
        "threshold_ratio": 0.50,
        "target_ratio": 0.20,
    },
    "providers": {
        "openai": {"api_key": "", "base_url": ""},
        "anthropic": {"api_key": "", "base_url": ""},
        "ollama": {"api_key": "", "base_url": "http://localhost:11434/v1"},
    },
}


def load_config() -> dict:
    """Load config, merging defaults + yaml + env overrides."""
    config = DEFAULT_CONFIG.copy()

    # Ensure MINTABIE_HOME exists
    MINTABIE_HOME.mkdir(parents=True, exist_ok=True)

    # Load YAML if exists
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            yaml_config = yaml.safe_load(f) or {}
        _deep_merge(config, yaml_config)

    # Env overrides
    if os.environ.get("OPENAI_API_KEY"):
        config["model"]["api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("OPENAI_BASE_URL"):
        config["model"]["base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.environ.get("MINTABIE_MODEL"):
        config["model"]["default"] = os.environ["MINTABIE_MODEL"]
    if os.environ.get("MINTABIE_PROVIDER"):
        config["model"]["provider"] = os.environ["MINTABIE_PROVIDER"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        config.setdefault("providers", {})
        config["providers"].setdefault("anthropic", {})
        config["providers"]["anthropic"]["api_key"] = os.environ["ANTHROPIC_API_KEY"]

    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override into base."""
    for key, val in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deep_merge(base[key], val)
        else:
            base[key] = val
