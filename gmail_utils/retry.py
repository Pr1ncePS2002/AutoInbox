"""
Retry and error handling utilities for Gmail API operations.
"""

import time
import logging
import functools
import random
from googleapiclient.errors import HttpError
from config.settings import API_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gmail_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def exponential_backoff(attempt, base=API_SETTINGS["BACKOFF_BASE"]):
    """Calculate exponential backoff time with jitter."""
    delay = base ** attempt + random.uniform(0, 1)
    return delay

def retry_on_api_error(max_retries=API_SETTINGS["MAX_RETRIES"]):
    """Decorator to retry functions on API errors with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    if e.resp.status in (403, 429):  # Rate limit or quota exceeded
                        if attempt < max_retries:
                            delay = exponential_backoff(attempt)
                            logger.warning(
                                f"Rate limit hit. Retrying in {delay:.2f} seconds. "
                                f"Attempt {attempt + 1}/{max_retries}"
                            )
                            time.sleep(delay)
                        else:
                            logger.error(f"Max retries exceeded for API call: {func.__name__}")
                            raise
                    elif e.resp.status >= 500:  # Server error
                        if attempt < max_retries:
                            delay = exponential_backoff(attempt)
                            logger.warning(
                                f"Server error. Retrying in {delay:.2f} seconds. "
                                f"Attempt {attempt + 1}/{max_retries}"
                            )
                            time.sleep(delay)
                        else:
                            logger.error(f"Max retries exceeded for API call: {func.__name__}")
                            raise
                    else:  # Other errors
                        logger.error(f"API error in {func.__name__}: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
        return wrapper
    return decorator

def safe_api_call(func):
    """Decorator to safely make API calls with proper error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            status = e.resp.status
            if status == 400:
                logger.error(f"Bad request: {e}")
            elif status == 401:
                logger.error(f"Authentication error: {e}")
            elif status == 403:
                logger.error(f"Forbidden. Quota exceeded or insufficient permissions: {e}")
            elif status == 404:
                logger.error(f"Resource not found: {e}")
            elif status == 429:
                logger.error(f"Rate limit exceeded: {e}")
            elif status >= 500:
                logger.error(f"Server error: {e}")
            else:
                logger.error(f"API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    return wrapper

def track_api_usage(func):
    """Decorator to track API usage for monitoring."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # Log API call details
        logger.info(
            f"API Call: {func.__name__} - "
            f"Duration: {elapsed_time:.2f}s"
        )
        return result
    return wrapper