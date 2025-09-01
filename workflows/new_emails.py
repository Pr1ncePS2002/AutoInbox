from typing import List, Optional
from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_new_emails
from gmail_utils.actions import move_email, save_draft, batch_move_emails
from llm_utils.classifier import classify_email, needs_response
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
    # Use cache for better performance
    emails = fetch_new_emails(use_cache=True)
    return {"emails": emails}

def classify_emails_node(state: EmailState):
    classified = []
    if state.emails:
        for email in state.emails:
            # Add a 2-second delay to comply with the quota but optimize for performance
            time.sleep(2) 
            
            try:
                # Use the new classification system
                label = classify_email(email["subject"], email["body"])
                needs_reply = label.strip().lower() == "wanted important"
                classified.append({
                    **email, 
                    "label": label,
                    "needs_reply": needs_reply
                })
            except Exception as e:
                print(f"Error classifying email {email['id']}: {e}")
                # Add with default classification on error
                classified.append({
                    **email, 
                    "label": "Unwanted Important",
                    "needs_reply": False
                })
    return {"classified_emails": classified}

def route_action(state: EmailState):
    results = []
    
    # Prepare batch operations
    wanted_important_ids = []
    unwanted_important_ids = []
    
    if state.classified_emails:
        for email in state.classified_emails:
            email_id = email["id"]
            subject = email["subject"]
            body = email["body"]
            to_email = email["to_email"]
            label = email["label"]
            needs_reply = email.get("needs_reply", False)
            
            # Categorize based on new classification
            if label.strip().lower() == "wanted important":
                wanted_important_ids.append(email_id)
                
                # Only create draft replies for emails that need a response
                if needs_reply:
                    try:
                        draft_id = save_draft(subject, body, to_email)
                        results.append({
                            "email_id": email_id, 
                            "action": "Created draft reply",
                            "draft_id": draft_id
                        })
                    except Exception as e:
                        print(f"Error creating draft for {email_id}: {e}")
            else:  # Unwanted Important
                unwanted_important_ids.append(email_id)
                results.append({
                    "email_id": email_id, 
                    "action": "Marked as important, no reply needed"
                })
        
        # Batch move emails to appropriate labels
        if wanted_important_ids:
            batch_move_emails(wanted_important_ids, "IMPORTANT")
        
        if unwanted_important_ids:
            batch_move_emails(unwanted_important_ids, "IMPORTANT")
            
    return {"results": results}