"""
Creates data/sample_job_postings_SYNTHETIC.csv

!!  THIS DATA IS INVENTED.  !!
It exists only so you can run and test the whole pipeline (load -> SQL -> API -> dashboard)
before you download the real dataset. The "fake" postings follow patterns I made up,
so any number computed from this file says NOTHING about real job scams.
Never quote results from this file as findings.

    python -m etl.make_sample_data
"""
import random
from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_job_postings_SYNTHETIC.csv"
N_ROWS = 800
FRAUD_SHARE = 0.08
SEED = 42

COLUMNS = [
    "job_id", "title", "location", "department", "salary_range", "company_profile",
    "description", "requirements", "benefits", "telecommuting", "has_company_logo",
    "has_questions", "employment_type", "required_experience", "required_education",
    "industry", "function", "fraudulent",
]
TITLES = ["Software Engineer", "Data Analyst", "Customer Support Agent", "Marketing Executive",
          "Sales Associate", "Accountant", "Project Manager", "Content Writer", "HR Coordinator",
          "Data Entry Clerk", "Delivery Associate", "Graphic Designer"]
LOCATIONS = ["US, NY, New York", "US, CA, San Francisco", "GB, LND, London", "IN, MH, Pune",
             "CA, ON, Toronto", "AU, NSW, Sydney", "US, TX, Austin", "DE, BE, Berlin"]
EMPLOYMENT = ["Full-time", "Part-time", "Contract", "Temporary", "Other"]
EXPERIENCE = ["Entry level", "Mid-Senior level", "Associate", "Not Applicable", "Director"]
EDUCATION = ["Bachelor's Degree", "High School or equivalent", "Master's Degree", "Unspecified"]
INDUSTRIES = ["Information Technology and Services", "Marketing and Advertising", "Retail",
              "Accounting", "Financial Services", "Education Management", "Hospital & Health Care"]
FUNCTIONS = ["Engineering", "Sales", "Marketing", "Administrative", "Customer Service", "Finance"]
LEGIT_TEXT = [
    "You will work with the team to build and improve our internal reporting tools.",
    "Responsibilities include planning projects, writing clear documentation and supporting clients.",
    "We are looking for a motivated person to join our growing department.",
    "The role involves daily coordination with other teams and regular progress reports.",
]
SCAM_TEXT = [
    "Work from home and earn money fast. Limited seats available.",
    "No experience needed. Start immediately and get paid weekly.",
    "Apply today, we are hiring many people for this easy position.",
]
SCAM_EXTRAS = [
    "A registration fee is required before your first day.",
    "You must pay a training fee to receive your materials.",
    "A refundable deposit is needed for your laptop.",
    "Contact our recruiter on t.me/hiring_desk to begin.",
    "Offer expires in 24 hours so reply now.",
    "Candidates are selected without interview.",
]


def _maybe(rng: random.Random, probability: float, value):
    return value if rng.random() < probability else ""


def make_row(rng: random.Random, job_id: int, fraud: bool) -> dict:
    p = (lambda legit, fake: fake if fraud else legit)  # pick the probability for this class
    description = rng.choice(SCAM_TEXT if fraud else LEGIT_TEXT) + f" Posting reference {job_id}."
    if fraud:
        for extra, chance in zip(SCAM_EXTRAS, [0.20, 0.08, 0.06, 0.08, 0.12, 0.10]):
            if rng.random() < chance:
                description += " " + extra
    low = rng.choice([20000, 30000, 45000, 60000])
    salary = rng.choice([f"{low}-{low + 15000}", "0-0", "Dec-20", ""]) if rng.random() < p(0.30, 0.12) else ""
    return {
        "job_id": job_id,
        "title": rng.choice(TITLES),
        "location": rng.choice(LOCATIONS) if rng.random() < 0.97 else "",
        "department": _maybe(rng, 0.35, rng.choice(["Operations", "Product", "Support"])),
        "salary_range": salary,
        "company_profile": _maybe(rng, p(0.90, 0.40), "We are an established company with offices in several countries."),
        "description": description,
        "requirements": _maybe(rng, p(0.90, 0.50), "Good communication skills and basic computer knowledge."),
        "benefits": _maybe(rng, p(0.60, 0.30), "Flexible hours and paid leave."),
        "telecommuting": int(rng.random() < p(0.05, 0.25)),
        "has_company_logo": int(rng.random() < p(0.85, 0.20)),
        "has_questions": int(rng.random() < p(0.55, 0.25)),
        "employment_type": _maybe(rng, 0.85, rng.choice(EMPLOYMENT)),
        "required_experience": _maybe(rng, 0.65, rng.choice(EXPERIENCE)),
        "required_education": _maybe(rng, 0.55, rng.choice(EDUCATION)),
        "industry": _maybe(rng, 0.75, rng.choice(INDUSTRIES)),
        "function": _maybe(rng, 0.65, rng.choice(FUNCTIONS)),
        "fraudulent": int(fraud),
    }


def main() -> None:
    rng = random.Random(SEED)
    rows = [make_row(rng, i, rng.random() < FRAUD_SHARE) for i in range(1, N_ROWS + 1)]
    # add a few exact duplicates (new job_id) so the cleaning step has something to remove
    for k in range(10):
        dup = dict(rows[k])
        dup["job_id"] = N_ROWS + 1 + k
        rows.append(dup)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(OUTPUT, index=False)
    fraud = sum(r["fraudulent"] for r in rows)
    print(f"Wrote {OUTPUT}  ({len(rows)} rows, {fraud} labelled fake). SYNTHETIC - not real data.")


if __name__ == "__main__":
    main()
