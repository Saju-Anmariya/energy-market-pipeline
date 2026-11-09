# Energy Market Pipeline

![CI](https://github.com/Saju-Anmariya/energy-market-pipeline/actions/workflows/ci.yml/badge.svg)
![Daily data pipeline](https://github.com/Saju-Anmariya/energy-market-pipeline/actions/workflows/daily-run.yml/badge.svg)

An automated data pipeline for the German electricity market. Every day it downloads day-ahead electricity prices and solar and wind generation, checks the data quality, and adds the new data to a growing history in this repository.

## What it does

1. **Extract:** fetches day-ahead prices (DE-LU) and generation and load data (Germany) from the Energy-Charts API, in 15-minute steps
2. **Transform:** merges both sources into one table with one row per timestamp (all times in UTC)
3. **Check:** runs data quality checks and stops the pipeline on errors
4. **Load:** stores the data in SQLite with an upsert, so re-running never creates duplicates and corrected values overwrite old ones
5. **Automate:** a scheduled GitHub Actions workflow runs every day, publishes a report, and commits the updated history (`data/market.csv`)

## Data

| Column | Description |
|---|---|
| `timestamp` | Start of the 15-minute interval, UTC |
| `price_eur_mwh` | Day-ahead price in EUR/MWh |
| `solar_mw` | Solar generation in MW |
| `wind_onshore_mw` | Onshore wind generation in MW |
| `wind_offshore_mw` | Offshore wind generation in MW |
| `load_mw` | Electricity load in MW |
| `renewable_share_pct` | Renewable share of load in % |

Prices are published ahead of time, while generation and load exist only for intervals that have already happened. Newer rows therefore have empty generation values until a later run fills them in.

## Data quality checks

| Check | Result |
|---|---|
| Empty result | Error, nothing is stored |
| Duplicate timestamps | Error |
| Missing 15-minute intervals | Error |
| Missing values per column | Warning |
| Prices outside -500 to 4000 EUR/MWh | Warning |
| Negative generation or load | Warning |
| Renewable share outside 0 to 100 % | Warning |

## Tests and automation

- 14 automated tests (pytest). The API calls are replaced by fake responses, so the tests run without internet.
- `ci.yml` runs the tests and a dependency vulnerability scan (pip-audit) on every push.
- `daily-run.yml` runs the pipeline every day at 06:30 UTC and can also be started by hand. The report appears on the run summary page.

- `security-scan.yml` runs an OWASP ZAP scan of the API (started manually). Results and fixes: see [SECURITY.md](SECURITY.md).

## Run it locally

```bash
git clone https://github.com/Saju-Anmariya/energy-market-pipeline.git
cd energy-market-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pipeline.run --days 3
python -m pytest
```

## Project structure

```
pipeline/    extraction, transformation, quality checks, storage and runner
tests/       automated tests
data/        market.csv, the growing data history
.github/     GitHub Actions workflows
```

## Limitations

- Scheduled GitHub Actions workflows in public repositories are paused after about 60 days without repository activity
- Prices before October 2025 are hourly, so the 15-minute gap check is meant for recent data
- The history lives in a CSV file in the repository, which is fine for this size but not for large data

## Data source and license

Data from Energy-Charts.info (Fraunhofer ISE), licensed CC BY 4.0. The API names Bundesnetzagentur | SMARD.de as the original source of the data.