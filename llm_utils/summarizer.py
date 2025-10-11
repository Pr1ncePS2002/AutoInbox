import re
import os
from dotenv import load_dotenv
# from groq import Groq
from openai import OpenAI
from config.settings import LLM_SETTINGS, EMAIL_SETTINGS

load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CLASSIFICATION_MODEL = LLM_SETTINGS.get("CLASSIFICATION_MODEL", "gpt-4o-mini")
AI_SUMMARY_MAX_TOKENS = EMAIL_SETTINGS.get("AI_SUMMARY_MAX_TOKENS", 150)

def basic_summarize(text, max_length=300):
    if not text or len(text) <= max_length:
        return text

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if not line.strip().startswith('>') and not re.match(r'^On .* wrote:$', line.strip()):
            cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines)

    if len(cleaned_text) > max_length:
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        important_sentences = [
            s for s in sentences if '?' in s or 
            any(k in s.lower() for k in ['urgent', 'important', 'please', 'request', 'need', 'help', 'question', 'deadline', 'asap', 'required'])
        ]
        if sentences and sentences[0] not in important_sentences:
            important_sentences.insert(0, sentences[0])
        if sentences and sentences[-1] not in important_sentences:
            important_sentences.append(sentences[-1])
        
        summary = ' '.join(important_sentences)
        if len(summary) <= max_length:
            return summary

        first_part = cleaned_text[:max_length // 2]
        last_part = cleaned_text[-max_length // 2:]
        return first_part + "..." + last_part

    return cleaned_text

def ai_summarize(text, max_tokens=AI_SUMMARY_MAX_TOKENS):
    if len(text) < 1000:
        return basic_summarize(text)

    prompt_content = f"""
    Summarize the following email clearly and concisely, preserving the main points,
    questions, and any action items. Keep the summary under {max_tokens} tokens.

    EMAIL:
    {text}

    SUMMARY:
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_content}],
            model=CLASSIFICATION_MODEL,
        )
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Error in AI summarization: {e}")
        return basic_summarize(text)

# In llm_utils/summarizer.py

def summarize_email(subject, body, use_ai=False, max_length=300):
    """
    Summarize an email for classification purposes.
    Combines subject and summarized body to reduce token usage.
    """
    if use_ai and len(body) > 1000:
        summarized_body = ai_summarize(body)
    else:
        # Pass the max_length argument down to the basic summarizer
        summarized_body = basic_summarize(body, max_length=max_length)

    return {
        "subject": subject,
        "body": summarized_body
    }