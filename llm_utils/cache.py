"""
Email Classification Cache Module

This module provides caching functionality for email classification to avoid
redundant LLM API calls by checking content similarity against previously
classified emails.
"""

import json
import os
import time
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from config.settings import CLASSIFICATION_CACHE_SETTINGS


class ClassificationCache:
    """
    Manages caching of email classifications with content similarity matching.
    """
    
    def __init__(self):
        self.cache_file = CLASSIFICATION_CACHE_SETTINGS["CACHE_FILE"]
        self.similarity_threshold = CLASSIFICATION_CACHE_SETTINGS["SIMILARITY_THRESHOLD"]
        self.max_cache_size = CLASSIFICATION_CACHE_SETTINGS["MAX_CACHE_SIZE"]
        self.cache_ttl = CLASSIFICATION_CACHE_SETTINGS["CACHE_TTL"]
        self.enabled = CLASSIFICATION_CACHE_SETTINGS["ENABLED"]
        self.min_content_length = CLASSIFICATION_CACHE_SETTINGS["MIN_CONTENT_LENGTH"]
        self.max_content_length = CLASSIFICATION_CACHE_SETTINGS["MAX_CONTENT_LENGTH"]
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Initialize TF-IDF vectorizer for similarity calculation
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        self._cache_data = self._load_cache()
        self._update_vectorizer()
    
    def _load_cache(self) -> Dict:
        """Load cache data from file."""
        if not os.path.exists(self.cache_file):
            return {"classifications": [], "last_updated": time.time()}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Clean expired entries
                self._clean_expired_entries(data)
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {"classifications": [], "last_updated": time.time()}
    
    def _save_cache(self):
        """Save cache data to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save classification cache: {e}")
    
    def _clean_expired_entries(self, data: Dict):
        """Remove expired cache entries."""
        current_time = time.time()
        data["classifications"] = [
            entry for entry in data["classifications"]
            if current_time - entry.get("timestamp", 0) < self.cache_ttl
        ]
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess email content for similarity comparison."""
        if not content:
            return ""
        
        # Truncate content if too long
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length]
        
        # Clean and normalize text
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'[^\w\s]', ' ', content)  # Remove special characters
        content = content.lower().strip()
        
        return content
    
    def _update_vectorizer(self):
        """Update TF-IDF vectorizer with current cache content."""
        if not self._cache_data["classifications"]:
            return
        
        contents = [
            self._preprocess_content(entry["content"])
            for entry in self._cache_data["classifications"]
        ]
        
        if contents:
            try:
                self.vectorizer.fit(contents)
            except Exception as e:
                print(f"Warning: Failed to update vectorizer: {e}")
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate cosine similarity between two text contents."""
        try:
            processed_content1 = self._preprocess_content(content1)
            processed_content2 = self._preprocess_content(content2)
            
            if not processed_content1 or not processed_content2:
                return 0.0
            
            # Use existing vectorizer or create new one for comparison
            try:
                vectors = self.vectorizer.transform([processed_content1, processed_content2])
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                return float(similarity)
            except:
                # Fallback: create temporary vectorizer for this comparison
                temp_vectorizer = TfidfVectorizer(
                    max_features=500,
                    stop_words='english',
                    lowercase=True
                )
                vectors = temp_vectorizer.fit_transform([processed_content1, processed_content2])
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                return float(similarity)
        except Exception as e:
            print(f"Warning: Similarity calculation failed: {e}")
            return 0.0
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content to enable quick exact matches."""
        processed_content = self._preprocess_content(content)
        return hashlib.md5(processed_content.encode('utf-8')).hexdigest()
    
    def get_cached_classification(self, email_content: str, subject: str = "") -> Optional[Dict]:
        """
        Get cached classification for similar email content.
        
        Args:
            email_content: The email content to classify
            subject: Email subject (optional, used for additional context)
            
        Returns:
            Cached classification dict if similar content found, None otherwise
        """
        if not self.enabled or not email_content:
            return None
        
        # Skip very short content
        if len(email_content) < self.min_content_length:
            return None
        
        # Combine subject and content for comparison
        full_content = f"{subject} {email_content}".strip()
        content_hash = self._generate_content_hash(full_content)
        
        # Check for exact match first (fastest)
        for entry in self._cache_data["classifications"]:
            if entry.get("content_hash") == content_hash:
                print(f"Cache hit: Exact match found for email")
                return {
                    "category": entry["category"],
                    "confidence": entry.get("confidence", 0.9),
                    "cache_type": "exact_match"
                }
        
        # Check for similarity matches
        best_similarity = 0.0
        best_match = None
        
        for entry in self._cache_data["classifications"]:
            similarity = self._calculate_similarity(full_content, entry["content"])
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = entry
        
        if best_match:
            print(f"Cache hit: Similar content found (similarity: {best_similarity:.3f})")
            return {
                "category": best_match["category"],
                "confidence": best_match.get("confidence", 0.9) * best_similarity,
                "cache_type": "similarity_match",
                "similarity_score": best_similarity
            }
        
        return None
    
    def cache_classification(self, email_content: str, subject: str, category: str, confidence: float = 0.9):
        """
        Cache a new email classification.
        
        Args:
            email_content: The email content
            subject: Email subject
            category: Classification category
            confidence: Classification confidence score
        """
        if not self.enabled or not email_content:
            return
        
        # Skip very short content
        if len(email_content) < self.min_content_length:
            return
        
        full_content = f"{subject} {email_content}".strip()
        content_hash = self._generate_content_hash(full_content)
        
        # Check if already cached (avoid duplicates)
        for entry in self._cache_data["classifications"]:
            if entry.get("content_hash") == content_hash:
                return  # Already cached
        
        # Add new cache entry
        cache_entry = {
            "content": full_content,
            "content_hash": content_hash,
            "category": category,
            "confidence": confidence,
            "timestamp": time.time(),
            "subject": subject
        }
        
        self._cache_data["classifications"].append(cache_entry)
        
        # Maintain cache size limit
        if len(self._cache_data["classifications"]) > self.max_cache_size:
            # Remove oldest entries
            self._cache_data["classifications"].sort(key=lambda x: x["timestamp"])
            self._cache_data["classifications"] = self._cache_data["classifications"][-self.max_cache_size:]
        
        # Update vectorizer with new content
        self._update_vectorizer()
        
        # Save to file
        self._cache_data["last_updated"] = time.time()
        self._save_cache()
        
        print(f"Cached classification: {category} (confidence: {confidence:.3f})")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache_data["classifications"]),
            "cache_file": self.cache_file,
            "last_updated": datetime.fromtimestamp(self._cache_data["last_updated"]).isoformat(),
            "enabled": self.enabled,
            "similarity_threshold": self.similarity_threshold
        }
    
    def clear_cache(self):
        """Clear all cached classifications."""
        self._cache_data = {"classifications": [], "last_updated": time.time()}
        self._save_cache()
        print("Classification cache cleared")


# Global cache instance
_cache_instance = None

def get_classification_cache() -> ClassificationCache:
    """Get the global classification cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ClassificationCache()
    return _cache_instance