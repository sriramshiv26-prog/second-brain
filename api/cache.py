"""Caching layer for API responses and queries."""

import json
from datetime import datetime, timedelta
from typing import Any, Optional
from functools import lru_cache


class CacheManager:
    """In-memory cache manager with TTL support."""

    def __init__(self):
        """Initialize cache manager."""
        self.cache: dict[str, dict] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if datetime.utcnow() > entry["expires_at"]:
            del self.cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL."""
        self.cache[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        }

    def clear(self, pattern: str = None):
        """Clear cache entries matching pattern."""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]

    def stats(self) -> dict:
        """Get cache statistics."""
        valid_entries = sum(
            1
            for entry in self.cache.values()
            if datetime.utcnow() <= entry["expires_at"]
        )
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
        }


# Global cache instance
cache = CacheManager()


def cached(ttl_seconds: int = 300):
    """Decorator to cache function results."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{json.dumps(str(args))}"

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator
