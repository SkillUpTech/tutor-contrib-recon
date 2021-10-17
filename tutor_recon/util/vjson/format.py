"""Utility functions for formatting VJSON strings."""

from typing import MutableMapping

from .custom import VJSON_T
from .constants import JSON_T, NOTHING
from .util import brief


def escape(value: VJSON_T = None) -> JSON_T:
    """If the value is a string beginning with '$', replace it with '$$'.

    Recursively descends into child objects.
    """
    if isinstance(value, str) and value.startswith("$"):
        return "$" + value
    if isinstance(value, MutableMapping):
        return {k: escape(v) for k, v in value.items()}
    return value


def format_unset(default: JSON_T = NOTHING, max_default_len=35) -> str:
    """Return '$#', optionally with a parenthesized default value added after a space."""
    if default is not NOTHING:
        default = brief(repr(default), max_len=max_default_len)
        return f"$# ({default})"
    return f"$#"
