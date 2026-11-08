from dataclasses import dataclass

import pandas as pd

EXPECTED_FREQUENCY = "15min"
PRICE_RANGE = (-500.0, 4000.0)  # EUR/MWh, a plausible range for day-ahead prices


@dataclass
class Issue:
    level: str  # "error" stops the pipeline, "warning" is only reported
    message: str


def check_dataset(df: pd.DataFrame) -> list:
    if df.empty:
        return [Issue("error", "No rows were fetched")]

    issues = []

    duplicates = int(df["timestamp"].duplicated().sum())
    if duplicates:
        issues.append(Issue("error", f"{duplicates} duplicate timestamps"))

    expected = pd.date_range(df["timestamp"].min(), df["timestamp"].max(), freq=EXPECTED_FREQUENCY)
    missing = expected.difference(pd.DatetimeIndex(df["timestamp"]))
    if len(missing) > 0:
        issues.append(Issue("error", f"{len(missing)} missing {EXPECTED_FREQUENCY} intervals"))

    for column in df.columns.drop("timestamp"):
        empty = int(df[column].isna().sum())
        if empty:
            issues.append(Issue("warning", f"{column}: {empty} missing values"))

    low, high = PRICE_RANGE
    bad_prices = int(((df["price_eur_mwh"] < low) | (df["price_eur_mwh"] > high)).sum())
    if bad_prices:
        issues.append(Issue("warning", f"price_eur_mwh: {bad_prices} values outside {low} to {high} EUR/MWh"))

    for column in ["solar_mw", "wind_onshore_mw", "wind_offshore_mw", "load_mw"]:
        negative = int((df[column] < 0).sum())
        if negative:
            issues.append(Issue("warning", f"{column}: {negative} negative values"))

    bad_share = int(((df["renewable_share_pct"] < 0) | (df["renewable_share_pct"] > 100)).sum())
    if bad_share:
        issues.append(Issue("warning", f"renewable_share_pct: {bad_share} values outside 0 to 100"))

    return issues


def has_errors(issues) -> bool:
    return any(issue.level == "error" for issue in issues)