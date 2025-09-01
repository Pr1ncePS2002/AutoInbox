from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os, json
import logging
from functools import lru_cache
import time
from config.settings import CACHE_SETTINGS
from gmail_utils.retry import retry_on_api_error, track_api_usage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gmail_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.labels",
          "https://www.googleapis.com/auth/gmail.send",
          "https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

# Global service instance
_gmail_service = None
_last_service_time = 0
_SERVICE_CACHE_TTL = CACHE_SETTINGS["SERVICE_CACHE_TTL"]

@lru_cache(maxsize=1)
@track_api_usage
def get_gmail_service():
    """
    Get Gmail service with caching to reduce API initialization calls.
    Uses both a global variable and LRU cache for optimal performance.
    Includes retry mechanisms and error handling.
    """
    global _gmail_service, _last_service_time
    
    # Return cached service if it exists and is not expired
    current_time = time.time()
    if _gmail_service and (current_time - _last_service_time) < _SERVICE_CACHE_TTL:
        logger.debug("Using cached Gmail service")
        return _gmail_service
    
    logger.info("Initializing new Gmail service")
    
    try:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Creating new credentials")
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

        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_SETTINGS["CACHE_DIR"], exist_ok=True)
        
        _gmail_service = build("gmail", "v1", credentials=creds)
        _last_service_time = current_time
        logger.info("Gmail service initialized successfully")
        return _gmail_service
        
    except HttpError as e:
        logger.error(f"HTTP error during service initialization: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing Gmail service: {e}")
        raise

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
