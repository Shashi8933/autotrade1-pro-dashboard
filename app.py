import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

def get_nse_equity_data():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive"
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        # Fetch cookies first
        session.get("https://www.nseindia.com", timeout=5)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['data'])
        return df
    except Exception as e:
        st.error(f"NSE Equity Data Error: {e}")
        return pd.DataFrame()

refresh_interval = 3  # seconds

st.title("NSE NIFTY 50 Live Data")

# Refresh every 3 seconds
st_autorefresh(interval=refresh_interval * 1000, key="autorefresh")

df = get_nse_equity_data()

if not df.empty:
    st.dataframe(df)
else:
    st.write("No data to display.")
