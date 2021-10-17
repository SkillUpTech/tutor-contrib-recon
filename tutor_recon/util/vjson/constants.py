from typing import Literal, Union

MARKER = "$"

JSON_T = Union[str, int, float, bool, list, dict]
"""A type which can be represented in JSON."""

NOTHING = object()
"""
Used in place of `None` in this module to indicate a parameter without a value,
since `None` maps to `null`, a valid JSON primitive.
"""

IGNORE = object()
"""
When produced as a value, indicates that the entire keypair should be ignored.
"""

CUSTOM_TYPE = object()
"""
When given as a key, indicates that the value denotes a custom type for the object.
"""

NOTHING_T = Literal[NOTHING]

IGNORE_T = Literal[IGNORE]

CUSTOM_TYPE_T = Literal[CUSTOM_TYPE]

KEY_T = Union[str, NOTHING_T]

POSSIBLE_JSON_T = Union[JSON_T, IGNORE_T]
