import streamlit as st
from api_client import APIClient

st.set_page_config(
    page_title="JobShield - Verification Platform",
    page_icon="🛡️",
    layout="wide"
)

# Initialize Session State
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

st.title("🛡️ JobShield — Job & Company Verification Platform")
st.markdown("##### *Evidence-Based Job Scam & Recruiter Fraud Risk Assessment*")
st.divider()

if not st.session_state.token:
    tab1, tab2 = st.tabs(["🔒 Login", "📝 Register"])

    with tab1:
        st.subheader("Login to JobShield")
        with st.form("login_form"):
            email = st.text_input("Email Address", value="user@example.com")
            password = st.text_input("Password", type="password", value="StrongPassword123")
            submit = st.form_submit_button("Sign In")

            if submit:
                res = APIClient.login(email, password)
                if res["status_code"] == 200:
                    st.session_state.token = res["data"]["access_token"]
                    user_res = APIClient.get_me(st.session_state.token)
                    if user_res["status_code"] == 200:
                        st.session_state.user = user_res["data"]
                        st.success(f"Welcome back, {st.session_state.user['name']}!")
                        st.rerun()
                else:
                    err_msg = res.get("data", {}).get("error", {}).get("message", "Invalid credentials")
                    st.error(f"Login failed: {err_msg}")

    with tab2:
        st.subheader("Create a New Account")
        with st.form("register_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_pass = st.text_input("Password (min 8 characters)", type="password")
            register_submit = st.form_submit_button("Register Account")

            if register_submit:
                res = APIClient.register(new_name, new_email, new_pass)
                if res["status_code"] == 201:
                    st.success("Registration successful! Please sign in using the Login tab.")
                else:
                    err_msg = res.get("data", {}).get("error", {}).get("message", "Registration failed")
                    st.error(f"Error: {err_msg}")
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.success(f"Logged in as: **{st.session_state.user.get('name', 'User')}** ({st.session_state.user.get('email')})")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    st.markdown("""
    ---
    ### 📌 Navigation
    Use the sidebar menu to navigate across platform features:
    - **Dashboard & Verification History**: View past analysis reports.
    - **Verify Job Listing**: Scrape job URLs and evaluate risk signals.
    - **Verify Recruiter Email**: Check job offer emails, payment requests, and domain mismatches.
    - **Reports**: Submit and track scam reports.
    - **Job Posting Analytics**: Fake-posting statistics and rule-engine performance on a labelled dataset.
    - **Report Suspicious Offers**: Submit community reports for unverified recruiters or fraudulent offers.
    """)
