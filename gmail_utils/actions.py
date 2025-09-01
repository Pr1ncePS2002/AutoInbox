import base64
from email.mime.text import MIMEText
from gmail_utils.auth import get_gmail_service
import time
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

def move_email(email_id, label_name):
    """Move a single email to a label."""
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"addLabelIds": [label_name]}
    ).execute()

def batch_move_emails(email_ids, label_name):
    """Move multiple emails to a label in a single batch operation."""
    if not email_ids:
        return
        
    service = get_gmail_service()
    
    def callback(request_id, response, exception):
        if exception:
            print(f"Error moving message {request_id}: {exception}")
    
    batch = service.new_batch_http_request(callback=callback)
    
    for email_id in email_ids:
        batch.add(
            service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"addLabelIds": [label_name]}
            )
        )
    
    batch.execute()

def delete_email(email_id):
    """Move a single email to trash."""
    service = get_gmail_service()
    service.users().messages().trash(userId="me", id=email_id).execute()

def batch_delete_emails(email_ids):
    """Move multiple emails to trash in a single batch operation."""
    if not email_ids:
        return
        
    service = get_gmail_service()
    
    def callback(request_id, response, exception):
        if exception:
            print(f"Error trashing message {request_id}: {exception}")
    
    batch = service.new_batch_http_request(callback=callback)
    
    for email_id in email_ids:
        batch.add(
            service.users().messages().trash(
                userId="me",
                id=email_id
            )
        )
    
    batch.execute()

def permanent_delete(query, batch_size=50):
    """Permanently delete emails matching a query with batching."""
    service = get_gmail_service()
    
    try:
        # Only fetch IDs to reduce data transfer
        results = service.users().messages().list(
            userId="me", 
            q=query, 
            fields="messages/id,nextPageToken"
        ).execute()
        
        messages = results.get("messages", [])
        if not messages:
            return
            
        # Process in batches to reduce API calls
        message_ids = [msg["id"] for msg in messages]
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i+batch_size]
            batch_permanent_delete(batch_ids)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(message_ids):
                time.sleep(1)
    
    except HttpError as error:
        print(f"An error occurred: {error}")

def batch_permanent_delete(email_ids):
    """Permanently delete multiple emails in a single batch operation."""
    if not email_ids:
        return
        
    service = get_gmail_service()
    
    def callback(request_id, response, exception):
        if exception:
            print(f"Error deleting message {request_id}: {exception}")
    
    batch = service.new_batch_http_request(callback=callback)
    
    for email_id in email_ids:
        batch.add(
            service.users().messages().delete(
                userId="me",
                id=email_id
            )
        )
    
    batch.execute()

def search_and_trash(query, batch_size=50):
    """Search for emails matching a query and move them to trash with batching."""
    service = get_gmail_service()
    
    try:
        # Only fetch IDs to reduce data transfer
        results = service.users().messages().list(
            userId="me", 
            q=query, 
            fields="messages/id,nextPageToken"
        ).execute()
        
        messages = results.get("messages", [])
        if not messages:
            return
            
        # Process in batches to reduce API calls
        message_ids = [msg["id"] for msg in messages]
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i+batch_size]
            batch_delete_emails(batch_ids)
            
            # Add delay between batches to avoid rate limiting
            if i + batch_size < len(message_ids):
                time.sleep(1)
    
    except HttpError as error:
        print(f"An error occurred: {error}")

from llm_utils.classifier import generate_response # You will create this function
def save_draft(subject, body, to_email):
    """Save a draft email with an automated response."""
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
    
    try:
        draft = service.users().drafts().create(userId="me", body=message).execute()
        return draft["id"]
    except HttpError as error:
        print(f"An error occurred while saving draft: {error}")
        return None

def batch_save_drafts(draft_data_list):
    """Save multiple draft emails in a batch operation."""
    if not draft_data_list:
        return []
        
    service = get_gmail_service()
    draft_ids = []
    
    def callback(request_id, response, exception):
        if exception:
            print(f"Error saving draft {request_id}: {exception}")
        else:
            draft_ids.append(response.get("id"))
    
    batch = service.new_batch_http_request(callback=callback)
    
    for i, draft_data in enumerate(draft_data_list):
        subject = draft_data.get("subject", "")
        body = draft_data.get("body", "")
        to_email = draft_data.get("to_email", "")
        
        # Generate response
        automated_response_body = generate_response(body)
        
        # Create message
        message_text = MIMEText(automated_response_body)
        message_text['Subject'] = f"Re: {subject}"
        message_text['From'] = "me"
        message_text['To'] = to_email
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message_text.as_bytes()).decode('utf-8')
        
        message = {
            "message": {
                "raw": raw_message
            }
        }
        
        batch.add(
            service.users().drafts().create(userId="me", body=message),
            request_id=str(i)
        )
    
    batch.execute()
    return draft_ids
