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

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_email(subject, body):
    prompt = f"""
    You are an email classifier. Categorize the following email into one of:
    [Important, Promotions, Updates, Spam].

    Email:
    Subject: {subject}
    Body: {body}

    Respond with one label only.
    """
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

def generate_response(email_body):
    prompt = f"""
    You are an AI assistant. Write a polite and concise response to the following email.
    Do not add any signatures.

    Email Body:
    {email_body}

    Your Response:
    """
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()