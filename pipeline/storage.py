import sqlite3
from pathlib import Path

import pandas as pd

VALUE_COLUMNS = [
    "price_eur_mwh",
    "solar_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "load_mw",
    "renewable_share_pct",
]


def connect(path: str = "data/market.db") -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    columns = ", ".join(f"{column} REAL" for column in VALUE_COLUMNS)
    conn.execute(f"CREATE TABLE IF NOT EXISTS market_data (timestamp TEXT PRIMARY KEY, {columns})")
    return conn


def upsert(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Inserts new rows and updates existing ones, so running twice never creates duplicates."""
    records = []
    for row in df.itertuples(index=False):
        values = [None if pd.isna(getattr(row, c)) else float(getattr(row, c)) for c in VALUE_COLUMNS]
        records.append((row.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), *values))

    names = ", ".join(["timestamp", *VALUE_COLUMNS])
    marks = ", ".join("?" for _ in range(len(VALUE_COLUMNS) + 1))
    updates = ", ".join(f"{c} = excluded.{c}" for c in VALUE_COLUMNS)
    conn.executemany(
        f"INSERT INTO market_data ({names}) VALUES ({marks}) "
        f"ON CONFLICT(timestamp) DO UPDATE SET {updates}",
        records,
    )
    conn.commit()
    return len(records)


def count_rows(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]

def export_csv(conn: sqlite3.Connection, path: str) -> None:
    df = pd.read_sql_query("SELECT * FROM market_data ORDER BY timestamp", conn)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def import_csv(conn: sqlite3.Connection, path: str) -> int:
    """Loads earlier results from a CSV file, if it exists."""
    if not Path(path).exists():
        return 0
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return upsert(conn, df)