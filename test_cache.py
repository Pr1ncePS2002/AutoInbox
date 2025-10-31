#!/usr/bin/env python3
"""
Test script for email classification caching functionality.
This script tests the caching system without requiring full Gmail API setup.
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_utils.cache import get_classification_cache

def test_caching_functionality():
    """Test the email classification caching system."""
    print("🧪 Testing Email Classification Caching System")
    print("=" * 50)
    
    # Get cache instance
    cache = get_classification_cache()
    
    # Clear cache for clean test
    cache.clear_cache()
    
    # Test data
    test_emails = [
        {
            "subject": "Meeting Tomorrow",
            "body": "Hi, can we schedule a meeting tomorrow at 2 PM to discuss the project?",
            "expected_category": "Wanted Important"
        },
        {
            "subject": "Re: Meeting Tomorrow", 
            "body": "Hi, can we schedule a meeting tomorrow at 2 PM to discuss the project details?",
            "expected_category": "Wanted Important"  # Should be similar to first email
        },
        {
            "subject": "Newsletter - Weekly Updates",
            "body": "Here are this week's updates from our company. New features, bug fixes, and announcements.",
            "expected_category": "Updates"
        },
        {
            "subject": "Special Offer - 50% Off!",
            "body": "Don't miss out on our amazing sale! Get 50% off all products this weekend only.",
            "expected_category": "Promotions"
        }
    ]
    
    print("1. Testing cache miss (first classification):")
    print("-" * 40)
    
    # First pass - should all be cache misses
    for i, email in enumerate(test_emails, 1):
        print(f"\nEmail {i}: {email['subject']}")
        
        # Check cache (should be empty)
        cached_result = cache.get_cached_classification(email['body'], email['subject'])
        if cached_result:
            print(f"❌ Unexpected cache hit: {cached_result}")
        else:
            print("✅ Cache miss as expected")
        
        # Simulate classification and cache it
        category = email['expected_category']
        cache.cache_classification(email['body'], email['subject'], category, confidence=0.9)
        print(f"📝 Cached classification: {category}")
    
    print(f"\n2. Testing cache hits (second classification):")
    print("-" * 40)
    
    # Second pass - should be cache hits for exact matches
    for i, email in enumerate(test_emails, 1):
        print(f"\nEmail {i}: {email['subject']}")
        
        cached_result = cache.get_cached_classification(email['body'], email['subject'])
        if cached_result:
            print(f"✅ Cache hit: {cached_result['category']} ({cached_result['cache_type']})")
            if cached_result.get('similarity_score'):
                print(f"   Similarity: {cached_result['similarity_score']:.3f}")
        else:
            print("❌ Expected cache hit but got miss")
    
    print(f"\n3. Testing similarity matching:")
    print("-" * 40)
    
    # Test similar content (should match first email)
    similar_email = {
        "subject": "Meeting Schedule",
        "body": "Hello, could we arrange a meeting tomorrow around 2 PM for the project discussion?"
    }
    
    print(f"Similar email: {similar_email['subject']}")
    cached_result = cache.get_cached_classification(similar_email['body'], similar_email['subject'])
    
    if cached_result and cached_result.get('cache_type') == 'similarity_match':
        print(f"✅ Similarity match found: {cached_result['category']}")
        print(f"   Similarity score: {cached_result.get('similarity_score', 0):.3f}")
    else:
        print("❌ Expected similarity match but didn't find one")
    
    print(f"\n4. Cache statistics:")
    print("-" * 40)
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print(f"\n🎉 Cache testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_caching_functionality()