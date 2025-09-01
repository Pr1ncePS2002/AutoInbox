"""
Email summarization utilities to reduce token usage in classification.
"""
import re
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def basic_summarize(text, max_length=300):
    """
    Basic text summarization without API calls.
    Uses simple heuristics to extract the most important parts of an email.
    """
    if not text or len(text) <= max_length:
        return text
    
    # Remove quoted replies (common in emails)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if not line.strip().startswith('>') and not re.match(r'^On .* wrote:$', line.strip()):
            cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # If still too long, extract key sentences
    if len(cleaned_text) > max_length:
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        
        # Prioritize sentences with question marks or important keywords
        important_sentences = []
        for sentence in sentences:
            if '?' in sentence or any(keyword in sentence.lower() for keyword in 
                                     ['urgent', 'important', 'please', 'request', 'need', 'help',
                                      'question', 'deadline', 'asap', 'required']):
                important_sentences.append(sentence)
        
        # Add first and last sentences if not already included
        if sentences and sentences[0] not in important_sentences:
            important_sentences.insert(0, sentences[0])
        if sentences and sentences[-1] not in important_sentences:
            important_sentences.append(sentences[-1])
        
        # If we have important sentences, use them
        if important_sentences:
            summary = ' '.join(important_sentences)
            if len(summary) <= max_length:
                return summary
        
        # If still too long or no important sentences, take first part and last part
        first_part = cleaned_text[:max_length//2]
        last_part = cleaned_text[-max_length//2:]
        return first_part + "..." + last_part
    
    return cleaned_text

def ai_summarize(text, max_tokens=150):
    """
    Use AI to summarize longer emails.
    Only use for emails that are very long to avoid unnecessary API calls.
    """
    # Only use AI summarization for very long emails
    if len(text) < 1000:
        return basic_summarize(text)
    
    prompt = f"""
    Summarize the following email in a concise way that preserves the main points, 
    questions, and requests. Keep your summary under {max_tokens} tokens.
    
    EMAIL:
    {text}
    
    SUMMARY:
    """
    
    try:
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in AI summarization: {e}")
        # Fall back to basic summarization
        return basic_summarize(text)

def summarize_email(subject, body, use_ai=False):
    """
    Summarize an email for classification purposes.
    Combines subject and summarized body to reduce token usage.
    """
    # Subject is usually important, keep it intact
    # For body, use either basic or AI summarization
    if use_ai and len(body) > 1000:
        summarized_body = ai_summarize(body)
    else:
        summarized_body = basic_summarize(body)
    
    return {
        "subject": subject,
        "body": summarized_body
    }