from langgraph.graph import StateGraph
from gmail_utils.fetch import fetch_new_emails
from gmail_utils.actions import move_email, save_draft
from llm_utils.classifier import classify_email

def process_new_emails():
    sg = StateGraph()

    sg.add_node("fetch_emails", fetch_new_emails)
    sg.add_node("classify", classify_email_node)
    sg.add_node("route", route_action)

    sg.add_edge("fetch_emails", "classify")
    sg.add_edge("classify", "route")

    return sg.compile()

def classify_email_node(state):
    subject, body, email_id = state["subject"], state["body"], state["id"]
    label = classify_email(subject, body)
    return {"id": email_id, "label": label, "subject": subject, "body": body}

def route_action(state):
    label = state["label"]
    email_id = state["id"]
    subject, body = state["subject"], state["body"]

    if label == "Important":
        move_email(email_id, "IMPORTANT")
    elif label == "High Priority":
        move_email(email_id, "HIGH_PRIORITY")
        draft_id = save_draft(subject, body)  # auto-generate reply
        return {"draft_id": draft_id}
    elif label == "Promotions":
        move_email(email_id, "CATEGORY_PROMOTIONS")
    elif label == "Updates":
        move_email(email_id, "CATEGORY_UPDATES")
    elif label == "Spam":
        move_email(email_id, "SPAM")
    return {}
