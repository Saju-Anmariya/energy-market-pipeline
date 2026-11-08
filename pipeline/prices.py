from datetime import date, datetime, timezone

import requests

BASE_URL = "https://api.energy-charts.info"


def fetch_day_ahead_prices(start: date, end: date, bzn: str = "DE-LU", session=requests):
    """Returns a list of dicts: {'timestamp': UTC datetime, 'price_eur_mwh': float}."""
    response = session.get(
        f"{BASE_URL}/price",
        params={"bzn": bzn, "start": start.isoformat(), "end": end.isoformat()},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    rows = []
    for seconds, price in zip(data["unix_seconds"], data["price"]):
        if price is None:
            continue
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(seconds, tz=timezone.utc),
                "price_eur_mwh": float(price),
            }
        )
    return rows