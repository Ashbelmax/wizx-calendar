from __future__ import annotations

from src.providers.base_provider import BaseProvider
from src.providers.live_provider import LiveProvider
from src.utils.config import get_env


def create_provider() -> BaseProvider:
    provider_name = (get_env("DATA_PROVIDER") or "live").strip().lower()
    if provider_name in {"live", "alphavantage"}:
        return LiveProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")
