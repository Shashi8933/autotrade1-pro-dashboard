
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import time

# -----------------------------
# SETTINGS SIDEBAR
# -----------------------------
st.set_page_config(page_title="AutoTrade Pro Dashboard", layout="wide")
st.sidebar.title("⚙️ Settings")
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 3, 60, 3)  # Default now set to 3 seconds
selected_segment = st.sidebar.selectbox("Market Segment", ["Equity", "Futures", "Options", "Forex"])
option_symbol = st.sidebar.selectbox("Option Symbol", ["NIFTY", "BANKNIFTY"])

# -----------------------------
# HEADER & SEARCH
# -----------------------------
st.title("📊 AutoTrade Pro Dashboard")
st.markdown("Use this dashboard to monitor live Indian market data and identify Zero to Hero opportunities.")
search_query = st.text_input("🔍 Search Stock/Option:", "")

# -----------------------------
# FUNCTION TO GET NSE DATA
# -----------------------------
def get_nse_equity_data():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, timeout=10)
    data = response.json()
    df = pd.DataFrame(data['data'])
    return df

# -----------------------------
# FUNCTION TO GET OPTION DATA
# -----------------------------
def get_nse_option_chain(symbol="NIFTY"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, timeout=10)
    data = response.json()
    records = data['records']['data']
    df = pd.json_normalize(records, errors='ignore')
    return df, data['records']['strikePrices']

# -----------------------------
# FUNCTION TO GET FOREX DATA
# -----------------------------
def get_forex_data():
    url = "https://api.exchangerate.host/latest?base=USD&symbols=INR,EUR,JPY,GBP"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data['rates'], orient='index', columns=['Rate'])
    df.reset_index(inplace=True)
    df.columns = ['Currency', 'Rate']
    return df

# -----------------------------
# FUNCTION TO PLOT TREND
# -----------------------------
def plot_sample_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['symbol'], y=df['lastPrice'], name="Price"))
    fig.update_layout(title="Live Market Trend", xaxis_title="Symbol", yaxis_title="Price (INR)")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# FUNCTION TO PLOT MAX PAIN
# -----------------------------
def plot_max_pain_chart(df):
    if 'strikePrice' not in df.columns or 'CE.openInterest' not in df.columns or 'PE.openInterest' not in df.columns:
        return
    df['total_OI'] = df['CE.openInterest'].fillna(0) + df['PE.openInterest'].fillna(0)
    max_pain_strike = df.loc[df['total_OI'].idxmax(), 'strikePrice']
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['strikePrice'], y=df['total_OI'], name="Total OI"))
    fig.update_layout(title=f"Max Pain Point: {max_pain_strike}", xaxis_title="Strike Price", yaxis_title="Total OI")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# FUNCTION TO GET FAKE PNL
# -----------------------------
def show_fake_pnl_chart():
    data = {
        'Time': pd.date_range(end=pd.Timestamp.now(), periods=8, freq='h'),
        'PnL': [0, 100, 250, 300, 500, 450, 600, 800]
    }
    df = pd.DataFrame(data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Time'], y=df['PnL'], mode='lines+markers', name='PnL'))
    fig.update_layout(title='Cumulative PnL (Simulated)', xaxis_title='Time', yaxis_title='Profit & Loss')
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# FUNCTION TO DISPLAY OI SPIKES
# -----------------------------
def detect_oi_spikes(df):
    df = df[['strikePrice', 'CE.openInterest', 'PE.openInterest']].fillna(0)
    df['OI_Change'] = df['CE.openInterest'] + df['PE.openInterest']
    df = df.sort_values('OI_Change', ascending=False).head(10)
    st.subheader("📊 Top OI Spikes")
    st.dataframe(df)

# -----------------------------
# DISPLAY DATA BASED ON SELECTION
# -----------------------------
placeholder = st.empty()

while True:
    with placeholder.container():
        try:
            if selected_segment == "Equity":
                st.subheader("📈 Equity Market Overview")
                equity_df = get_nse_equity_data()
                if search_query:
                    equity_df = equity_df[equity_df['symbol'].str.contains(search_query.upper())]
                st.dataframe(equity_df[['symbol', 'lastPrice', 'change', 'pChange']])
                plot_sample_chart(equity_df)
                show_fake_pnl_chart()

            elif selected_segment == "Options":
                st.subheader(f"📉 Option Chain Screener (Zero to Hero) - {option_symbol}")
                option_df, strikes = get_nse_option_chain(option_symbol)
                option_df = option_df.dropna(subset=['CE.openInterest', 'PE.openInterest'])
                if search_query:
                    option_df = option_df[option_df['expiryDate'].astype(str).str.contains(search_query)]
                st.dataframe(option_df[['expiryDate', 'strikePrice', 'CE.openInterest', 'PE.openInterest']].head(20))
                plot_max_pain_chart(option_df)
                detect_oi_spikes(option_df)
                show_fake_pnl_chart()

            elif selected_segment == "Futures":
                st.subheader("🔮 Futures Segment Coming Soon...")
                st.info("This section is under development.")

            elif selected_segment == "Forex":
                st.subheader("🌍 Real-Time Forex Rates")
                forex_df = get_forex_data()
                st.dataframe(forex_df)

        except Exception as e:
            st.error(f"Error fetching data: {e}")

    time.sleep(refresh_interval)
    st.experimental_rerun()
