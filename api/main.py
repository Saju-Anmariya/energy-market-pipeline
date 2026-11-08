from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, Query

CSV_PATH = Path("data/market.csv")

app = FastAPI(title="Energy Market API", version="0.1.0")


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def load_data(path: Path = CSV_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def get_data() -> pd.DataFrame:
    return load_data()


def to_utc(value: datetime) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def number(value) -> Optional[float]:
    return None if pd.isna(value) else round(float(value), 2)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data")
def list_rows(
    limit: int = Query(96, ge=1, le=1000),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    df: pd.DataFrame = Depends(get_data),
):
    if df.empty:
        return []
    if start is not None:
        df = df[df["timestamp"] >= to_utc(start)]
    if end is not None:
        df = df[df["timestamp"] <= to_utc(end)]
    rows = df.sort_values("timestamp", ascending=False).head(limit).copy()
    rows["timestamp"] = rows["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = rows.astype(object).where(rows.notna(), None)
    return rows.to_dict(orient="records")


@app.get("/summary")
def summary(df: pd.DataFrame = Depends(get_data)):
    if df.empty:
        return {"rows": 0}
    return {
        "rows": int(len(df)),
        "first_timestamp": df["timestamp"].min().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_timestamp": df["timestamp"].max().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_eur_mwh": {
            "mean": number(df["price_eur_mwh"].mean()),
            "min": number(df["price_eur_mwh"].min()),
            "max": number(df["price_eur_mwh"].max()),
        },
        "renewable_share_pct_mean": number(df["renewable_share_pct"].mean()),
    }