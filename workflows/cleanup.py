from langgraph.graph import StateGraph
from gmail_utils.actions import permanent_delete, search_and_trash
from datetime import datetime, timedelta

def daily_cleanup():
    sg = StateGraph()
    sg.add_node("cleanup", cleanup_task)
    return sg.compile()

def cleanup_task(state):
    now = datetime.utcnow()

    # 1. Permanently delete trash older than 90 days
    permanent_delete(query="in:trash older_than:90d")

    # 2. Move unread promotions older than 15 days to trash
    search_and_trash(query="category:promotions is:unread older_than:15d")

    return {"status": "cleanup complete"}
