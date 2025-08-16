from openai import OpenAI

client = OpenAI()

def classify_email(subject, body):
    prompt = f"""
    You are an email classifier. Categorize the following email into one of:
    [Important, High Priority (if related to placements), Promotions, Updates, Spam].

    Email:
    Subject: {subject}
    Body: {body}

    Respond with one label only.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    return resp.choices[0].message.content.strip()
