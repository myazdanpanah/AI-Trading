"""Core utility functions."""
import hashlib
import json
from typing import Any, Dict


def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    key_str = json.dumps(args, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as percentage."""
    return f"{value:.{decimals}f}%"


def calculate_confidence_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Calculate weighted confidence score."""
    if not scores or not weights:
        return 0.0
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(scores.get(k, 0) * weights.get(k, 0) for k in scores)
    return weighted_sum / total_weight
