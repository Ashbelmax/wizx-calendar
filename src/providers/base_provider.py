from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from src.models.event import CalendarEvent


class BaseProvider(ABC):
    @abstractmethod
    def fetch_events(self) -> List[CalendarEvent]:
        """Fetch events from a specific data source."""

    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    def health_check(self) -> dict[str, Any]:
        """Return a lightweight provider health summary."""
        return {"status": "healthy", "provider": self.name()}
