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
from gmail_utils.attachments import process_message_attachments
from config.settings import ATTACHMENT_SETTINGS

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
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_path):
        age = time.time() - os.path.getmtime(cache_path)
        if age < max_age:
            with open(cache_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except Exception:
                    return None
    return None


def _save_emails_to_cache(emails, cache_key):
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False)

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
    days_ago = (datetime.utcnow() - timedelta(days=EMAIL_SETTINGS["DAYS_LOOKBACK"]))
    query = f"after:{days_ago.strftime('%Y/%m/%d')}"

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
        include_attachments = ATTACHMENT_SETTINGS.get("INCLUDE_IN_CONTEXT", True)
        
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
                    # Extract attachments content
                    att_text, att_meta = process_message_attachments(service, m)
                    email_data["attachments_text"] = att_text
                    email_data["attachments_meta"] = att_meta
                    if include_attachments and att_text:
                        # Append attachment text to body for richer context
                        email_data["body"] = f"{email_data['body']}\n\n{att_text}".strip()
                    emails.append(email_data)
                    
                    # Add small delay between requests to avoid rate limiting
                    time.sleep(API_SETTINGS.get("API_CALL_DELAY", 0.1))
                except HttpError as error:
                    logger.warning(f"Error fetching message {msg_id}: {error}")
                    continue
        
        # Save to cache for future use
        if emails and use_cache:
            _save_emails_to_cache(emails, cache_key)
            
        return emails
    
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return []


def fetch_new_emails(max_results=5, use_cache=False):
    """Fetch new (unread) emails from Gmail."""
    # For unread emails, we use a shorter cache time or no cache
    cache_key = "unread_emails"
    cache_ttl = CACHE_SETTINGS.get("UNREAD_CACHE_TTL", 300)
    
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
        include_attachments = ATTACHMENT_SETTINGS.get("INCLUDE_IN_CONTEXT", True)
        
        for msg_id in message_ids:
            try:
                m = service.users().messages().get(
                    userId="me", 
                    id=msg_id,
                    fields="id,payload/headers,payload/body,payload/parts,internalDate"
                ).execute()
                
                email_data = _extract_email_content(m)
                # Extract attachments content
                att_text, att_meta = process_message_attachments(service, m)
                email_data["attachments_text"] = att_text
                email_data["attachments_meta"] = att_meta
                if include_attachments and att_text:
                    email_data["body"] = f"{email_data['body']}\n\n{att_text}".strip()
                emails.append(email_data)
                
                # Add small delay between requests to avoid rate limiting
                time.sleep(API_SETTINGS.get("API_CALL_DELAY", 0.1))
            except HttpError as error:
                logger.warning(f"Error fetching message {msg_id}: {error}")
                continue
        
        # Save to cache for future use if enabled
        if emails and use_cache:
            _save_emails_to_cache(emails, cache_key)
            
        return emails
    
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return []