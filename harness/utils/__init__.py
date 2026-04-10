"""Shared utilities used across the harness."""

from typing import Any, Dict, Optional


def safe_get(dict_obj: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary.

    Why this design: safe_get provides a null-safe way to access dictionary values,
    preventing KeyError exceptions and providing sensible defaults.

    Args:
        dict_obj: The dictionary to access
        key: The key to look up
        default: Default value if key is missing

    Returns:
        The value for the key or the default
    """
    return dict_obj.get(key, default)


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Why this design: deep_merge_dicts recursively merges nested dictionaries,
    useful for combining configuration defaults with overrides.

    Args:
        base: Base dictionary
        update: Dictionary with updates

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
