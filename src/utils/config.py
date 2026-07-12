from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
