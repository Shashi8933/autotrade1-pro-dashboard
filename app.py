import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import json # Required for json.JSONDecodeError

# --- NSE Data Fetching Function ---
def get_nse_equity_data():
    """
    Fetches NIFTY 50 equity data from the NSE India website.
    Returns a pandas DataFrame with the data, or an empty DataFrame on error.
    """
    api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    # Using a common browser User-Agent and more specific headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market", # A relevant referer
        "X-Requested-With": "XMLHttpRequest", # Often useful for AJAX endpoints
        "Connection": "keep-alive"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    response_text_area = None # Placeholder for displaying response text on error

    try:
        # It's good practice to hit a browseable page first to establish a session and get cookies
        nse_market_page_url = "https://www.nseindia.com/market-data/live-equity-market"
        session.get(nse_market_page_url, timeout=10) # Increased timeout
        
        # Make the API call
        response = session.get(api_url, timeout=10) # Increased timeout
        
        # Log status code and content type for debugging in Streamlit if needed
        # st.caption(f"NSE API Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")

        response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)
        
        # Attempt to parse JSON
        data = response.json()
        
        if 'data' in data and isinstance(data['data'], list):
            df = pd.DataFrame(data['data'])
            return df
        else:
            st.error("NSE Equity Data Error: 'data' key not found or not in expected format in the JSON response.")
            if isinstance(data, dict): # if it's a dict, show it
                st.json(data)
            else: # otherwise, show as text
                st.text_area("Problematic JSON Response", str(data), height=150)
            return pd.DataFrame()

    except requests.exceptions.HTTPError as http_err:
        st.error(f"NSE Equity Data Error (HTTPError): {http_err}")
        if 'response' in locals() and response is not None:
            response_text_area = response.text
        st.text_area("Response Text (HTTPError)", response_text_area if response_text_area else "No response object", height=150)
        return pd.DataFrame()
    except json.JSONDecodeError as json_err:
        st.error(f"NSE Equity Data Error (JSONDecodeError): {json_err}")
        st.info("This usually means the NSE did not return valid JSON. It might be an HTML error page, a CAPTCHA, or a block. Check the response text below.")
        if 'response' in locals() and response is not None:
            response_text_area = response.text
        st.text_area("Response Text (JSONDecodeError)", response_text_area if response_text_area else "No response object", height=300)
        return pd.DataFrame()
    except requests.exceptions.RequestException as req_err: # Catch other request-related errors (e.g., timeout, connection error)
        st.error(f"NSE Equity Data Error (RequestException): {req_err}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected NSE Equity Data Error occurred: {e}")
        if 'response' in locals() and response is not None:
            response_text_area = response.text
            st.text_area("Response Text (Generic Error)", response_text_area, height=150)
        return pd.DataFrame()

# --- Streamlit App Layout ---
st.set_page_config(page_title="NIFTY 50 Live Data", layout="wide")

st.title("📈 NSE NIFTY 50 Live Data")
st.caption(f"Data refreshes automatically every 10 seconds. Source: NSE India")

# Auto-refresh setup
REFRESH_INTERVAL_SECONDS = 10
st_autorefresh(interval=REFRESH_INTERVAL_SECONDS * 1000, key="nifty50autorefresh")

# Fetch and display data
nifty50_df = get_nse_equity_data()

if not nifty50_df.empty:
    st.success("NIFTY 50 data fetched successfully!")
    
    # Define columns to display and their preferred order
    # You can adjust these based on the actual columns available and your preference
    desired_columns = [
        'symbol', 'priority', 'identifier', 'lastPrice', 'change', 'pChange', 
        'open', 'dayHigh', 'dayLow', 'previousClose', 
        'totalTradedVolume', 'totalTradedValue', 'lastUpdateTime',
        'yearHigh', 'yearLow', 'perChange365d', 'perChange30d'
    ]
    
    # Filter DataFrame to include only existing desired columns
    # This prevents errors if some columns are unexpectedly missing
    columns_to_display = [col for col in desired_columns if col in nifty50_df.columns]
    display_df = nifty50_df[columns_to_display]
    
    st.dataframe(display_df, height=600, use_container_width=True) # Adjust height as needed

    # Show some metadata if available (example: timestamp from the API)
    if 'timestamp' in nifty50_df.columns: # Assuming the API might provide a general timestamp for the data
        st.caption(f"Data Timestamp (from API): {nifty50_df['timestamp'].iloc[0] if not nifty50_df.empty else 'N/A'}")
    elif 'lastUpdateTime' in display_df.columns and not display_df['lastUpdateTime'].empty:
         st.caption(f"Last Update Time for NIFTY 50 Index (from API): {display_df[display_df['symbol'] == 'NIFTY 50']['lastUpdateTime'].iloc[0] if not display_df[display_df['symbol'] == 'NIFTY 50'].empty else 'N/A'}")


else:
    st.warning("Could not retrieve NIFTY 50 data from NSE at this moment.")
    st.info("This could be due to various reasons such as temporary issues with the NSE API, network connectivity problems, or rate limiting if requests are too frequent. Check error messages above if any.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Disclaimer:** This tool is for informational purposes only. Data is sourced from NSE India and may be subject to delays or inaccuracies. Not financial advice.")
st.sidebar.markdown(f"Refresh Interval: **{REFRESH_INTERVAL_SECONDS} seconds**")
