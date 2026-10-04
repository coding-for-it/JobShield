import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Verify Job - JobShield", page_icon="🔗", layout="wide")

st.title("🔗 Verify Job Posting URL")
st.write("Analyze job listings, detect suspicious subdomains, IP hostnames, and scrape web text for hidden fee demands.")

if not st.session_state.get("token"):
    st.warning("Please sign in from the main app page to perform job verification.")
    st.stop()

token = st.session_state.token

with st.form("verify_job_form"):
    job_url = st.text_input("Job Posting URL", placeholder="https://techcorp.com/careers/backend-developer")
    company_name = st.text_input("Company Name (Optional)", placeholder="TechCorp Solutions")
    submit = st.form_submit_button("🔍 Run Job Verification")

if submit:
    if not job_url:
        st.error("Please enter a valid job URL.")
    else:
        with st.spinner("Analyzing web domain, SSL encryption, and scraping job description..."):
            res = APIClient.verify_job(token, job_url, company_name)
            
        if res["status_code"] == 200:
            data = res["data"]
            st.success("Verification Completed!")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Score", f"{data['risk_score']} / 100")
            col2.metric("Risk Level", data["risk_level"])
            col3.metric("Verification Status", data["verification_status"])
            
            st.markdown("### 📋 Executive Summary")
            st.info(data.get("summary", "No summary generated."))

            if data.get("signals"):
                st.markdown("### 🚨 Detected Signals & Evidence")
                for sig in data["signals"]:
                    st.warning(f"**{sig['title']}** (Impact: +{sig['score_impact']})\n\n{sig['description']}\n\n*Evidence:* `{sig.get('evidence')}`")

            if data.get("recommended_actions"):
                st.markdown("### 💡 Recommended Actions")
                for action in data["recommended_actions"]:
                    st.write(f"👉 {action}")
        else:
            err = res.get("data", {}).get("error", {}).get("message", "API Error")
            st.error(f"Verification Failed: {err}")
