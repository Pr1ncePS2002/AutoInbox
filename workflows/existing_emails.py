from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_existing_emails
from gmail_utils.actions import move_email, delete_email
from llm_utils.classifier import classify_email
from datetime import datetime, timedelta

def process_existing_emails():
    sg = StateGraph()
    sg.add_node("fetch_existing", fetch_existing_emails_node)
    sg.add_node("classify", classify_email_node)
    sg.add_node("route", route_existing_action)

    sg.add_edge("fetch_existing", "classify")
    sg.add_edge("classify", "route")
    return sg.compile()

def fetch_existing_emails_node(state):
    emails = fetch_existing_emails()
    return {"emails": emails}

def classify_email_node(state):
    classified = []
    for email in state["emails"]:
        label = classify_email(email["subject"], email["body"])
        classified.append({**email, "label": label})
    return {"classified_emails": classified}

def route_existing_action(state):
    actions = []
    now = datetime.utcnow()
    for email in state["classified_emails"]:
        label = email["label"]
        email_id = email["id"]

        if label == "Important":
            move_email(email_id, "IMPORTANT")
        elif label == "High Priority":
            move_email(email_id, "HIGH_PRIORITY")
        elif label == "Promotions":
            # delete if older than 10 days
            received = now - timedelta(days=11)   # simulate timestamp
            if received < now - timedelta(days=10):
                delete_email(email_id)  # Move to Trash
            else:
                move_email(email_id, "CATEGORY_PROMOTIONS")
        elif label == "Updates":
            move_email(email_id, "CATEGORY_UPDATES")
        elif label == "Spam":
            move_email(email_id, "SPAM")
        actions.append((email_id, label))
    return {"actions": actions}
