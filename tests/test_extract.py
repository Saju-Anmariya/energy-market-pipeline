from datetime import date

from pipeline.generation import fetch_generation
from pipeline.prices import fetch_day_ahead_prices


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return FakeResponse(self.payload)


def test_prices_are_parsed_and_missing_values_skipped():
    payload = {"unix_seconds": [1793833200, 1793834100, 1793835000], "price": [202.6, None, 194.18]}
    session = FakeSession(payload)
    rows = fetch_day_ahead_prices(date(2026, 11, 5), date(2026, 11, 7), session=session)
    assert [row["price_eur_mwh"] for row in rows] == [202.6, 194.18]
    assert rows[0]["timestamp"].tzinfo is not None
    url, params = session.calls[0]
    assert url.endswith("/price")
    assert params["bzn"] == "DE-LU"
    assert params["start"] == "2026-11-05"


def test_generation_is_parsed_into_columns():
    payload = {
        "unix_seconds": [1793833200, 1793834100],
        "production_types": [
            {"name": "Solar", "data": [0.0, 12.5]},
            {"name": "Wind onshore", "data": [100.0, None]},
            {"name": "Load", "data": [50000.0, 50100.0]},
        ],
    }
    rows = fetch_generation(date(2026, 11, 5), date(2026, 11, 7), session=FakeSession(payload))
    assert len(rows) == 2
    assert rows[1]["solar_mw"] == 12.5
    assert rows[1]["wind_onshore_mw"] is None
    assert rows[0]["wind_offshore_mw"] is None
    assert rows[0]["load_mw"] == 50000.0