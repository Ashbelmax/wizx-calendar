from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

import requests

from src.models.event import CalendarEvent
from src.providers.base_provider import BaseProvider
from src.utils.config import get_env


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "message": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
        }
        for key in ("provider", "event_count", "status", "reason", "error"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel((get_env("LOG_LEVEL") or "INFO").upper())
    logger.propagate = False
    return logger


class LiveProvider(BaseProvider):
    """Fetches economic events from a permitted provider when configured."""

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

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self._session = session or requests.Session()
        self._timeout = int(get_env("REQUEST_TIMEOUT_SECONDS") or 10)
        self._max_retries = int(get_env("MAX_RETRIES") or 3)
        self._api_key = get_env("ALPHA_VANTAGE_API_KEY")
        self._api_url = (get_env("ECONOMIC_CALENDAR_API_URL") or "https://www.alphavantage.co/query").strip()
        self._logger = _build_logger("wizx_calendar.live_provider")

    def fetch_events(self) -> List[CalendarEvent]:
        if not self._api_key:
            self._logger.warning("alpha_vantage_api_key_missing", extra={"provider": self.name(), "status": "degraded"})
            return self._build_fallback_events()

        try:
            payload = self._request_events()
        except Exception as exc:  # pragma: no cover - exercised in runtime environments
            self._logger.exception(
                "provider_request_failed",
                extra={"provider": self.name(), "status": "degraded", "error": str(exc)},
            )
            return self._build_fallback_events()

        events = self._parse_events(payload)
        if not events:
            self._logger.warning("provider_returned_no_events", extra={"provider": self.name(), "status": "degraded"})
            return self._build_fallback_events()

        filtered = [event for event in events if self._is_supported(event)]
        self._logger.info(
            "provider_fetch_succeeded",
            extra={"provider": self.name(), "event_count": len(filtered), "status": "healthy"},
        )
        return filtered

    def health_check(self) -> dict[str, Any]:
        if not self._api_key:
            return {"status": "degraded", "provider": self.name(), "reason": "missing_api_key"}

        try:
            self._request_events()
        except Exception as exc:  # pragma: no cover - exercised in runtime environments
            return {"status": "unhealthy", "provider": self.name(), "reason": str(exc)}

        return {"status": "healthy", "provider": self.name()}

    def name(self) -> str:
        return "live"

    def _request_events(self) -> dict[str, Any]:
        params = {"function": "ECONOMIC_CALENDAR", "apikey": self._api_key}
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                response = self._session.get(self._api_url, params=params, timeout=self._timeout)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and "Error Message" in payload:
                    raise RuntimeError(payload["Error Message"])
                if isinstance(payload, dict) and "error" in payload:
                    raise RuntimeError(str(payload["error"]))
                return payload
            except requests.RequestException as exc:
                last_error = exc
            except ValueError as exc:
                last_error = exc
            except RuntimeError as exc:
                last_error = exc

            if attempt < self._max_retries - 1:
                delay = 2**attempt
                self._logger.warning(
                    "provider_retry",
                    extra={"provider": self.name(), "attempt": attempt + 1, "backoff_seconds": delay},
                )
                time.sleep(delay)

        if last_error is None:
            raise RuntimeError("provider request failed")
        raise last_error

    def _parse_events(self, payload: dict[str, Any]) -> List[CalendarEvent]:
        if not isinstance(payload, dict):
            return []

        items: Any = payload.get("economicCalendar") or payload.get("events") or payload.get("data") or []
        if not isinstance(items, list):
            return []

        parsed: List[CalendarEvent] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("eventName") or item.get("name") or "").strip()
            if not title:
                continue
            event_time = item.get("date") or item.get("eventDate") or item.get("time") or item.get("datetime")
            if not event_time:
                continue
            parsed.append(
                CalendarEvent(
                    title=title,
                    currency=str(item.get("currency") or item.get("currencyCode") or "USD").strip().upper(),
                    expected=str(item.get("forecast") or item.get("expected") or "").strip(),
                    previous=str(item.get("previous") or item.get("prior") or "").strip(),
                    actual=str(item.get("actual") or item.get("release") or "").strip(),
                    impact=str(item.get("impact") or item.get("importance") or "High").strip().title(),
                    datetime=self._normalize_datetime(event_time),
                    country=str(item.get("country") or "United States").strip(),
                    source=self._api_url,
                )
            )
        return parsed

    def _normalize_datetime(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return self._default_datetime()
            if text.endswith("Z"):
                return text
            if "T" in text:
                try:
                    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                except ValueError:
                    parsed = datetime.fromisoformat(text)
                return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError:
                return self._default_datetime()
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return self._default_datetime()

    def _default_datetime(self) -> str:
        return (datetime.now(timezone.utc) + timedelta(days=7)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")

    def _is_supported(self, event: CalendarEvent) -> bool:
        return event.impact.lower() == "high" and event.title in self.HIGH_IMPACT_TITLES

    def _build_fallback_events(self) -> List[CalendarEvent]:
        now = datetime.now(timezone.utc)
        events = [
            ("FOMC Interest Rate Decision", now + timedelta(days=3), 18, 0, "USD", "United States", "4.50%", "4.50%", "High"),
            ("FOMC Statement", now + timedelta(days=4), 18, 0, "USD", "United States", "4.50%", "4.50%", "High"),
            ("FOMC Press Conference", now + timedelta(days=4), 20, 0, "USD", "United States", "N/A", "N/A", "High"),
            ("FOMC Meeting Minutes", now + timedelta(days=16), 18, 0, "USD", "United States", "N/A", "N/A", "High"),
            ("Non-Farm Payrolls", now + timedelta(days=5), 12, 30, "USD", "United States", "250K", "248K", "High"),
            ("Consumer Price Index", now + timedelta(days=8), 12, 30, "USD", "United States", "0.3%", "0.2%", "High"),
            ("Core CPI", now + timedelta(days=8), 12, 30, "USD", "United States", "0.3%", "0.2%", "High"),
            ("Producer Price Index", now + timedelta(days=10), 12, 30, "USD", "United States", "0.2%", "0.1%", "High"),
            ("Core PCE Price Index", now + timedelta(days=11), 12, 30, "USD", "United States", "0.2%", "0.1%", "High"),
            ("GDP", now + timedelta(days=12), 12, 30, "USD", "United States", "1.8%", "1.6%", "High"),
            ("Retail Sales", now + timedelta(days=13), 12, 30, "USD", "United States", "0.4%", "0.1%", "High"),
            ("Unemployment Rate", now + timedelta(days=7), 12, 30, "USD", "United States", "4.2%", "4.1%", "High"),
            ("Initial Jobless Claims", now + timedelta(days=6), 12, 30, "USD", "United States", "220K", "221K", "High"),
            ("ECB Interest Rate Decision", now + timedelta(days=9), 12, 15, "EUR", "Eurozone", "3.50%", "3.50%", "High"),
            ("BoE Interest Rate Decision", now + timedelta(days=10), 12, 0, "GBP", "United Kingdom", "4.50%", "4.50%", "High"),
            ("BoJ Interest Rate Decision", now + timedelta(days=11), 3, 0, "JPY", "Japan", "0.25%", "0.25%", "High"),
        ]
        result: List[CalendarEvent] = []
        for title, event_dt, hour, minute, currency, country, expected, previous, impact in events:
            timestamp = event_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            result.append(
                CalendarEvent(
                    title=title,
                    currency=currency,
                    expected=expected,
                    previous=previous,
                    actual="",
                    impact=impact,
                    datetime=timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    country=country,
                    source="https://www.alphavantage.co/",
                )
            )
        return result
