import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

def fetch_sheet_data():
    """Fetch live data from Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Try to use Streamlit secrets first
    try:
        if 'gcp_service_account' in st.secrets:
            # Get credentials from Streamlit secrets
            credentials_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        else:
            # Fall back to credentials.json
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    except Exception as e:
        st.error(f"Authentication error: {e}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()
    
    # Connect to Google Sheets
    client = gspread.authorize(creds)

    sheet_id = "161ap6zuSkPNfmCXSS-3YkD-jD5lT8yT49Oo_3Q-dgf0"
    spreadsheet = client.open_by_url(f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    worksheet = spreadsheet.sheet1  # or spreadsheet.worksheet("Sheet1")
    data = worksheet.get_all_records()
    
    return pd.DataFrame(data)