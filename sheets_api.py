import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os

def fetch_sheet_data():
    """Fetch live data from Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds = None
    error_message = None
    
    # Try to use Streamlit secrets first
    try:
        # Check if secrets are available
        if st.secrets:
            credentials_dict = dict(st.secrets)
            
            # Ensure the private key is properly formatted if it exists
            if 'private_key' in credentials_dict:
                credentials_dict['private_key'] = credentials_dict['private_key'].replace('\\n', '\n')
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    except Exception as e:
        error_message = f"Error using Streamlit secrets: {str(e)}"
        st.warning(error_message)
    
    # If secrets didn't work, try credentials.json as fallback
    if creds is None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        except Exception as e:
            if error_message:
                error_message += f"\nError using credentials.json: {str(e)}"
            else:
                error_message = f"Error using credentials.json: {str(e)}"
            
            st.error(error_message)
            # Return empty DataFrame as fallback
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
