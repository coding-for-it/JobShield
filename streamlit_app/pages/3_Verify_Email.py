import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Verify Email - JobShield", page_icon="✉️", layout="wide")

st.title("✉️ Verify Recruiter Email / Offer Message")
st.write("Detect domain mismatches, personal Gmail/Yahoo recruiters, payment requests (registration fees, deposits), and pressure tactics.")

if not st.session_state.get("token"):
    st.warning("Please sign in from the main app page to analyze emails.")
    st.stop()

token = st.session_state.token

with st.form("verify_email_form"):
    company_name = st.text_input("Company Name", value="TechCorp Solutions")
    company_website = st.text_input("Company Website (Optional)", value="https://techcorp.com")
    sender_name = st.text_input("Recruiter Name", value="HR Recruiting Team")
    sender_email = st.text_input("Recruiter Sender Email", value="hr-techcorp@gmail.com")
    subject = st.text_input("Email Subject Line", value="URGENT: Selection Notice for Data Analyst Position")
    body = st.text_area(
        "Email Body Text",
        height=180,
        value="Congratulations! You have been selected without interview. To reserve your laptop and onboarding materials, please submit a refundable registration fee of $100 via gift card."
    )
    submit = st.form_submit_button("🔍 Run Email Analysis")

if submit:
    if not sender_email or not body:
        st.error("Please provide both sender email and email body text.")
    else:
        payload = {
            "company_name": company_name,
            "company_website": company_website,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "body": body
        }
        with st.spinner("Analyzing email headers, domain alignment, and linguistic triggers."):
            res = APIClient.verify_email(token, payload)

        if res["status_code"] == 200:
            data = res["data"]
            st.success("Email Analysis Complete!")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Score", f"{data['risk_score']} / 100")
            col2.metric("Risk Level", data["risk_level"])
            col3.metric("Verification Status", data["verification_status"])

            st.markdown("### 📋 Verification Summary")
            st.info(data.get("summary"))

            if data.get("signals"):
                st.markdown("### 🚨 Detected Fraud Signals")
                for sig in data["signals"]:
                    st.error(f"**{sig['title']}** [Severity: `{sig['severity']}` | Impact: `+{sig['score_impact']}`]\n\n{sig['description']}\n\n*Evidence:* `{sig.get('evidence')}`")

            if data.get("recommended_actions"):
                st.markdown("### 💡 Recommended Next Steps")
                for action in data["recommended_actions"]:
                    st.write(f"👉 {action}")
        else:
            err = res.get("data", {}).get("error", {}).get("message", "API Error")
            st.error(f"Analysis Failed: {err}")
