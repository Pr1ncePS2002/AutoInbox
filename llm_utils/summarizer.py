"""
Email summarization utilities to reduce token usage and provide context.
Includes basic heuristic summarization and optional AI-powered summarization.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from config.settings import EMAIL_SETTINGS

# Attempt to use OpenAI for AI summarization, fallback gracefully if unavailable
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()

SUMMARY_MAX_LENGTH = EMAIL_SETTINGS.get("SUMMARY_MAX_LENGTH", 300)
AI_SUMMARY_THRESHOLD = EMAIL_SETTINGS.get("AI_SUMMARY_THRESHOLD", 1000)
AI_SUMMARY_MAX_TOKENS = EMAIL_SETTINGS.get("AI_SUMMARY_MAX_TOKENS", 150)


def basic_summarize(text: str, max_length: int = SUMMARY_MAX_LENGTH) -> str:
    """Heuristic-based summarization: returns the first N chars and trims noise."""
    if not text:
        return ""
    # Simple heuristic: collapse whitespace, trim signatures and replies markers
    cleaned = " ".join(text.split())
    # Truncate to max_length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip() + "…"
    return cleaned


def ai_summarize(text: str, system_hint: Optional[str] = None) -> str:
    """AI-powered summarization using OpenAI if configured; otherwise fallback."""
    if not text:
        return ""

    # If text is short, use basic summary
    if len(text) < AI_SUMMARY_THRESHOLD:
        return basic_summarize(text)

    # Use OpenAI client if available and key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI is None or not api_key:
        return basic_summarize(text, max_length=SUMMARY_MAX_LENGTH)

    try:
        client = OpenAI(api_key=api_key)
        messages = []
        if system_hint:
            messages.append({"role": "system", "content": system_hint})
        messages.append({
            "role": "user",
            "content": (
                "Summarize the following email content into a concise, factual "
                "summary capturing key actions, dates, amounts, and obligations.\n\n" + text
            ),
        })
        chat = client.chat.completions.create(
            model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            max_tokens=AI_SUMMARY_MAX_TOKENS,
            messages=messages,
        )
        return chat.choices[0].message.content.strip()
    except Exception:
        # In case of any error, fallback to basic
        return basic_summarize(text, max_length=SUMMARY_MAX_LENGTH)


def summarize_email(subject: str, body: str) -> str:
    """Summarize an email using heuristic or AI based on size."""
    # Combine subject and body for better context
    combined = (subject or "") + "\n\n" + (body or "")
    # Decide summarization path using thresholds
    if len(combined) >= AI_SUMMARY_THRESHOLD:
        return ai_summarize(combined, system_hint="You are summarizing email content for triage.")
    return basic_summarize(combined, max_length=SUMMARY_MAX_LENGTH)