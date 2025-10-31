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

# Attachment Processing Settings
ATTACHMENT_SETTINGS = {
    # Maximum attachment size to process (bytes)
    "MAX_SIZE_BYTES": 10 * 1024 * 1024,  # 10 MB
    
    # Supported MIME types
    "SUPPORTED_MIME_TYPES": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # legacy .doc
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel"  # legacy .xls
    ],
    
    # Maximum text length to include from attachments
    "MAX_TEXT_LENGTH": 4000,
    
    # Whether to include attachment text in classification context
    "INCLUDE_IN_CONTEXT": True,
}

# LLM Settings
LLM_SETTINGS = {
    # Use OpenAI GPT-4o-mini instead of Groq
    "CLASSIFICATION_MODEL": "gpt-4o-mini",
    "RESPONSE_MODEL": "gpt-4o-mini",

    "CATEGORIES": ["Wanted Important", "Unwanted Important", "Promotions", "Updates", "Spam"],
}

# Classification Cache Settings
CLASSIFICATION_CACHE_SETTINGS = {
    # Cache file for storing classified emails
    "CACHE_FILE": "cache/classification_cache.json",
    
    # Similarity threshold for cache matching (0.0 to 1.0)
    "SIMILARITY_THRESHOLD": 0.85,
    
    # Maximum number of cached classifications to keep
    "MAX_CACHE_SIZE": 1000,
    
    # TTL for cached classifications in seconds (7 days)
    "CACHE_TTL": 7 * 24 * 3600,
    
    # Whether to use classification caching
    "ENABLED": True,
    
    # Minimum content length to cache (avoid caching very short emails)
    "MIN_CONTENT_LENGTH": 50,
    
    # Maximum content length to compare (truncate very long emails for similarity)
    "MAX_CONTENT_LENGTH": 2000,
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