from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_existing_emails
from gmail_utils.actions import move_email, delete_email, batch_move_emails, batch_delete_emails
# from llm_utils.classifier import classify_email, needs_response
from llm_utils.summarizer import summarize_email
from gmail_utils.retry import retry_on_api_error, safe_api_call
from gmail_utils.monitor import track_api_call, get_quota_monitor
from config.settings import EMAIL_SETTINGS, GMAIL_LABELS, API_SETTINGS
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from typing import List, Optional, Dict
from llm_utils.classifier import categorize_email, check_if_reply_needed
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

class EmailState(BaseModel):
    emails: Optional[List[dict]] = None
    classified_emails: Optional[List[dict]] = None
    actions: Optional[List[dict]] = None
    count: Optional[int] = None

def process_existing_emails():
    """
    Process existing emails workflow with monitoring, batch operations, and retry mechanisms.
    """
    sg = StateGraph(EmailState)
    sg.add_node("fetch_existing", fetch_existing_emails_node)
    sg.add_node("classify", classify_emails_node)
    sg.add_node("route", route_existing_action)
    sg.add_edge("fetch_existing", "classify")
    sg.add_edge("classify", "route")
    sg.set_entry_point("fetch_existing")
    sg.set_finish_point("route")
    return sg.compile()

@track_api_call("fetch_existing_emails_workflow", quota_cost=1)
def fetch_existing_emails_node(state: EmailState):
    """Fetch existing emails with caching and monitoring."""
    num_to_fetch = state.count if state.count is not None else EMAIL_SETTINGS["DEFAULT_EMAIL_COUNT"]
    logger.info(f"Fetching {num_to_fetch} existing emails")
    
    # Check if we should throttle based on quota usage
    quota_monitor = get_quota_monitor()
    if quota_monitor.should_throttle():
        logger.warning("Throttling email fetching due to high API usage")
        num_to_fetch = min(num_to_fetch, 3)  # Reduce batch size when throttling
    
    emails = fetch_existing_emails(num_to_fetch, use_cache=True)
    logger.info(f"Fetched {len(emails)} existing emails")
    return {"emails": emails}

@track_api_call("classify_emails_workflow", quota_cost=1)
def classify_emails_node(state: EmailState):
    """Classify emails with a two-step process."""
    classified = []
    if not state.emails:
        logger.warning("No emails to classify")
        return {"classified_emails": []}
    
    logger.info(f"Classifying {len(state.emails)} emails")
    for email in state.emails:
        time.sleep(API_SETTINGS["API_CALL_DELAY"] * 20)
        
        try:
            # Step 1: Broad Categorization
            category = categorize_email(email["subject"], email["body"])
            final_label = category

            # Step 2: If it's important, check if a reply is needed
            if category == "Important":
                importance_label = check_if_reply_needed(email["subject"], email["body"])
                final_label = importance_label

            classified.append({**email, "label": final_label})
            logger.debug(f"Classified email {email['id']} as {final_label}")
        except Exception as e:
            logger.error(f"Error classifying email {email['id']}: {e}")
            continue
            
    logger.info(f"Successfully classified {len(classified)} emails")
    return {"classified_emails": classified}

@retry_on_api_error()
@track_api_call("route_emails_workflow", quota_cost=2)
def route_existing_action(state: EmailState):
    """Route emails using batch operations for efficiency."""
    if not state.classified_emails:
        logger.warning("No classified emails to route")
        return {"actions": []}
        
    actions = []
    now = datetime.now(timezone.utc)
    
    # Group emails by label for batch processing
    emails_by_label: Dict[str, List[str]] = {
        "wanted_important": [],
        "unwanted_important": [],
        "promotions": [],
        "updates": [],
        "spam": [],
        "delete": []
    }
    
    # First pass: categorize emails
    for email in state.classified_emails:
        label = email["label"]
        email_id = email["id"]
        
        if "internalDate" in email:
            received = datetime.fromtimestamp(int(email["internalDate"]) / 1000, tz=timezone.utc)
        else:
            received = now
            
        # Use the new classification system
        if label == "Wanted Important":
            emails_by_label["wanted_important"].append(email_id)
        elif label == "Unwanted Important":
            emails_by_label["unwanted_important"].append(email_id)
        elif label == "Promotions":
            # Delete old promotions
            if received < now - timedelta(days=10):
                emails_by_label["delete"].append(email_id)
                actions.append({"email_id": email_id, "action": "Deleted Promotion"})
            else:
                emails_by_label["promotions"].append(email_id)
        elif label == "Updates":
            emails_by_label["updates"].append(email_id)
        elif label == "Spam":
            emails_by_label["spam"].append(email_id)
        # Handle legacy classification
        elif label == "Important":
            if needs_response(email["subject"], email["body"]):
                emails_by_label["wanted_important"].append(email_id)
            else:
                emails_by_label["unwanted_important"].append(email_id)
            
        actions.append({"email_id": email_id, "label": label})
    
    # Second pass: batch process emails by category
    logger.info("Processing emails in batches")
    
    # Process each category with batch operations
    if emails_by_label["wanted_important"]:
        batch_move_emails(emails_by_label["wanted_important"], GMAIL_LABELS["WANTED_IMPORTANT"])
        logger.info(f"Moved {len(emails_by_label['wanted_important'])} emails to Wanted Important")
        
    if emails_by_label["unwanted_important"]:
        batch_move_emails(emails_by_label["unwanted_important"], GMAIL_LABELS["UNWANTED_IMPORTANT"])
        logger.info(f"Moved {len(emails_by_label['unwanted_important'])} emails to Unwanted Important")
        
    if emails_by_label["promotions"]:
        batch_move_emails(emails_by_label["promotions"], GMAIL_LABELS["PROMOTIONS"])
        logger.info(f"Moved {len(emails_by_label['promotions'])} emails to Promotions")
        
    if emails_by_label["updates"]:
        batch_move_emails(emails_by_label["updates"], GMAIL_LABELS["UPDATES"])
        logger.info(f"Moved {len(emails_by_label['updates'])} emails to Updates")
        
    if emails_by_label["spam"]:
        batch_move_emails(emails_by_label["spam"], GMAIL_LABELS["SPAM"])
        logger.info(f"Moved {len(emails_by_label['spam'])} emails to Spam")
        
    if emails_by_label["delete"]:
        batch_delete_emails(emails_by_label["delete"])
        logger.info(f"Deleted {len(emails_by_label['delete'])} old promotional emails")
    
    logger.info(f"Completed processing {len(state.classified_emails)} emails")
    return {"actions": actions}