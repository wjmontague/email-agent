"""
Simple caching utilities for performance optimization
"""
import time
from functools import wraps
from typing import Dict, Any

class SimpleCache:
    """Thread-safe simple cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        if key in self.cache:
            if time.time() < self.cache[key]['expires']:
                return self.cache[key]['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()

# Global cache instance
app_cache = SimpleCache()

def cached(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = app_cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            app_cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
