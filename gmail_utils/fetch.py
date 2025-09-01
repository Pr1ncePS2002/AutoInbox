from datetime import datetime, timedelta
from gmail_utils.auth import get_gmail_service
from gmail_utils.retry import retry_on_api_error, safe_api_call
from gmail_utils.monitor import track_api_call
from config.settings import CACHE_SETTINGS, API_SETTINGS, EMAIL_SETTINGS
import base64
import os
import json
import time
import logging
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

# Configure logging
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = CACHE_SETTINGS["CACHE_DIR"]
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache TTL in seconds
EMAIL_CACHE_TTL = CACHE_SETTINGS["EMAIL_CACHE_TTL"]

def _extract_email_content(message):
    """Extract email content from a Gmail message object."""
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    
    # Extract the sender's email address if present in headers
    from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
    to_email = ""
    if "<" in from_header and ">" in from_header:
        to_email = from_header.split("<")[-1].replace(">", "").strip()
    else:
        to_email = from_header.strip()

    # Gmail gives body in Base64 -> decode safely
    body = ""
    if "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    else:
        # Sometimes body is nested inside parts
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break

    return {
        "id": message["id"],
        "subject": subject,
        "body": body,
        "internalDate": int(message.get("internalDate", 0)),
        "to_email": to_email
    }

def _get_cached_emails(cache_key, max_age=EMAIL_CACHE_TTL):
    """Get emails from cache if available and not expired."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_file):
        # Check if cache is still valid
        if time.time() - os.path.getmtime(cache_file) < max_age:
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If cache file is corrupted, ignore it
                pass
    
    return None

def _save_emails_to_cache(emails, cache_key):
    """Save emails to cache."""
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(emails, f)
    except IOError:
        # If we can't write to cache, just continue without caching
        pass

@retry_on_api_error()
@track_api_call("fetch_existing_emails", quota_cost=5)
def fetch_existing_emails(max_results=EMAIL_SETTINGS["DEFAULT_EMAIL_COUNT"], use_cache=CACHE_SETTINGS["USE_CACHE"]):
    """
    Fetch emails from the last N days with subject, body, and internalDate.
    Uses caching, monitoring, and retry mechanisms for efficiency.
    """
    # Try to get from cache first
    cache_key = f"existing_emails_{max_results}"
    if use_cache:
        cached_emails = _get_cached_emails(cache_key)
        if cached_emails:
            logger.info(f"Using cached existing emails ({len(cached_emails)} emails)")
            return cached_emails
    
    logger.info(f"Fetching {max_results} existing emails from Gmail API")
    service = get_gmail_service()
    days_ago = (datetime.utcnow() - timedelta(days=EMAIL_SETTINGS["DAYS_LOOKBACK"])).strftime("%Y/%m/%d")
    query = f"after:{days_ago}"

    try:
        # Use fields parameter to only fetch the data we need
        results = service.users().messages().list(
            userId="me", 
            q=query, 
            maxResults=max_results,
            fields="messages/id,nextPageToken"
        ).execute()
        
        message_ids = [msg["id"] for msg in results.get("messages", [])]
        logger.info(f"Found {len(message_ids)} existing emails")
        
        # Use batch processing for better efficiency
        if not message_ids:
            return []
        
        # Use batch requests to reduce API calls
        emails = []
        batch_size = 10  # Process in batches of 10
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i+batch_size]
            
            # Fetch minimal fields needed for each message
            for msg_id in batch_ids:
                try:
                    m = service.users().messages().get(
                        userId="me", 
                        id=msg_id,
                        fields="id,payload/headers,payload/body,payload/parts,internalDate"
                    ).execute()
                    
                    email_data = _extract_email_content(m)
                    emails.append(email_data)
                    
                    # Add small delay between requests to avoid rate limiting
                    time.sleep(0.1)
                except HttpError as error:
                    print(f"Error fetching message {msg_id}: {error}")
                    continue
        
        # Save to cache for future use
        if emails and use_cache:
            _save_emails_to_cache(emails, cache_key)
            
        return emails
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def fetch_new_emails(max_results=5, use_cache=False):
    """Fetch new (unread) emails from Gmail."""
    # For unread emails, we use a shorter cache time or no cache
    cache_key = "unread_emails"
    cache_ttl = 300  # 5 minutes for unread emails
    
    if use_cache:
        cached_emails = _get_cached_emails(cache_key, cache_ttl)
        if cached_emails:
            return cached_emails
    
    service = get_gmail_service()
    
    try:
        # Use fields parameter to only fetch the data we need
        results = service.users().messages().list(
            userId="me", 
            q="is:unread", 
            maxResults=max_results,
            fields="messages/id,nextPageToken"
        ).execute()
        
        message_ids = [msg["id"] for msg in results.get("messages", [])]
        
        # Use batch requests to reduce API calls
        emails = []
        
        for msg_id in message_ids:
            try:
                m = service.users().messages().get(
                    userId="me", 
                    id=msg_id,
                    fields="id,payload/headers,payload/body,payload/parts,internalDate"
                ).execute()
                
                email_data = _extract_email_content(m)
                emails.append(email_data)
                
                # Add small delay between requests to avoid rate limiting
                time.sleep(0.1)
            except HttpError as error:
                print(f"Error fetching message {msg_id}: {error}")
                continue
        
        # Save to cache for future use if enabled
        if emails and use_cache:
            _save_emails_to_cache(emails, cache_key)
            
        return emails
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []