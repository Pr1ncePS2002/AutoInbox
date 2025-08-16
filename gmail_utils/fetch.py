from datetime import datetime, timedelta
from gmail_utils.auth import get_gmail_service
import base64

def fetch_existing_emails(max_results):
    """Fetch emails from the last 15 days with subject, body, and internalDate."""
    service = get_gmail_service()
    days_ago = (datetime.utcnow() - timedelta(days=15)).strftime("%Y/%m/%d")
    query = f"after:{days_ago}"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results # Use the max_results parameter
    ).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = m.get("payload", {})
        headers = payload.get("headers", [])

        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")

        body = ""
        if "body" in payload and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        else:
            parts = payload.get("parts", [])
            for part in parts:
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break

        emails.append({
            "id": msg["id"],
            "subject": subject,
            "body": body,
            "internalDate": int(m.get("internalDate", 0))
        })
    return emails


def fetch_new_emails():
    """Fetch new (unread) emails from Gmail."""
    service = get_gmail_service()
    
    results = service.users().messages().list(
        userId="me", q="is:unread", maxResults=5
    ).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = m.get("payload", {})
        headers = payload.get("headers", [])

        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
        
        # Extract the sender's email address
        from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
        # A simple way to get the email part is to split at < and >
        to_email = from_header.split("<")[-1].replace(">", "").strip()

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

        emails.append({
            "id": msg["id"],
            "subject": subject,
            "body": body,
            "internalDate": int(m.get("internalDate", 0)),
            "to_email": to_email # Add the sender's email to the dictionary
        })
    return emails