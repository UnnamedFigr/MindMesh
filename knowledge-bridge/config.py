"""Configuration loader for knowledge-bridge.

The bridge is driven entirely by bridge.config.json.
To migrate to another project: copy knowledge-bridge/, edit bridge.config.json.
"""
import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


BRIDGE_DIR = Path(__file__).parent


class SyncTarget(BaseModel):
    """Maps an extraction output to a repo artifact file."""
    extraction_type: str = Field(
        description="'best_practices' or 'anti_patterns'"
    )
    filter: dict = Field(
        default_factory=dict,
        description="Key/value filters applied to extraction items. "
                    "E.g. {'applicable_to': ['backend']}",
    )
    target_file: str = Field(
        description="Path to the repo file to update, relative to bridge.config.json."
    )
    section: str = Field(
        description="Section title used inside the generated block."
    )


class BridgeConfig(BaseModel):
    # ── Project identity (change these when migrating) ──────────
    project_name: str = "MyProject"
    tech_stack: str = "Python, TypeScript, SQL"

    # ── Gemini model settings ────────────────────────────────────
    model: str = "gemini-2.5-flash"
    cache_ttl_seconds: int = 3600

    # ── Directory layout (relative to bridge.config.json) ───────
    sources_dir: str = "./sources"
    outputs_dir: str = "./outputs"
    cache_dir: str = "./cache"

    # ── Sync targets (project-specific) ─────────────────────────
    sync_targets: list[SyncTarget] = Field(default_factory=list)


def load_config(config_path: Optional[Path] = None) -> BridgeConfig:
    """Load bridge.config.json.  Falls back to defaults if file is missing."""
    if config_path is None:
        config_path = BRIDGE_DIR / "bridge.config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return BridgeConfig(**json.load(f))
    return BridgeConfig()


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set.\n"
            "Get a free key at: https://aistudio.google.com/apikey"
        )
    return key
