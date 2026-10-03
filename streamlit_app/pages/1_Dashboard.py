import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Dashboard - JobShield", page_icon="📊", layout="wide")

st.title("📊 Verification History & Dashboard")

if not st.session_state.get("token"):
    st.warning("Please sign in from the main app page to view your verification history.")
    st.stop()

token = st.session_state.token
res = APIClient.get_verification_history(token)

if res["status_code"] == 200:
    history = res["data"]
    if not history:
        st.info("No verifications performed yet. Use the sidebar to verify a Job or Email offer!")
    else:
        st.metric(label="Total Verifications Performed", value=len(history))
        st.divider()

        for item in history:
            risk_color = "green" if item['risk_level'] == "LOW" else "orange" if item['risk_level'] == "MODERATE" else "red"
            
            with st.expander(f"[{item['verification_type'].upper()}] - Risk: :{risk_color}[{item['risk_level']} ({item['risk_score']}/100)] | {item['created_at'][:10]}"):
                st.write(f"**Verification Status:** {item['verification_status']}")
                st.write(f"**Summary:** {item.get('summary')}")
                
                if item.get("signals"):
                    st.markdown("##### Detected Signals:")
                    for sig in item["signals"]:
                        st.write(f"- ⚠️ **{sig['title']}** (Severity: `{sig['severity']}`, Impact: `+{sig['score_impact']}`) — {sig['description']}")
else:
    st.error("Failed to load verification history from backend API.")
