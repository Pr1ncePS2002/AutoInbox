from langgraph.graph import StateGraph
from gmail_utils.actions import search_and_trash
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class CleanupState(BaseModel):
    status: Optional[str] = None

def daily_cleanup():
    sg = StateGraph(CleanupState)
    sg.add_node("cleanup", cleanup_task)
    sg.set_entry_point("cleanup")
    sg.set_finish_point("cleanup")
    return sg.compile()

def cleanup_task(state: CleanupState):
    now = datetime.utcnow()
    # Move unread promotions older than 15 days to trash
    search_and_trash(query="category:promotions is:unread older_than:15d")
    return {"status": "cleanup complete"}