"""Miscellaneous utility functions."""

from typing import Any, Hashable, Iterator, MutableMapping, Optional
from collections.abc import Mapping, Sequence


def brief(string: str, max_len=20) -> str:
    """Shorten the given string to a maximum length using elipses."""
    if len(string) > max_len:
        return string[: max_len - 3] + "..."
    return string


def walk_dict(
    mapping: Mapping, key_prefix: "Optional[list[Hashable]]" = None
) -> "Iterator[tuple[tuple[Hashable, ...], Any]]":
    """Recursively walk through the given dict and yield all terminal values.

    Descends into values which are dictionaries/mappings, but not lists.

    Arguments:
        mapping: The `Mapping` to flatten.
        key_prefix: A list of keys to front-append to each `key_sequence` generated.

    Yields:
        `(key_sequence, value)` where `key_sequence` is the sequence of nested keys in `mapping`
        under which `value` resides.
    """
    key_prefix = [] if key_prefix is None else key_prefix
    for k, v in mapping.items():
        key_seq = key_prefix + [k]
        if isinstance(v, Mapping):
            yield from walk_dict(v, key_prefix=key_seq)
        else:
            yield key_seq, v


def set_nested(mapping: Mapping, key_sequence: Sequence[str], value: Any) -> None:
    """Set the value in `mapping` under the given sequence of nested keys.

    Sub-mappings are created as instances of `dict` if they do not yet exist.
    """
    assert key_sequence, "The sequence of keys cannot be empty."
    if len(key_sequence) == 1:
        mapping[key_sequence[0]] = value
    else:
        first, rest = key_sequence[0], key_sequence[1:]
        if first not in mapping:
            mapping[first] = dict()
        set_nested(mapping[first], rest, value)


def recursive_update(mapping: Mapping, other: Mapping) -> None:
    """Recursively update `mapping` using the terminal values from `other`.

    Creates sub-mappings if they don't yet exist.
    """
    for key_list, value in walk_dict(other):
        set_nested(mapping, key_list, value)


def flatten_dict(
    mapping: Mapping,
    prefix: Sequence[Hashable] = tuple(),
    replace_values: bool = False,
    replacement_value: Any = None,
) -> dict:
    """Flatten a dictionary as tuples of subkeys mapped to terminal values.

    Arguments:
        mapping: The source dictionary.

    Keyword Arguments:
        prefix: A sequence to prepend to each key tuple.
        replace_values: If set, substitutes all terminal values with `replacement_value`.
        replacement_value: See above. Ignored if `not replace_values`.
    """
    flattened = dict()
    for keys, terminal in walk_dict(mapping, key_prefix=prefix):
        if replace_values:
            terminal = replacement_value
        flattened[tuple(keys)] = terminal
    return flattened


class WrappedDict(MutableMapping):
    """Dict-like object which thinly wraps an underlying dictionary.

    Does *not* satisfy `isinstance(WrappedDict, dict)` -- this is intentional.
    It allows customization of serialization by `json.dump()` and `json.dumps()`,
    since `json` calls a `default` function on unknown types.
    """

    def __init__(self, *args, **kwargs):
        self._dict = dict()
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)
