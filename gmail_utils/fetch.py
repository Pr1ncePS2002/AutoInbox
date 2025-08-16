from datetime import datetime, timedelta
from gmail_utils.auth import get_gmail_service

def fetch_existing_emails():
    """Fetch emails from last 50 days."""
    service = get_gmail_service()
    days_ago = (datetime.utcnow() - timedelta(days=50)).strftime("%Y/%m/%d")
    query = f"after:{days_ago}"
    
    results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    messages = results.get("messages", [])
    
    emails = []
    for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = m["payload"]
        headers = payload.get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        body = payload.get("body", {}).get("data", "")
        emails.append({"id": msg["id"], "subject": subject, "body": body})
    return emails
