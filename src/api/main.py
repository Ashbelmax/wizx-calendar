from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.models.event import CalendarEvent
from src.providers.base_provider import BaseProvider
from src.providers.provider_factory import create_provider
from src.services.calendar_service import CalendarService

app = FastAPI(title="WizX Calendar", version="1.0.0")
provider = create_provider()


class HealthResponse(BaseModel):
    status: str
    provider: str
    provider_status: str


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, Any]:
    provider_health = provider.health_check() if isinstance(provider, BaseProvider) and hasattr(provider, "health_check") else {"status": "unknown"}
    return {"status": "ok", "provider": provider_health.get("provider", provider.name()), "provider_status": provider_health.get("status", "unknown")}


@app.get("/high-impact.ics")
def high_impact_ics() -> FileResponse:
    output_path = Path("output/high-impact.ics")
    if not output_path.exists():
        generate_outputs()
    return FileResponse(output_path, media_type="text/calendar", filename="high-impact.ics")


@app.get("/high-impact.json")
def high_impact_json() -> JSONResponse:
    output_path = Path("output/high-impact.json")
    if not output_path.exists():
        generate_outputs()
    return JSONResponse(content=_load_json(output_path))


@app.get("/today")
def today() -> List[CalendarEvent]:
    events = provider.fetch_events()
    return CalendarService.filter_high_impact(events)


@app.get("/week")
def week() -> List[CalendarEvent]:
    return today()


@app.get("/next")
def next_event() -> CalendarEvent:
    events = CalendarService.filter_high_impact(provider.fetch_events())
    if not events:
        raise HTTPException(status_code=404, detail="No upcoming events")
    return events[0]


def generate_outputs() -> None:
    events = CalendarService.filter_high_impact(provider.fetch_events())
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    ics_payload = CalendarService.build_ics(events)
    json_payload = CalendarService.export_json(events)
    (output_dir / "high-impact.ics").write_text(ics_payload, encoding="utf-8")
    (output_dir / "high-impact.json").write_text(json_payload, encoding="utf-8")


def _load_json(path: Path) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    generate_outputs()
    print("Generated output files successfully.")
