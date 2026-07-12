from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "provider" in response.json()


def test_high_impact_ics_endpoint() -> None:
    response = client.get("/high-impact.ics")
    assert response.status_code == 200
    assert "BEGIN:VCALENDAR" in response.text


def test_high_impact_json_endpoint() -> None:
    response = client.get("/high-impact.json")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
