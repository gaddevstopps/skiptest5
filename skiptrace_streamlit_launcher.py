
import streamlit as st
import pandas as pd
import requests
from difflib import get_close_matches

st.set_page_config(page_title="📦 Skiptrace Launcher")

st.title("📦 Clean Skiptrace Launcher")
st.write("Upload your CSV and run your own Apify actor for skip tracing (e.g. TruePeopleSearch).")

# Upload section
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# Helper to match column names
def fuzzy_find(possible_names, columns):
    for name in possible_names:
        match = get_close_matches(name.upper(), columns, n=1, cutoff=0.6)
        if match:
            return match[0]
    return None

def run_apify_actor(payload_list):
    token = st.secrets["apify"]["token"]
    actor_id = st.secrets["apify"]["actor_id"]  # Should be like: yourusername~your-cloned-actor
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={token}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "street_citystatezip": payload_list,
        "max_results": 1
    }

    with st.spinner("Sending to Apify..."):
        response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        run_url = response.json()["data"]["statusUrl"]
        st.success("Actor started successfully!")
        st.markdown(f"[🔍 View run on Apify]({run_url})")
    else:
        st.error("❌ Failed to trigger actor:")
        st.code(response.text)

# Main logic
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    columns = df.columns.str.upper().tolist()

    # Match required fields
    house = fuzzy_find(['MAIL HOUSE NUMBER', 'HOUSE NUMBER'], columns)
    street = fuzzy_find(['MAIL STREET NAME', 'STREET NAME'], columns)
    city = fuzzy_find(['MAIL CITY', 'CITY'], columns)
    state = fuzzy_find(['MAIL STATE', 'STATE'], columns)
    zipc = fuzzy_find(['MAIL ZIP/ZIP+4', 'ZIP'], columns)

    if not all([house, street, city, state, zipc]):
        st.error("Could not detect all required address fields. Please check your column headers.")
    else:
        df.columns = df.columns.str.upper()

        # Format into 'Street; City, State ZIP'
        addresses = (
            df[house].astype(str).str.strip() + ' ' +
            df[street].astype(str).str.strip() + '; ' +
            df[city].astype(str).str.strip() + ', ' +
            df[state].astype(str).str.strip() + ' ' +
            df[zipc].astype(str).str.strip()
        ).str.replace(r'\s+', ' ', regex=True).str.strip()

        st.write("📬 Preview of formatted inputs:")
        st.dataframe(addresses.head(10))

        if st.button("🚀 Run Skiptrace Actor"):
            run_apify_actor(addresses.tolist())
