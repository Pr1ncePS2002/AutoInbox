# 📌 Title: AutoInbox(AI-Powered Gmail Automation)

## 🧠 Overview

This project is a Python-based system designed to automate various tasks within a Gmail account using the power of AI. It allows users to categorize emails, draft responses, organize their inbox, and perform other Gmail management functions. The system leverages libraries like `langgraph` for building AI workflows, Google API client libraries for interacting with Gmail, and optionally integrates with Groq for advanced AI capabilities. The project includes features for authentication, email retrieval, classification, response generation, and automated inbox management. It prioritizes efficiency, error handling, and compliance with Gmail API usage quotas through caching, rate limiting, and usage tracking.

## ⚙️ Features

*   **Automated Email Categorization:** Uses AI models to classify emails into predefined categories (e.g., "Wanted Important", "Unwanted Important").
*   **AI-Powered Response Generation:** Generates draft responses to emails based on their content, using Groq or other LLMs.
*   **Customizable Automation Rules:** Allows users to define rules for handling emails based on their classification,
                                       such as moving them to specific labels or deleting them.
    
*   **Email Retrieval and Caching:** Efficiently fetches emails from Gmail, with caching to improve performance and reduce API calls.
*   **Gmail API Interaction:** Provides robust functions for interacting with the Gmail API, including moving, deleting, and saving draft emails.
*   **Rate Limiting and Error Handling:** Implements rate limiting, exponential backoff, and retry mechanisms to handle API errors and prevent exceeding quota limits.
*   **Usage Monitoring:** Tracks Gmail API usage to ensure compliance with quota restrictions.
*   **Automated Cleanup:** Offers a daily cleanup workflow to manage emails (e.g., delete old promotions).
*   **Flexible Configuration:** Loads settings from a configuration file (e.g., `config/settings.py`) and environment variables for easy customization.
*   **Batch Operations:** Utilizes batch operations for efficient processing of multiple emails.
*   **Modular Design:** Organized with reusable modules for authentication, API interaction, email processing, and AI integration.

## 🛠️ Installation Steps

1.  **Clone the Repository:**

    ```bash
    git clone "https://github.com/Pr1ncePS2002/AutoInbox"  
    cd AutoInbox>
    ```

2.  **Create a Virtual Environment:**

    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**

    *   **Linux/macOS:**

        ```bash
        source .venv/bin/activate
        ```

    *   **Windows:**

        ```bash
        .venv\Scripts\activate
        ```

4.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt  
    ```

    If no `requirements.txt` exists, install the key dependencies:

    ```bash
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib langgraph google-generativeai python-dotenv pydantic groq
    ```

5.  **Configure Gmail API Credentials:**

    *   Create a `credentials.json` file in the project's root directory.  This file is generated dynamically from environment variables by the authentication module.
    *   Set the following environment variables (using a `.env` file or your system's environment variables):

        *   `CLIENT_ID`: Your Google API client ID.
        *   `CLIENT_SECRET`: Your Google API client secret.
        *   `REDIRECT_URI`: Your Google API redirect URI (e.g., `urn:ietf:wg:oauth:2.0:oob`).

        Example `.env` file:

        ```
        CLIENT_ID=YOUR_CLIENT_ID
        CLIENT_SECRET=YOUR_CLIENT_SECRET
        REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
        OPENAI_API_KEY=YOUR_API_KEY
        GROQ_API_KEY=YOUR_GROQ_API_KEY # Optional, if using Groq
        ```

6.  **Configure Settings:**
    *   Create a `config/settings.py` file and modify the settings to match your preferences.
    *   This file allows you to configure API settings, cache settings, email processing settings, LLM settings, and Gmail label IDs.

## 🚀 How to Run / Usage Instructions

1.  **Run the Main Script:**

    ```bash
    python main.py
    ```

    *   The script will authenticate with your Gmail account, fetch new emails, classify them, and perform actions based on the configured automation rules.
    *   You will be prompted in the terminal to grant access to your Gmail account the first time you run the script.

2.  **Modify Configuration:**

    *   Adjust settings in the `config/settings.py` file to customize email categories, response templates, AI models, and automation preferences.
    *   Update the `.env` file with your API keys and credentials.

3.  **Monitor and Review Logs:**

    *   The script logs API calls and errors to both the console and a log file (specified in the logging configuration).
    *   Regularly review the logs to monitor the system's behavior, identify any issues, and track API usage.

4.  **Available Workflows:**

    *   `process_new_emails`: This workflow is actively invoked. It fetches new emails, classifies them, and routes them to different actions.
    *   `process_existing_emails`: This workflow is commented out and is designed to process existing emails based on a count specified by a command-line argument.
    *   `daily_cleanup`: This workflow is commented out and is designed to be executed daily for cleanup tasks.




