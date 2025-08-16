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

def save_draft(subject, body):
    service = get_gmail_service()
    message = {
        "message": {
            "raw": f"Subject: Re: {subject}\n\nAuto-generated reply:\n{body}".encode("utf-8").decode("latin1")
        }
    }
    draft = service.users().drafts().create(userId="me", body=message).execute()
    return draft["id"]
