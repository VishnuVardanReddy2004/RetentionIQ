
import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.schema import DB_PATH


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = PROJECT_ROOT / "data" / "exports" / "csv"
JSON_DIR = PROJECT_ROOT / "data" / "exports" / "json"

TABLES = [
    "customers",
    "subscriptions",
    "usage_snapshots",
    "billing_events",
    "support_cases",
    "offers",
    "eligibility_rules",
    "campaign_contacts",
    "churn_outcomes",
    "retention_outcomes",
]


def export_data():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        for table in TABLES:
            df = pd.read_sql_query(
                f'SELECT * FROM "{table}"',
                connection,
            )

            csv_path = CSV_DIR / f"{table}.csv"
            json_path = JSON_DIR / f"{table}.json"

            df.to_csv(csv_path, index=False)

            records = json.loads(
                df.to_json(
                    orient="records",
                    date_format="iso",
                )
            )

            with json_path.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    records,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            print(
                f"{table}: {len(df):,} rows exported"
            )

    print("\nCSV and JSON exports completed.")


if __name__ == "__main__":
    export_data()
