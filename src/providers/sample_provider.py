from __future__ import annotations

from src.providers.live_provider import LiveProvider


class SampleProvider(LiveProvider):
    """Backward-compatible provider shim that uses the live implementation."""

    def name(self) -> str:
        return "sample"
