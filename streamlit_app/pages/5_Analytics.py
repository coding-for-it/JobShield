import pandas as pd
import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Analytics - JobShield", page_icon="📈", layout="wide")

st.title("📈 Job Posting Analytics")
st.write("How common are fake job postings, what do they look like, and how well does the rule engine catch them?")

if not st.session_state.get("token"):
    st.warning("Please sign in from the main app page to view analytics.")
    st.stop()

token = st.session_state.token

threshold = st.sidebar.slider(
    "Flag a posting when its risk score is at least", min_value=0, max_value=100, value=25, step=5,
    help="Lower = flags more postings (catches more scams, more false alarms). Higher = the opposite.",
)

res = APIClient.analytics_summary(token, threshold)
if res["status_code"] != 200:
    st.error(f"Could not load analytics: {res['data'].get('error', {}).get('message', 'unknown error')}")
    st.stop()
summary = res["data"]

if summary["total_postings"] == 0:
    st.info("No job postings loaded yet. In a terminal, run:  `python -m etl.load_postings`  "
            "(small sample)  or  `python -m etl.load_postings --csv data/fake_job_postings.csv`  (real dataset).")
    st.stop()

if any("synthetic" in name.lower() for name in summary["datasets"]):
    st.warning("⚠️ This is the SYNTHETIC sample dataset (invented data). The numbers below only prove the "
               "pipeline works. They say nothing about real job scams. Load the real dataset for real findings.")

st.caption("Dataset: " + ", ".join(summary["datasets"]))


def fmt(value):
    return "n/a" if value is None else f"{value}%"


# ---------- 1. overview ----------
st.subheader("1. Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Postings", f"{summary['total_postings']:,}")
c2.metric("Fake postings", f"{summary['fraud_postings']:,}", fmt(summary["fraud_rate_pct"]), delta_color="off")
c3.metric("Precision", fmt(summary["precision_pct"]), help="Of the postings I flagged, how many were really fake?")
c4.metric("Recall", fmt(summary["recall_pct"]), help="Of all the fake postings, how many did I catch?")

cm = summary["confusion_matrix"]
left, right = st.columns([1, 2])
with left:
    st.dataframe(
        pd.DataFrame(
            {"Really fake": [cm["true_positives"], cm["false_negatives"]],
             "Really real": [cm["false_positives"], cm["true_negatives"]]},
            index=["Flagged", "Not flagged"],
        )
    )
with right:
    st.write(
        f"**Accuracy is misleading here.** Saying 'everything is real' would be right "
        f"{fmt(summary['always_real_accuracy_pct'])} of the time, because fake postings are rare. "
        f"The rule engine's accuracy is {fmt(summary['accuracy_pct'])}. That is why precision and recall are the "
        f"numbers to look at."
    )

st.divider()

# ---------- 2. fraud rate by category ----------
st.subheader("2. Where are fake postings concentrated?")
col_a, col_b = st.columns(2)
dimension = col_a.selectbox(
    "Group postings by",
    ["employment_type", "industry", "required_experience", "required_education", "job_function", "country"],
)
min_postings = col_b.slider("Ignore groups with fewer postings than", 1, 200, 30,
                            help="Small groups give unreliable percentages.")
res = APIClient.analytics_fraud_by(token, dimension, min_postings)
if res["status_code"] == 200 and res["data"]:
    df = pd.DataFrame(res["data"])
    st.bar_chart(df.set_index("category")["fraud_pct"])
    st.dataframe(df, hide_index=True)
else:
    st.info("No group has that many postings. Lower the minimum.")

st.divider()

# ---------- 3. features ----------
st.subheader("3. Do missing details predict fake postings?")
res = APIClient.analytics_features(token)
if res["status_code"] == 200 and res["data"]:
    feats = pd.DataFrame(res["data"])
    pivot = feats.pivot(index="feature", columns="feature_value", values="fraud_pct")
    pivot.columns = ["% fake when feature = 0 (absent)", "% fake when feature = 1 (present)"]
    st.bar_chart(pivot)
    st.dataframe(pivot)
    st.caption("Large gaps between the two columns mean the feature separates fake from real postings.")

st.divider()

# ---------- 4. rule performance ----------
st.subheader("4. Which rules work, and which are noisy?")
res = APIClient.analytics_rule_performance(token)
if res["status_code"] == 200 and res["data"]:
    rules = pd.DataFrame(res["data"])
    st.dataframe(rules, hide_index=True)
    st.caption("precision: of postings where the rule fired, % that were fake. "
               "coverage: of all fake postings, % the rule fired on. "
               "lift: precision divided by the overall fake rate (above 1 beats guessing).")
else:
    st.info("No rule has fired yet.")

st.divider()

# ---------- 5. threshold trade-off ----------
st.subheader("5. The precision / recall trade-off")
res = APIClient.analytics_threshold_sweep(token)
if res["status_code"] == 200 and res["data"]:
    sweep = pd.DataFrame(res["data"])
    st.line_chart(sweep.set_index("threshold")[["precision_pct", "recall_pct"]])
    st.dataframe(sweep, hide_index=True)
    st.caption("Moving the threshold up reduces false alarms but misses more scams. Pick it based on which mistake costs more.")
