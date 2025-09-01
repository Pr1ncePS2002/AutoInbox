# import google.generativeai as genai
# from dotenv import load_dotenv
# import os

# load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# def classify_email(subject, body):
#     model = genai.GenerativeModel("gemini-1.5-flash")
#     prompt = f"""
#     You are an email classifier. Categorize the following email into one of:
#     [Important, High Priority (if related to placements), Promotions, Updates, Spam].

#     Email:
#     Subject: {subject}
#     Body: {body}

#     Respond with one label only.
#     """
#     resp = model.generate_content(prompt)
#     return resp.text.strip()

from groq import Groq
from dotenv import load_dotenv
import os
from llm_utils.summarizer import summarize_email

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_email(subject, body, use_summary=True):
    """
    Classify an email as either "Wanted Important" or "Unwanted Important".
    
    Args:
        subject: Email subject
        body: Email body
        use_summary: Whether to summarize the email before classification
    
    Returns:
        Classification result as string
    """
    # Summarize email if requested to reduce token usage
    if use_summary:
        email_data = summarize_email(subject, body)
        subject = email_data["subject"]
        body = email_data["body"]
    
    prompt = f"""
    You are an email classification assistant.
    Your task is to decide if an email requires a response or not.
    There are ONLY two categories:
    
    1. Wanted Important = The email is important AND requires a reply or action.
       (Example: Client request, colleague asking something, project update requiring confirmation.)
    
    2. Unwanted Important = The email is important but does NOT require a reply.
       (Example: Google security alert, OTP, password reset, system notification, promotional alert.)
    
    Classify the following email into ONE category ONLY: "Wanted Important" or "Unwanted Important".
    
    Email:
    Subject: {subject}
    Body: {body}
    
    Answer only with: Wanted Important OR Unwanted Important
    """
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

def generate_response(email_body, use_summary=False):
    """
    Generate a response to an email.
    
    Args:
        email_body: The body of the email to respond to
        use_summary: Whether to use a summary for context (for very long emails)
    
    Returns:
        Generated response text
    """
    # For response generation, we might want to use AI summarization
    # for very long emails to provide context, but still use the full
    # email for the actual response
    if use_summary and len(email_body) > 2000:
        from llm_utils.summarizer import ai_summarize
        context = ai_summarize(email_body)
        
        prompt = f"""
        You are an AI assistant. Write a polite and concise response to the following email.
        Do not add any signatures.
        Keep your response professional but friendly.
        Address the specific questions or requests in the email.
        If there are multiple questions, address each one.
        
        Here's a summary of the email for context:
        {context}
        
        The full email body is:
        {email_body[:1000]}... [email continues]
        
        Your Response:
        """
    else:
        prompt = f"""
        You are an AI assistant. Write a polite and concise response to the following email.
        Do not add any signatures.
        Keep your response professional but friendly.
        Address the specific questions or requests in the email.
        If there are multiple questions, address each one.
        
        Email Body:
        {email_body}
        
        Your Response:
        """
    
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

def needs_response(subject, body):
    """
    Determine if an email needs a response based on classification.
    Returns True if email needs a response, False otherwise.
    """
    classification = classify_email(subject, body)
    return classification.strip().lower() == "wanted important"