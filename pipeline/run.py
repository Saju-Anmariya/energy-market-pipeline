import argparse
from datetime import date, timedelta

from .generation import fetch_generation
from .prices import fetch_day_ahead_prices
from .quality import check_dataset, has_errors
from .storage import connect, count_rows, export_csv, import_csv, upsert
from .transform import build_dataset


def run(days: int = 3, db_path: str = "data/market.db", csv_path: str = "data/market.csv") -> int:
    end = date.today()
    start = end - timedelta(days=days)

    prices = fetch_day_ahead_prices(start, end)
    generation = fetch_generation(start, end)
    df = build_dataset(prices, generation)

    issues = check_dataset(df)
    for issue in issues:
        print(f"[{issue.level.upper()}] {issue.message}")
    if has_errors(issues):
        print("Data quality errors found, nothing was written.")
        return 1

    conn = connect(db_path)
    try:
        import_csv(conn, csv_path)  # history from earlier runs
        written = upsert(conn, df)
        total = count_rows(conn)
        export_csv(conn, csv_path)
    finally:
        conn.close()

    print(f"Fetched {len(df)} rows ({start} to {end}), wrote {written}, history now holds {total} rows.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Fetch Energy-Charts data and store it")
    parser.add_argument("--days", type=int, default=3, help="how many past days to fetch")
    parser.add_argument("--db", default="data/market.db", help="path of the SQLite file")
    parser.add_argument("--csv", default="data/market.csv", help="path of the history CSV")
    args = parser.parse_args()
    raise SystemExit(run(args.days, args.db, args.csv))


if __name__ == "__main__":
    main()