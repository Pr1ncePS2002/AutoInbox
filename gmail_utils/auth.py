from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os, json

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.labels",
          "https://www.googleapis.com/auth/gmail.send",
          "https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Build credentials.json dynamically from .env
            credentials_data = {
                "installed": {
                    "client_id": os.getenv("GMAIL_CLIENT_ID"),
                    "project_id": "gmail-automation-project",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                    "redirect_uris": ["http://localhost"]
                }
            }

            # Save a temporary credentials.json file
            with open("credentials.json", "w") as f:
                json.dump(credentials_data, f)

            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8888)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service

if __name__ == "__main__":
    print("🔑 Starting Gmail OAuth setup...")
    service = get_gmail_service()
    print("✅ Gmail authentication successful! token.json created.")

    # Quick test: list 5 recent messages
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages", [])
    print("📬 Latest 5 emails:")
    for msg in messages:
        print(msg["id"])
