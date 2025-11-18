import hashlib
import time
from typing import Dict, Optional
from ..models.item import ClaimItem, PricingResult


def get_cache_key(item: ClaimItem) -> str:
    """
    Create cache key for similar items

    Args:
        item: ClaimItem to create key for

    Returns:
        MD5 hash string as cache key
    """
    key_fields = f"{item.description}_{item.brand or ''}_{item.condition or ''}"
    return hashlib.md5(key_fields.lower().encode()).hexdigest()


class ItemCache:
    """Simple in-memory cache for pricing results"""

    def __init__(self, ttl: int = 86400):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default 24 hours)
        """
        self.cache: Dict[str, tuple[PricingResult, float]] = {}
        self.ttl = ttl

    def get(self, item: ClaimItem) -> Optional[PricingResult]:
        """
        Get cached result for item

        Args:
            item: ClaimItem to lookup

        Returns:
            PricingResult if cached and not expired, None otherwise
        """
        key = get_cache_key(item)

        if key in self.cache:
            result, timestamp = self.cache[key]

            # Check if expired
            if time.time() - timestamp < self.ttl:
                return result
            else:
                # Remove expired entry
                del self.cache[key]

        return None

    def set(self, item: ClaimItem, result: PricingResult) -> None:
        """
        Cache pricing result for item

        Args:
            item: ClaimItem being cached
            result: PricingResult to cache
        """
        key = get_cache_key(item)
        self.cache[key] = (result, time.time())

    def clear(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)
