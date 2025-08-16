import base64
from email.mime.text import MIMEText
from gmail_utils.auth import get_gmail_service

def move_email(email_id, label_name):
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"addLabelIds": [label_name]}
    ).execute()

def delete_email(email_id):
    service = get_gmail_service()
    service.users().messages().trash(userId="me", id=email_id).execute()

def permanent_delete(query):
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    for msg in messages:
        service.users().messages().delete(userId="me", id=msg["id"]).execute()

def search_and_trash(query):
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    for msg in messages:
        service.users().messages().trash(userId="me", id=msg["id"]).execute()

from llm_utils.classifier import generate_response # You will create this function
def save_draft(subject, body, to_email):
    service = get_gmail_service()
    
    # 1. Generate the automated response using a new function
    automated_response_body = generate_response(body)

    # 2. Create the MIMEText message with the new response
    message_text = MIMEText(automated_response_body)
    message_text['Subject'] = f"Re: {subject}"
    message_text['From'] = "me"
    message_text['To'] = to_email

    # 3. Encode the message to base64url string
    raw_message = base64.urlsafe_b64encode(message_text.as_bytes()).decode('utf-8')

    message = {
        "message": {
            "raw": raw_message
        }
    }
    
    draft = service.users().drafts().create(userId="me", body=message).execute()
    return draft["id"]
