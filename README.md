Gmail Automation with AI

Automate your Gmail workflow using AI-powered agents. This project allows you to categorize emails, draft responses, and manage your inbox efficiently with minimal manual effort.

FEATURES

Automatically categorize incoming emails

Generate draft responses using AI

Label and organize emails

Fully customizable automation rules

Easy integration with Gmail API

INSTALLATION:
Step 1:
Clone the repository
```
git clone https://github.com/yourusername/gmail-automation.git
cd gmail-automation
```
Step 2:
Create a virtual environment
```
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
Step 3:
Install dependencies
```
pip install -r requirements.txt
```
Step4:
i) Set up Gmail API credentials

ii) Go to Google Cloud Console

iii) Enable the Gmail API

iv) Create OAuth 2.0 credentials

Step 5:
Download credentials.json and place it in the project root

USAGE

Run the main script:
```
python main.py
```

Follow the on-screen instructions to authenticate with your Gmail account. The AI agent will then start automating your inbox based on the rules you configure.

Configuration

Modify config.json to set your automation preferences

Specify labels, categories, and response templates

Set the AI response model (e.g., GPT-4, GPT-4o-mini)

DEPENDENCIES

Python 3.10+

langgraph

google-api-python-client

google-auth-httplib2

google-auth-oauthlib

Groq (for AI-generated responses)

