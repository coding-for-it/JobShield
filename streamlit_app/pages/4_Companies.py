import streamlit as st
from api_client import APIClient

st.set_page_config(page_title="Companies Directory - JobShield", page_icon="🏢", layout="wide")

st.title("🏢 Verified Companies Directory")
st.write("Explore company domain records and verify official corporate websites.")

search_query = st.text_input("Search Company by Name or Domain", placeholder="e.g. techcorp.com")
res = APIClient.list_companies(page=1, limit=10, domain=search_query if search_query else None)

if res["status_code"] == 200:
    data = res["data"]
    companies = data.get("data", [])
    pagination = data.get("pagination", {})
    
    st.write(f"Showing **{len(companies)}** of **{pagination.get('total', 0)}** registered companies.")
    st.divider()

    for comp in companies:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(comp['name'])
                st.write(f"🌐 **Website:** [{comp.get('website')}]({comp.get('website')}) | **Domain:** `{comp.get('domain')}`")
                if comp.get('description'):
                    st.write(comp['description'])
            with col2:
                if comp.get('verified_domain'):
                    st.success("✅ Verified Domain")
                else:
                    st.warning("⚠️ Unverified Domain")
            st.divider()
else:
    st.error("Failed to load companies directory from backend.")
