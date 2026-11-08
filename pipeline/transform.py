import pandas as pd

from .generation import SERIES


def build_dataset(prices, generation) -> pd.DataFrame:
    """Merges prices and generation into one table with one row per timestamp."""
    prices_df = pd.DataFrame(prices, columns=["timestamp", "price_eur_mwh"])
    generation_df = pd.DataFrame(generation, columns=["timestamp", *SERIES.values()])
    for frame in (prices_df, generation_df):
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    merged = prices_df.merge(generation_df, on="timestamp", how="outer")
    return merged.sort_values("timestamp").reset_index(drop=True)