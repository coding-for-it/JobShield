"""
Run every query in sql/analysis/, print the result, and save it as a CSV.

    python -m etl.run_analysis            (all queries)
    python -m etl.run_analysis 06         (only files whose name contains "06")

CSV files go to analysis_output/ - use them for charts and for docs/findings.md.
"""
import sys
from pathlib import Path

import pandas as pd

from app.database import get_connection

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "sql" / "analysis"
OUTPUT_DIR = ROOT / "analysis_output"


def main() -> int:
    name_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(f for f in ANALYSIS_DIR.glob("*.sql") if name_filter in f.name)
    if not files:
        print(f"No analysis files found in {ANALYSIS_DIR} matching '{name_filter}'")
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = get_connection()
    try:
        for path in files:
            with conn.cursor() as cur:
                cur.execute(path.read_text())
                rows = cur.fetchall()
            df = pd.DataFrame(rows)
            df.to_csv(OUTPUT_DIR / f"{path.stem}.csv", index=False)
            print(f"\n=== {path.name} ===")
            print(df.to_string(index=False) if not df.empty else "(no rows - is a dataset loaded?)")
    finally:
        conn.close()
    print(f"\nSaved CSV files to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
