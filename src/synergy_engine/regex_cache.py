"""
Regex Pattern Cache for Performance Optimization

This module provides cached regex compilation to avoid recompiling
patterns on every function call. This significantly speeds up synergy
detection by reducing regex compilation overhead.

Usage:
    from src.synergy_engine.regex_cache import search_cached, match_cached

    # Instead of: re.search(r'pattern', text)
    # Use: search_cached(r'pattern', text)
"""

import re
from functools import lru_cache
from typing import Optional, Pattern

# Cache for compiled regex patterns
_pattern_cache = {}


def get_compiled_pattern(pattern: str, flags: int = 0) -> Pattern:
    """
    Get a compiled regex pattern from cache, or compile and cache it.

    Args:
        pattern: The regex pattern string
        flags: Optional regex flags (e.g., re.IGNORECASE)

    Returns:
        Compiled regex pattern object
    """
    cache_key = (pattern, flags)
    if cache_key not in _pattern_cache:
        _pattern_cache[cache_key] = re.compile(pattern, flags)
    return _pattern_cache[cache_key]


def search_cached(pattern: str, text: str, flags: int = 0) -> Optional[re.Match]:
    """
    Perform regex search with cached compiled pattern.

    This is a drop-in replacement for re.search() that caches
    the compiled pattern for better performance.

    Args:
        pattern: The regex pattern string
        text: The text to search in
        flags: Optional regex flags

    Returns:
        Match object if found, None otherwise
    """
    compiled_pattern = get_compiled_pattern(pattern, flags)
    return compiled_pattern.search(text)


def match_cached(pattern: str, text: str, flags: int = 0) -> Optional[re.Match]:
    """
    Perform regex match with cached compiled pattern.

    This is a drop-in replacement for re.match() that caches
    the compiled pattern for better performance.

    Args:
        pattern: The regex pattern string
        text: The text to match
        flags: Optional regex flags

    Returns:
        Match object if found, None otherwise
    """
    compiled_pattern = get_compiled_pattern(pattern, flags)
    return compiled_pattern.match(text)


def findall_cached(pattern: str, text: str, flags: int = 0) -> list:
    """
    Perform regex findall with cached compiled pattern.

    Args:
        pattern: The regex pattern string
        text: The text to search in
        flags: Optional regex flags

    Returns:
        List of all matches
    """
    compiled_pattern = get_compiled_pattern(pattern, flags)
    return compiled_pattern.findall(text)


def clear_pattern_cache():
    """Clear the pattern cache (useful for testing or memory management)"""
    global _pattern_cache
    _pattern_cache.clear()


def get_cache_stats() -> dict:
    """Get statistics about the pattern cache"""
    return {
        'cached_patterns': len(_pattern_cache),
        'cache_size_bytes': sum(len(p.pattern) for p in _pattern_cache.values())
    }
