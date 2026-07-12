from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Iterable, List

from src.models.event import CalendarEvent


class CalendarService:
    HIGH_IMPACT_TITLES = {
        "FOMC Interest Rate Decision",
        "FOMC Statement",
        "FOMC Press Conference",
        "FOMC Meeting Minutes",
        "Non-Farm Payrolls",
        "Consumer Price Index",
        "Core CPI",
        "Producer Price Index",
        "Core PCE Price Index",
        "GDP",
        "Retail Sales",
        "Unemployment Rate",
        "Initial Jobless Claims",
        "ECB Interest Rate Decision",
        "BoE Interest Rate Decision",
        "BoJ Interest Rate Decision",
    }

    @classmethod
    def filter_high_impact(cls, events: Iterable[CalendarEvent]) -> List[CalendarEvent]:
        return [event for event in events if event.impact.lower() == "high" and event.title in cls.HIGH_IMPACT_TITLES]

    @classmethod
    def build_description(cls, event: CalendarEvent) -> str:
        return "\n".join(
            [
                f"Expected: {event.expected}",
                f"Previous: {event.previous}",
                f"Actual: {event.actual or 'N/A'}",
                f"Currency: {event.currency}",
                f"Impact: {event.impact}",
                f"Country: {event.country}",
                "",
                "More Information:",
                event.source,
            ]
        )

    @classmethod
    def build_ics(cls, events: Iterable[CalendarEvent]) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//WizX Calendar//EN",
            "METHOD:PUBLISH",
            "CALSCALE:GREGORIAN",
        ]
        for event in events:
            start_dt = cls._parse_datetime(event.datetime)
            end_dt = start_dt + timedelta(minutes=30)
            uid = f"{event.title}-{start_dt.strftime('%Y%m%dT%H%M%SZ')}".replace(" ", "")
            description = cls._escape_ics_text(cls.build_description(event))
            summary = cls._escape_ics_text(event.title)
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%SZ')}",
                    f"SUMMARY:{summary}",
                    f"DESCRIPTION:{description}",
                    "BEGIN:VALARM",
                    "ACTION:DISPLAY",
                    "DESCRIPTION:Reminder",
                    "TRIGGER:-PT30M",
                    "END:VALARM",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    @classmethod
    def export_json(cls, events: Iterable[CalendarEvent]) -> str:
        payload = [event.to_dict() for event in events]
        return json.dumps(payload, indent=2)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        return datetime.fromisoformat(value).astimezone(timezone.utc)

    @staticmethod
    def _escape_ics_text(value: str) -> str:
        return value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "")
