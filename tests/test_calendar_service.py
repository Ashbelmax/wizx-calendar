import json
from datetime import datetime, timezone

from src.models.event import CalendarEvent
from src.services.calendar_service import CalendarService


def test_calendar_event_to_description() -> None:
    event = CalendarEvent(
        title="FOMC Interest Rate Decision",
        currency="USD",
        expected="4.50%",
        previous="4.50%",
        actual="",
        impact="High",
        datetime="2026-07-15T18:00:00Z",
        country="United States",
        source="https://www.alphavantage.co/",
    )
    description = CalendarService.build_description(event)
    assert "Expected: 4.50%" in description
    assert "Previous: 4.50%" in description
    assert "Currency: USD" in description
    assert "Impact: High" in description
    assert "More Information:" in description


def test_calendar_event_to_ics() -> None:
    event = CalendarEvent(
        title="FOMC Interest Rate Decision",
        currency="USD",
        expected="4.50%",
        previous="4.50%",
        actual="",
        impact="High",
        datetime="2026-07-15T18:00:00Z",
        country="United States",
        source="https://www.alphavantage.co/",
    )
    ics = CalendarService.build_ics([event])
    assert "BEGIN:VCALENDAR" in ics
    assert "METHOD:PUBLISH" in ics
    assert "BEGIN:VEVENT" in ics
    assert "UID:" in ics
    assert "DTSTAMP:" in ics
    assert "DTSTART:" in ics
    assert "DTEND:" in ics
    assert "SUMMARY:FOMC Interest Rate Decision" in ics
    assert "DESCRIPTION:" in ics
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-PT30M" in ics
    assert "END:VCALENDAR" in ics


def test_json_export_uses_expected_shape() -> None:
    event = CalendarEvent(
        title="Non-Farm Payrolls",
        currency="USD",
        expected="250K",
        previous="248K",
        actual="",
        impact="High",
        datetime="2026-07-03T12:30:00Z",
        country="United States",
        source="https://www.alphavantage.co/",
    )
    data = CalendarService.export_json([event])
    payload = json.loads(data)
    assert isinstance(payload, list)
    assert payload[0]["title"] == "Non-Farm Payrolls"
    assert payload[0]["impact"] == "High"
    assert payload[0]["currency"] == "USD"
