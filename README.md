Gmail Automation with AI

Automate your Gmail workflow using AI-powered agents. This project allows you to categorize emails, draft responses, and manage your inbox efficiently with minimal manual effort.

Features

Automatically categorize incoming emails

Generate draft responses using AI

Label and organize emails

Fully customizable automation rules

Easy integration with Gmail API

Demo

(Optional: Include a GIF or screenshot of your project in action)

Installation

Clone the repository
```
git clone https://github.com/yourusername/gmail-automation.git
cd gmail-automation
```

Create a virtual environment
```
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

Install dependencies
```
pip install -r requirements.txt
```

Set up Gmail API credentials

Go to Google Cloud Console

Enable the Gmail API

Create OAuth 2.0 credentials

Download credentials.json and place it in the project root

Usage

Run the main script:
```
python main.py
```

Follow the on-screen instructions to authenticate with your Gmail account. The AI agent will then start automating your inbox based on the rules you configure.

Configuration

Modify config.json to set your automation preferences

Specify labels, categories, and response templates

Set the AI response model (e.g., GPT-4, GPT-4o-mini)

Dependencies

Python 3.10+

google-api-python-client

google-auth-httplib2

google-auth-oauthlib

Groq (for AI-generated responses)
