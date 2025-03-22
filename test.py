import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Define the scope (permissions for Google Sheets API)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from the JSON key file
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

# Authenticate with Google Sheets
client = gspread.authorize(creds)

# Open the Google Sheet by name or URL
sheet_id = "161ap6zuSkPNfmCXSS-3YkD-jD5lT8yT49Oo_3Q-dgf0"
spreadsheet = client.open_by_url(f"https://docs.google.com/spreadsheets/d/{sheet_id}")

# Select the worksheet (default is first sheet)
worksheet = spreadsheet.sheet1  # or spreadsheet.worksheet("Sheet1")

# Fetch all data
data = worksheet.get_all_records()

# Convert to DataFrame (for AI processing)
df = pd.DataFrame(data)

# Print the data
print(df)
