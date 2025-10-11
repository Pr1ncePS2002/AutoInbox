# In llm_utils/classifier.py

import os
from dotenv import load_dotenv
# from groq import Groq
from openai import OpenAI
from llm_utils.summarizer import ai_summarize, summarize_email
from config.settings import LLM_SETTINGS

load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# CLASSIFICATION_MODEL = LLM_SETTINGS.get("CLASSIFICATION_MODEL", "llama-3.1-8b-instant")
# RESPONSE_MODEL = LLM_SETTINGS.get("RESPONSE_MODEL", "llama-3.1-8b-instant")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CLASSIFICATION_MODEL = LLM_SETTINGS.get("CLASSIFICATION_MODEL", "gpt-4o-mini")
RESPONSE_MODEL = LLM_SETTINGS.get("RESPONSE_MODEL", "gpt-4o-mini")


def categorize_email(subject, body):
    try:
        prompt_content = f"""
        You are an email categorization engine. Your task is to classify an email into one of the following categories based on its content:
        - Important: Personal or work-related messages that seem to be from a real person and are not automated.
        - Promotions: Marketing emails, special offers, newsletters.
        - Updates: Notifications, shipping updates, social media alerts, forum digests.
        - Spam: Unsolicited junk mail.

        Analyze the email below and provide ONLY the category name.

        Subject: {subject}
        Body: {body}
        
        CRITICAL INSTRUCTION: Your entire response must be ONLY one of the following single words: Important, Promotions, Updates, Spam.
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_content}],
            model=CLASSIFICATION_MODEL,
            temperature=0.0
        )
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Error categorizing email: {e}")
        return "Updates"

def check_if_reply_needed(subject, body):
    try:
        # This is your highly detailed prompt for checking if a reply is needed
        prompt_content = f"""
        You are a hyper-efficient executive assistant AI. Your sole purpose is to classify incoming emails based on a strict set of rules provided by your user to determine if a personal reply is mandatory.

        Here are the user's exact classification rules:

        **1. Wanted Important:** This category is for any email which requires a direct, personal response.
        **2. Unwanted Important:** This category is for emails that contain important information but DO NOT require a reply.
        
        --- RULES & EXAMPLES ---
        - Emails from recruiters asking for availability are 'Wanted Important'.
        - Emails from colleagues asking for a file or your time are 'Wanted Important'.
        - Security alerts, company newsletters, and order confirmations are 'Unwanted Important'.
        ---

        Analyze the following email based ONLY on these rules.

        Email to Classify:
        Subject: {subject}
        Body: {body}

        CRITICAL INSTRUCTION: Your entire response must be ONLY the words "Wanted Important" or "Unwanted Important". Do not include any other text.
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_content}],
            model=CLASSIFICATION_MODEL,
            temperature=0.0
        )
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Error classifying email importance: {e}")
        return "Unwanted Important"


def generate_response(email_body, use_summary=False):
    # This function remains the same
    try:
        context_text = ""
        if use_summary and len(email_body) > 2000:
            context = ai_summarize(email_body)
            context_text = f"Here's a summary for context:\n{context}\n"

        prompt_content = f"""
        You are an AI assistant. Write a polite and concise response to the following email.
        Do not include signatures. Keep your response professional, friendly, and specific to any questions or requests.

        {context_text}
        Email Body:
        {email_body}

        Your Response:
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_content}],
            model=RESPONSE_MODEL,
        )
        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"⚠️ Error generating response: {e}")
        return "I'm sorry, I couldn’t generate a response."