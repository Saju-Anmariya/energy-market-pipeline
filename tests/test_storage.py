import pandas as pd
from pipeline.storage import connect, count_rows, export_csv, import_csv, upsert



def make_df():
    times = pd.date_range("2026-11-05", periods=4, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": times,
            "price_eur_mwh": [100.0, 101.0, 102.0, 103.0],
            "solar_mw": [0.0] * 4,
            "wind_onshore_mw": [2000.0] * 4,
            "wind_offshore_mw": [500.0] * 4,
            "load_mw": [50000.0] * 4,
            "renewable_share_pct": [40.0] * 4,
        }
    )


def test_upsert_inserts_rows():
    conn = connect(":memory:")
    assert upsert(conn, make_df()) == 4
    assert count_rows(conn) == 4


def test_running_twice_does_not_create_duplicates():
    conn = connect(":memory:")
    upsert(conn, make_df())
    upsert(conn, make_df())
    assert count_rows(conn) == 4


def test_changed_values_are_updated():
    conn = connect(":memory:")
    upsert(conn, make_df())
    changed = make_df()
    changed.loc[0, "price_eur_mwh"] = 555.0
    upsert(conn, changed)
    price = conn.execute("SELECT price_eur_mwh FROM market_data ORDER BY timestamp LIMIT 1").fetchone()[0]
    assert price == 555.0
    assert count_rows(conn) == 4


def test_missing_values_are_stored_as_null():
    conn = connect(":memory:")
    df = make_df()
    df.loc[1, "solar_mw"] = None
    upsert(conn, df)
    nulls = conn.execute("SELECT COUNT(*) FROM market_data WHERE solar_mw IS NULL").fetchone()[0]
    assert nulls == 1


def test_csv_export_and_import_roundtrip(tmp_path):
    conn = connect(":memory:")
    upsert(conn, make_df())
    csv_file = tmp_path / "market.csv"
    export_csv(conn, str(csv_file))

    other = connect(":memory:")
    assert import_csv(other, str(csv_file)) == 4
    assert count_rows(other) == 4