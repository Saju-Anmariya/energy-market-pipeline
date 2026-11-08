from datetime import date, datetime, timezone

import requests

BASE_URL = "https://api.energy-charts.info"

# name in the API -> column name in our data
SERIES = {
    "Solar": "solar_mw",
    "Wind onshore": "wind_onshore_mw",
    "Wind offshore": "wind_offshore_mw",
    "Load": "load_mw",
    "Renewable share of load": "renewable_share_pct",
}


def fetch_generation(start: date, end: date, country: str = "de", session=requests):
    """Returns a list of dicts with a UTC timestamp and one value per series in SERIES."""
    response = session.get(
        f"{BASE_URL}/public_power",
        params={"country": country, "start": start.isoformat(), "end": end.isoformat()},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    by_name = {item["name"]: item["data"] for item in data["production_types"]}
    rows = []
    for i, seconds in enumerate(data["unix_seconds"]):
        row = {"timestamp": datetime.fromtimestamp(seconds, tz=timezone.utc)}
        for api_name, column in SERIES.items():
            values = by_name.get(api_name)
            value = values[i] if values is not None and i < len(values) else None
            row[column] = float(value) if value is not None else None
        rows.append(row)
    return rows