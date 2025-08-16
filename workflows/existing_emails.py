from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_existing_emails
from gmail_utils.actions import move_email, delete_email
from llm_utils.classifier import classify_email
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import List, Optional
import time

class EmailState(BaseModel):
    emails: Optional[List[dict]] = None
    classified_emails: Optional[List[dict]] = None
    actions: Optional[List[dict]] = None
    count: Optional[int] = None

def process_existing_emails():
    sg = StateGraph(EmailState)
    sg.add_node("fetch_existing", fetch_existing_emails_node)
    sg.add_node("classify", classify_emails_node)
    sg.add_node("route", route_existing_action)
    sg.add_edge("fetch_existing", "classify")
    sg.add_edge("classify", "route")
    sg.set_entry_point("fetch_existing")
    sg.set_finish_point("route")
    return sg.compile()

def fetch_existing_emails_node(state: EmailState):
    num_to_fetch = state.count if state.count is not None else 5
    emails = fetch_existing_emails(num_to_fetch)
    return {"emails": emails}

def classify_emails_node(state: EmailState):
    classified = []
    if state.emails:
        for email in state.emails:
            time.sleep(4)
            try:
                label = classify_email(email["subject"], email["body"])
                classified.append({**email, "label": label})
            except Exception as e:
                print(f"Error classifying email {email['id']}: {e}")
                continue
    return {"classified_emails": classified}

def route_existing_action(state: EmailState):
    actions = []
    now = datetime.now(timezone.utc)
    if state.classified_emails:
        for email in state.classified_emails:
            label = email["label"]
            email_id = email["id"]
            if "internalDate" in email:
                received = datetime.fromtimestamp(int(email["internalDate"]) / 1000, tz=timezone.utc)
            else:
                received = now
            if label == "Important":
                move_email(email_id, "IMPORTANT") 
            elif label == "Promotions":
                if received < now - timedelta(days=10):
                    delete_email(email_id)
                    actions.append({"email_id": email_id, "action": "Deleted Promotion"})
                    continue
                else:
                    move_email(email_id, "CATEGORY_PROMOTIONS")
            elif label == "Updates":
                move_email(email_id, "CATEGORY_UPDATES")
            elif label == "Spam":
                move_email(email_id, "SPAM")
            actions.append({"email_id": email_id, "label": label})
    return {"actions": actions}