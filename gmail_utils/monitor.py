"""
Monitoring utilities for Gmail API usage and quota tracking.
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from config.settings import API_SETTINGS, CACHE_SETTINGS

# Configure logging
logger = logging.getLogger(__name__)

# Constants
QUOTA_FILE = os.path.join(CACHE_SETTINGS["CACHE_DIR"], "api_quota.json")
DAILY_QUOTA = 1000000  # Gmail API default quota units per day
QUOTA_WARNING_THRESHOLD = 0.8  # 80% of quota

class APIQuotaMonitor:
    """Monitor and track Gmail API usage to prevent quota limits."""
    
    def __init__(self):
        """Initialize the quota monitor."""
        os.makedirs(CACHE_SETTINGS["CACHE_DIR"], exist_ok=True)
        self.quota_data = self._load_quota_data()
        
    def _load_quota_data(self):
        """Load quota data from file or initialize if not exists."""
        if os.path.exists(QUOTA_FILE):
            try:
                with open(QUOTA_FILE, 'r') as f:
                    data = json.load(f)
                    # Check if data is for today
                    if data.get('date') != datetime.now().strftime('%Y-%m-%d'):
                        # Reset for new day
                        return self._initialize_quota_data()
                    return data
            except Exception as e:
                logger.error(f"Error loading quota data: {e}")
                return self._initialize_quota_data()
        else:
            return self._initialize_quota_data()
    
    def _initialize_quota_data(self):
        """Initialize new quota data structure."""
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_calls': 0,
            'quota_used': 0,
            'calls_by_type': {},
            'hourly_usage': {str(i): 0 for i in range(24)},
            'errors': 0
        }
        self._save_quota_data(data)
        return data
    
    def _save_quota_data(self, data):
        """Save quota data to file."""
        try:
            with open(QUOTA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quota data: {e}")
    
    def record_api_call(self, call_type, quota_cost=1, success=True):
        """
        Record an API call with its quota cost.
        
        Args:
            call_type (str): Type of API call (e.g., 'messages.list', 'messages.get')
            quota_cost (int): Quota units used by this call
            success (bool): Whether the call was successful
        """
        current_hour = datetime.now().hour
        
        # Update call counts
        self.quota_data['total_calls'] += 1
        self.quota_data['quota_used'] += quota_cost
        
        # Update call type stats
        if call_type not in self.quota_data['calls_by_type']:
            self.quota_data['calls_by_type'][call_type] = {
                'count': 0,
                'quota_used': 0
            }
        self.quota_data['calls_by_type'][call_type]['count'] += 1
        self.quota_data['calls_by_type'][call_type]['quota_used'] += quota_cost
        
        # Update hourly usage
        self.quota_data['hourly_usage'][str(current_hour)] += quota_cost
        
        # Update error count if needed
        if not success:
            self.quota_data['errors'] += 1
        
        # Save updated data
        self._save_quota_data(self.quota_data)
        
        # Check if approaching quota limit
        self._check_quota_warning()
    
    def _check_quota_warning(self):
        """Check if approaching quota limit and log warning."""
        quota_percentage = self.quota_data['quota_used'] / DAILY_QUOTA
        if quota_percentage >= QUOTA_WARNING_THRESHOLD:
            logger.warning(
                f"API QUOTA WARNING: {quota_percentage:.1%} of daily quota used "
                f"({self.quota_data['quota_used']} / {DAILY_QUOTA})"
            )
    
    def get_usage_stats(self):
        """Get current usage statistics."""
        return {
            'date': self.quota_data['date'],
            'total_calls': self.quota_data['total_calls'],
            'quota_used': self.quota_data['quota_used'],
            'quota_percentage': (self.quota_data['quota_used'] / DAILY_QUOTA) * 100,
            'most_used_endpoints': sorted(
                self.quota_data['calls_by_type'].items(),
                key=lambda x: x[1]['quota_used'],
                reverse=True
            )[:5],
            'errors': self.quota_data['errors']
        }
    
    def should_throttle(self):
        """
        Determine if API calls should be throttled based on usage patterns.
        Returns True if throttling is recommended.
        """
        # Check if we're over 90% of quota
        if (self.quota_data['quota_used'] / DAILY_QUOTA) > 0.9:
            return True
            
        # Check if current hour usage is high
        current_hour = str(datetime.now().hour)
        hourly_avg = sum(int(v) for v in self.quota_data['hourly_usage'].values()) / 24
        if int(self.quota_data['hourly_usage'][current_hour]) > hourly_avg * 2:
            return True
            
        return False

# Singleton instance
_quota_monitor = None

def get_quota_monitor():
    """Get the singleton quota monitor instance."""
    global _quota_monitor
    if _quota_monitor is None:
        _quota_monitor = APIQuotaMonitor()
    return _quota_monitor

def track_api_call(call_type, quota_cost=1):
    """
    Decorator to track API calls and their quota usage.
    
    Args:
        call_type (str): Type of API call
        quota_cost (int): Quota units used by this call
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_quota_monitor()
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"API call failed: {call_type} - {e}")
                raise
            finally:
                elapsed = time.time() - start_time
                monitor.record_api_call(call_type, quota_cost, success)
                logger.debug(f"API call: {call_type} - Time: {elapsed:.2f}s - Quota: {quota_cost}")
                
                # Add throttling if needed
                if monitor.should_throttle():
                    delay = API_SETTINGS["API_CALL_DELAY"] * 2
                    logger.info(f"Throttling API calls. Adding delay: {delay}s")
                    time.sleep(delay)
                
        return wrapper
    return decorator