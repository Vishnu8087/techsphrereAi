from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

# Define the scopes for all required Google services
SCOPES = [
    'https://www.googleapis.com/auth/drive',          # Full access to Google Drive
    'https://www.googleapis.com/auth/documents',     # Full access to Google Docs
    'https://www.googleapis.com/auth/spreadsheets',  # Full access to Google Sheets
    'https://www.googleapis.com/auth/forms',         # Full access to Google Forms
    'https://www.googleapis.com/auth/gmail.send',    # Send emails using Gmail
    'https://www.googleapis.com/auth/gmail.readonly',# Read-only access to Gmail
    'https://www.googleapis.com/auth/classroom.coursework.me', # Manage your own coursework
    'https://www.googleapis.com/auth/classroom.coursework.students', # Manage students' coursework
    'https://www.googleapis.com/auth/classroom.rosters' ,# Access class rosters
    'https://www.googleapis.com/auth/classroom.courses.readonly', #SHOW THE CLASS ROOM ID AND NAMES
    'https://www.googleapis.com/auth/classroom.courses',   #CREAE THE  CLASS ROOM COURSES
    'https://www.googleapis.com/auth/forms.body',  # Allows editing the form structure (needed for creating questions)
    'https://www.googleapis.com/auth/forms.body.readonly',  # Allows reading form structure
    'https://www.googleapis.com/auth/forms.responses.readonly',  # Allows reading form responses
    'https://www.googleapis.com/auth/drive.file' ,# Allows creating and managing forms in Google Drive

    "https://www.googleapis.com/auth/drive.metadata.readonly"

]


# Path to the credentiallient_user4.jsons file
CREDENTIALS_FILE = r'credentials\client_user4.json'  # Ensure this file exists and is properly configured

# Always authenticate and obtain a new token
flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
# Use `run_local_server` to authenticate
creds = flow.run_local_server(port=0, open_browser=True)  # Disables automatic browser launch

# Save the credentials for reuse
with open(r'credentials\token1.json', 'w') as token:
    token.write(creds.to_json())

print("Authentication successful!")
