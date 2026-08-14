"""
Simple TTL cache decorator for small in-process caching used by Streamlit.
Not intended as a replacement for Redis — just reduces repeated network calls
on Streamlit reruns while keeping code dependency-free.
"""

import time
from functools import wraps
from typing import Callable, Any, Dict, Tuple

_CACHE: Dict[Tuple[str, Tuple, Tuple], Tuple[float, Any]] = {}


def ttl_cache(ttl: int = 300):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _CACHE:
                ts, value = _CACHE[key]
                if now - ts < ttl:
                    return value
            value = func(*args, **kwargs)
            _CACHE[key] = (now, value)
            return value
        return wrapper
    return decorator
