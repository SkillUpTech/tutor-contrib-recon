"""A custom JSON decoder and associated utilities."""

from json import JSONDecoder
import json
from json.decoder import JSONDecodeError
from pathlib import Path
from tutor_recon.util.string import brief
from typing import Any, TypeVar

MARKER = "$"
ESCAPED_MARKER = MARKER * 2
UNSET_CONST_NAME = "default"

JSON_T = TypeVar("JSON_T", str, int, float, bool, list, dict)
"""A type which can be represented in JSON."""

NOT_SET = object()
"""Indicates that a value is not set."""


def escape(value: JSON_T = None) -> JSON_T:
    """If the value is a string beginning with '$', replace it with '$$'.

    Does not recursively descend into child objects.
    """
    if isinstance(value, str) and value.startswith("$"):
        return "$" + value
    return value


def format_unset(default: JSON_T, include_default=True, max_default_len=35) -> str:
    """Return '$default' with a parenthesized default value optionally added after a space."""
    if include_default:
        default = brief(repr(default), max_len=max_default_len)
        return f"${UNSET_CONST_NAME} ({default})"
    return f"${UNSET_CONST_NAME}"


def raise_decode_error(msg: str) -> None:
    raise JSONDecodeError(msg)


class VJSONDecoder(JSONDecoder):
    """A custom JSON decoder which supports variable expansion along with references to objects in other files.

    Control sequences must occur at the beginning of an encoded string (key or value),
        and are defined as follows:

    `$$`: A single `$` character.
    `$.`: Denotes the beginning of a relative path to anothor .json or .v.json spec to be substituted in its place.
          Always evaluates to an object.
    `$/`: Similar to above, but with an absolute path.
    `$` : Signifies the beginning of a variable name.
          If given as a key, it is added along with its corresponding value to the rendering namespace.
          If given as a value, it is expanded to the corresponding value in the rendering namespace.

    Two-character control sequences are checked before one-character control sequences, and keys are substituted before
    values.

    A special built-in variable, `$default`, when given as a value (optionally followed by any sequence of characters,
    which are ignored), signifies that a keypair should be entirely ignored by the decoder.

    Providing `$default`, or either path sequence, as a key is an error.

    The class can be instantiated with or without support for the relative path control sequence.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, object_hook=self.object_hook, **kwargs)
        self._csm = {
            ESCAPED_MARKER: lambda token, **_: token[1:],
            f"{MARKER}.": lambda *args, **kwargs: raise_decode_error(
                "This decoder does not support relative path references."
            ),
            f"{MARKER}/": self.expand_absolute,
            MARKER: self.handle_variable,
        }  # Stands for "control sequence mapping".

    def expand_absolute(self, value, key=NOT_SET):
        """Load the absolute path given in `value`. The path cannot be in the key.

        It is an error to set `key`. The file pointed to at `value` is assumed to be a
        .v.json-formatted text file.
        """
        assert key is NOT_SET
        with open(value, "r") as f:
            return json.load(f, cls=VJSONDecoder)

    def expand_relative_to(self, location, value, key=NOT_SET):
        """Load the path given in `value` relative to `location`. The path cannot be in the key.

        It is an error to set `key`. The file pointed to at `location / value` is assumed to be
        a .v.json-formatted text file.
        """
        assert key is NOT_SET
        with open(location / value, "r") as f:
            return json.load(f, cls=VJSONDecoder)

    def expand_escaped(self, value, key=NOT_SET):
        """Remove the escape character from the `key` if set, or from the `value` not."""
        if key is NOT_SET:
            return value[1:]
        return key[1:]

    def handle_variable(self, value, key=NOT_SET):
        """Store a value under `key` if `key` is set, otherwise handle a reference in `value`.

        In other words:
        - If `key` is set, `value` is stored under `key` so it can later be referenced.
          `key` is then returned.
        - If `key` is not set, expand the variable reference in in `value` and return the result
          of the expansion.

        If key is not set and value is `$default`, return NOT_SET.
        """
        if key is NOT_SET:
            if value.startswith(f'{MARKER}{UNSET_CONST_NAME}'):
                return NOT_SET
            return self._env[value]
        self._env[key] = value
        return key

    def expand(self, pair: "tuple[str, Any]") -> "tuple[str, Any]":
        """Expand the (key, value) pair as appropriate.

        First expands the key, then the value.
        """
        k, v = pair
        k2, v2 = k[:2], v[:2]
        k1, v1 = k[:1], v[:1]
        if k2 in self._csm:
            k = self._csm[k2](v, key=k)
        elif k1 in self._csm:
            k = self._csm[k1](v, key=k)
        if isinstance(v, str):
            if v2 in self._csm:
                v = self._csm[v2](v)
            elif v1 in self._csm:
                v = self._csm[v1](v)
        elif isinstance(v, dict):
            v = self.object_hook(v)
        return k, v

    def object_hook(self, obj: dict) -> dict:
        gen_expanded = (self.expand(pair) for pair in obj.items())
        return {k: v for k, v in gen_expanded if v is not NOT_SET}


def relative_decoder(location: Path) -> type:

    class FSAwareVJSONDecoder(VJSONDecoder):
        f"""A VJSONDecoder which supports relative file references relative to '{location}'."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            def expand_relative(path, **closure_kwargs):
                f"""Closure which expands the given path relative to '{location}'."""
                return self.expand_relative_to(location, path, **closure_kwargs)
            
            self._csm[MARKER + "."] = expand_relative

    return FSAwareVJSONDecoder    

