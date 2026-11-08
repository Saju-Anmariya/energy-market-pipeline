import pandas as pd

from pipeline.generation import SERIES
from pipeline.quality import check_dataset, has_errors
from pipeline.transform import build_dataset


def make_dataset(periods=8):
    times = pd.date_range("2026-11-05", periods=periods, freq="15min", tz="UTC")
    prices = [
        {"timestamp": t.to_pydatetime(), "price_eur_mwh": 100.0 + i} for i, t in enumerate(times)
    ]
    generation = [
        {
            "timestamp": t.to_pydatetime(),
            "solar_mw": 1000.0,
            "wind_onshore_mw": 2000.0,
            "wind_offshore_mw": 500.0,
            "load_mw": 50000.0,
            "renewable_share_pct": 40.0,
        }
        for t in times
    ]
    return prices, generation


def test_merge_has_all_columns():
    df = build_dataset(*make_dataset())
    assert set(df.columns) == {"timestamp", "price_eur_mwh", *SERIES.values()}
    assert len(df) == 8


def test_good_data_has_no_issues():
    df = build_dataset(*make_dataset())
    assert check_dataset(df) == []


def test_empty_dataset_is_an_error():
    df = build_dataset([], [])
    assert has_errors(check_dataset(df))


def test_duplicate_timestamps_are_errors():
    df = build_dataset(*make_dataset())
    df = pd.concat([df, df.iloc[[0]]])
    assert has_errors(check_dataset(df))


def test_missing_interval_is_an_error():
    df = build_dataset(*make_dataset())
    df = df.drop(index=3)
    issues = check_dataset(df)
    assert has_errors(issues)
    assert any("missing" in issue.message for issue in issues)


def test_price_outside_range_is_only_a_warning():
    df = build_dataset(*make_dataset())
    df.loc[0, "price_eur_mwh"] = 99999.0
    issues = check_dataset(df)
    assert not has_errors(issues)
    assert any("price_eur_mwh" in issue.message for issue in issues)


def test_negative_solar_is_only_a_warning():
    df = build_dataset(*make_dataset())
    df.loc[2, "solar_mw"] = -5.0
    issues = check_dataset(df)
    assert not has_errors(issues)
    assert any("solar_mw" in issue.message for issue in issues)