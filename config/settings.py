"""
Configuration settings for the Gmail automation system.
Centralized settings to make the system more customizable.
"""

# API and Rate Limiting Settings
API_SETTINGS = {
    # Maximum number of emails to process in one batch
    "MAX_BATCH_SIZE": 50,
    
    # Delay between API calls in seconds
    "API_CALL_DELAY": 0.1,
    
    # Delay between batches in seconds
    "BATCH_DELAY": 1.0,
    
    # Maximum retries for failed API calls
    "MAX_RETRIES": 3,
    
    # Exponential backoff base (in seconds)
    "BACKOFF_BASE": 2,
}

# Cache Settings
CACHE_SETTINGS = {
    # Directory for cache files
    "CACHE_DIR": "cache",
    
    # TTL for email cache in seconds (1 hour)
    "EMAIL_CACHE_TTL": 3600,
    
    # TTL for service cache in seconds (1 hour)
    "SERVICE_CACHE_TTL": 3600,
    
    # TTL for unread emails cache in seconds (5 minutes)
    "UNREAD_CACHE_TTL": 300,
    
    # Whether to use cache for email fetching
    "USE_CACHE": True,
}

# Email Processing Settings
EMAIL_SETTINGS = {
    # Number of days to look back for existing emails
    "DAYS_LOOKBACK": 15,
    
    # Default number of emails to process
    "DEFAULT_EMAIL_COUNT": 5,
    
    # Whether to summarize emails before classification
    "USE_SUMMARIZATION": True,
    
    # Maximum length for basic email summarization
    "SUMMARY_MAX_LENGTH": 300,
    
    # Threshold for using AI summarization (character count)
    "AI_SUMMARY_THRESHOLD": 1000,
    
    # Maximum tokens for AI summarization
    "AI_SUMMARY_MAX_TOKENS": 150,
}

# LLM Settings
LLM_SETTINGS = {
    # Model to use for classification
    "CLASSIFICATION_MODEL": "llama3-8b-8192",
    
    # Model to use for response generation
    "RESPONSE_MODEL": "llama3-8b-8192",
    
    # Classification categories
    "CATEGORIES": ["Wanted Important", "Unwanted Important", "Promotions", "Updates", "Spam"],
}

# Gmail Label IDs
# You can customize these based on your Gmail setup
GMAIL_LABELS = {
    "WANTED_IMPORTANT": "IMPORTANT",
    "UNWANTED_IMPORTANT": "CATEGORY_PERSONAL",
    "PROMOTIONS": "CATEGORY_PROMOTIONS",
    "UPDATES": "CATEGORY_UPDATES",
    "SPAM": "SPAM",
}