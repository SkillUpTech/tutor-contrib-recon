"""Miscellaneous utility functions."""

from typing import Any, Iterator, Optional
from collections.abc import Mapping, Sequence


def brief(string: str, max_len=20) -> str:
    """Shorten the given string to a maximum length using elipses."""
    if len(string) > max_len:
        return string[: max_len - 3] + "..."
    return string


def walk_dict(
    mapping: Mapping, key_prefix: "Optional[Sequence[str]]" = None
) -> "Iterator[tuple[Sequence[str], Any]]":
    """Recursively walk through the given dict and yield all terminal values.

    Descends into values which are dictionaries/mappings, but not lists.

    Yields:
        (key_sequence, value) where `key_sequence` is the sequence of nested keys in `mapping`
        under which `value` resides.
    """
    for k, v in mapping.items():
        key_seq = [k]
        if key_prefix:
            key_seq = key_prefix + key_seq
        if isinstance(v, Mapping):
            yield from walk_dict(v, key_prefix=key_seq)
        else:
            yield key_seq, v


def set_nested(mapping: Mapping, key_sequence: "Sequence[str]", value: Any) -> None:
    """Set the value in `mapping` under the given sequence of nested keys.

    Sub-mappings are created as instances of the same type as `mapping` if they do not yet exist.
    """
    assert key_sequence, "The sequence of keys cannot be empty."
    if len(key_sequence) == 1:
        mapping[key_sequence[0]] = value
    else:
        first, rest = key_sequence[0], key_sequence[1:]
        if first not in mapping:
            mapping[first] = type(mapping)()
        set_nested(mapping[first], rest, value)


def recursive_update(mapping: Mapping, other: Mapping) -> None:
    """Recursively update `mapping` using the terminal values from `other`.

    Creates sub-mappings if they don't yet exist, but does not destroy existing
    sub-mappings.
    """
    for key_list, value in walk_dict(other):
        set_nested(mapping, key_list, value)
