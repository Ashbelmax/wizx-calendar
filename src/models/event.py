from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class CalendarEvent:
    title: str
    currency: str
    expected: str
    previous: str
    actual: str = ""
    impact: str = "High"
    datetime: str = ""
    country: str = ""
    source: str = "https://www.alphavantage.co/"

    def to_dict(self) -> dict[str, Optional[str]]:
        return {
            "title": self.title,
            "currency": self.currency,
            "expected": self.expected,
            "previous": self.previous,
            "actual": self.actual,
            "impact": self.impact,
            "datetime": self.datetime,
            "country": self.country,
            "source": self.source,
        }
