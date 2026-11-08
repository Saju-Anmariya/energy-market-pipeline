import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app, get_data


def make_df():
    times = pd.date_range("2026-11-05", periods=4, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": times,
            "price_eur_mwh": [100.0, 110.0, 120.0, 130.0],
            "solar_mw": [0.0, 10.0, 20.0, None],
            "wind_onshore_mw": [2000.0] * 4,
            "wind_offshore_mw": [500.0] * 4,
            "load_mw": [50000.0] * 4,
            "renewable_share_pct": [40.0, 42.0, 44.0, 46.0],
        }
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_data] = make_df
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_data_returns_latest_rows_first(client):
    response = client.get("/data?limit=2")
    rows = response.json()
    assert response.status_code == 200
    assert len(rows) == 2
    assert rows[0]["timestamp"] == "2026-11-05T00:45:00Z"


def test_missing_values_are_returned_as_null(client):
    row = client.get("/data?limit=1").json()[0]
    assert row["solar_mw"] is None


def test_start_filter(client):
    rows = client.get("/data?start=2026-11-05T00:30:00").json()
    assert len(rows) == 2


def test_invalid_limit_is_rejected(client):
    assert client.get("/data?limit=0").status_code == 422
    assert client.get("/data?limit=5000").status_code == 422


def test_invalid_date_is_rejected(client):
    assert client.get("/data?start=not-a-date").status_code == 422


def test_summary(client):
    body = client.get("/summary").json()
    assert body["rows"] == 4
    assert body["price_eur_mwh"] == {"mean": 115.0, "min": 100.0, "max": 130.0}
    assert body["renewable_share_pct_mean"] == 43.0


def test_empty_data():
    app.dependency_overrides[get_data] = lambda: pd.DataFrame()
    try:
        client = TestClient(app)
        assert client.get("/data").json() == []
        assert client.get("/summary").json() == {"rows": 0}
    finally:
        app.dependency_overrides.clear()


def test_security_headers_are_set(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"