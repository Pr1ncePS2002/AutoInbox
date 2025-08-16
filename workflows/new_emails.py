from typing import List, Optional
from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_new_emails
from gmail_utils.actions import move_email, save_draft
from llm_utils.classifier import classify_email
from pydantic import BaseModel
import time # Import the time module

class EmailState(BaseModel):
    emails: Optional[List[dict]] = None
    classified_emails: Optional[List[dict]] = None
    results: Optional[List[dict]] = None

def process_new_emails():
    sg = StateGraph(EmailState)
    sg.add_node("fetch_emails", fetch_emails_node)
    sg.add_node("classify", classify_emails_node)
    sg.add_node("route", route_action)
    sg.add_edge("fetch_emails", "classify")
    sg.add_edge("classify", "route")
    sg.set_entry_point("fetch_emails")
    sg.set_finish_point("route")
    return sg.compile()

def fetch_emails_node(state: EmailState):
    emails = fetch_new_emails()
    return {"emails": emails}

def classify_emails_node(state: EmailState):
    classified = []
    if state.emails:
        for email in state.emails:
            # Add a 4-second delay to comply with the 15 requests per minute quota
            time.sleep(4) 
            
            try:
                label = classify_email(email["subject"], email["body"])
                classified.append({**email, "label": label})
            except Exception as e:
                print(f"Error classifying email {email['id']}: {e}")
                # You can add a fallback or skip the email on error
                continue
    return {"classified_emails": classified}

# In workflows/new_emails.py

def route_action(state: EmailState):
    results = []
    if state.classified_emails:
        for email in state.classified_emails:
            label = email["label"]
            email_id = email["id"]
            subject, body = email["subject"], email["body"]
            to_email = email["to_email"] # Access the sender's email from the state

            if label == "Important":
                move_email(email_id, "IMPORTANT")
                draft_id = save_draft(subject, body, to_email) # Pass the recipient's email
                results.append({"email_id": email_id, "draft_id": draft_id})
            elif label == "Promotions":
                move_email(email_id, "CATEGORY_PROMOTIONS")
            elif label == "Updates":
                move_email(email_id, "CATEGORY_UPDATES")
            elif label == "Spam":
                move_email(email_id, "SPAM")
            results.append({"email_id": email_id, "label": label})
    return {"results": results}