import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Report Suspicious Job - JobShield", page_icon="🚩", layout="wide")

st.title("🚩 Report Suspicious Job or Recruiter")
st.write("Help protect the job seeker community by submitting reports on fraudulent offers, fake interviews, or fee demands.")

if not st.session_state.get("token"):
    st.warning("Please sign in from the main app page to submit community reports.")
    st.stop()

token = st.session_state.token

tab1, tab2 = st.tabs(["📝 Submit New Report", "📂 My Submitted Reports"])

with tab1:
    with st.form("create_report_form"):
        report_type = st.selectbox(
            "Report Category",
            options=["PAYMENT_REQUEST", "FAKE_INTERVIEW", "SUSPICIOUS_RECRUITER", "FAKE_OFFER", "MISLEADING_JOB", "OTHER"]
        )
        description = st.text_area(
            "Detailed Description of Incident",
            height=150,
            placeholder="Explain what happened (e.g. Recruiter asked for $50 via Zelle before scheduling technical interview)."
        )
        submit = st.form_submit_button("Submit Report")

        if submit:
            if not description or len(description) < 10:
                st.error("Please provide a detailed description (at least 10 characters).")
            else:
                payload = {
                    "report_type": report_type,
                    "description": description
                }
                res = APIClient.create_report(token, payload)
                if res["status_code"] == 201:
                    st.success("Report submitted successfully! Status set to PENDING for moderation review.")
                else:
                    err = res.get("data", {}).get("error", {}).get("message", "Failed to submit report")
                    st.error(f"Error: {err}")

with tab2:
    reports_res = APIClient.list_reports(token)
    if reports_res["status_code"] == 200:
        reports = reports_res["data"]
        if not reports:
            st.info("You haven't submitted any reports yet.")
        else:
            for rep in reports:
                status_color = "orange" if rep['status'] == "PENDING" else "green"
                with st.expander(f"Report #{rep['id']} - [{rep['report_type']}] | Status: :{status_color}[{rep['status']}]"):
                    st.write(f"**Submitted Date:** {rep['created_at'][:10]}")
                    st.write(f"**Details:** {rep['description']}")
    else:
        st.error("Failed to load user reports.")
