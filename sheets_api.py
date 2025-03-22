import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

def fetch_sheet_data():
    """Fetch live data from Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Only use Streamlit secrets, no fallback to credentials.json
    try:
        # Check if secrets are available
        credentials_dict = dict(st.secrets)
        
        # Ensure the private key is properly formatted if it exists
        if 'private_key' in credentials_dict:
            credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    except Exception as e:
        # Return empty DataFrame without showing any error messages
        return pd.DataFrame()
    
    # If we have credentials, proceed with Google Sheets
    client = gspread.authorize(creds)
    
    try:
        sheet_id = "161ap6zuSkPNfmCXSS-3YkD-jD5lT8yT49Oo_3Q-dgf0"
        spreadsheet = client.open_by_url(f"https://docs.google.com/spreadsheets/d/{sheet_id}")
        worksheet = spreadsheet.sheet1  # or spreadsheet.worksheet("Sheet1")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error accessing Google Sheet: {str(e)}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()
