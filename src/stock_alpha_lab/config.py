"""Project configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    sec_user_agent: str = os.getenv("SEC_USER_AGENT", "")
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", "data/raw"))
    processed_data_dir: Path = Path(
        os.getenv("PROCESSED_DATA_DIR", "data/processed")
    )


def get_settings() -> Settings:
    """Return project settings."""

    return Settings()
