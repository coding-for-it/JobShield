"""
Which scam keywords fire on which postings, and how many of those postings are really fake?

    python -m etl.keyword_audit                         (uses data/fake_job_postings.csv)
    python -m etl.keyword_audit --csv path/to/file.csv

Reads the CSV directly (no database needed). Use it to see WHY a rule is noisy:
the example column shows the text around the first match.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from app.verification.email_analyzer import EmailAnalyzer
from app.verification.posting_analyzer import PostingAnalyzer
from etl.clean import clean_postings
from etl.load_postings import read_csv

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "fake_job_postings.csv"
KEYWORD_GROUPS = {
    "payment": EmailAnalyzer.PAYMENT_KEYWORDS,
    "urgency": EmailAnalyzer.URGENCY_KEYWORDS,
    "no_interview": EmailAnalyzer.NO_INTERVIEW_KEYWORDS,
    "link": EmailAnalyzer.SUSPICIOUS_LINK_PATTERNS,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit scam keywords against a labelled posting file.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = parser.parse_args()
    if not args.csv.exists():
        print(f"File not found: {args.csv}")
        return 1

    df, _ = clean_postings(read_csv(args.csv))
    hits, fake_hits, example = Counter(), Counter(), {}
    for record in df.to_dict("records"):
        text = PostingAnalyzer.build_text(record)
        for group, keywords in KEYWORD_GROUPS.items():
            for kw in keywords:
                position = text.find(kw)
                if position >= 0:
                    hits[(group, kw)] += 1
                    fake_hits[(group, kw)] += int(record["fraudulent"])
                    example.setdefault((group, kw), text[max(0, position - 50):position + len(kw) + 30].replace("\n", " "))

    rows = [{"group": g, "keyword": k, "postings": n, "fake": fake_hits[(g, k)],
             "precision_pct": round(100 * fake_hits[(g, k)] / n, 1), "example": "..." + example[(g, k)] + "..."}
            for (g, k), n in hits.most_common()]
    if not rows:
        print("No keyword matched any posting.")
        return 0
    pd.set_option("display.max_colwidth", 95, "display.width", 250)
    print(pd.DataFrame(rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
