"""A custom JSON decoder and associated utilities."""

from json import JSONDecoder, JSONEncoder, JSONDecodeError
import json
from pathlib import Path
from tutor_recon.util.misc import WrappedDict, brief
from typing import Any, Literal, Optional, Union

MARKER = "$"
ESCAPED_MARKER = MARKER * 2
UNSET_CONST_NAME = "default"

JSON_T = Union[str, int, float, bool, list, dict]
"""A type which can be represented in JSON."""

NOT_SET = object()
"""
Indicates that a value is not set. 
Used instead of `None` since `None` is a valid JSON value (corresponding to null).
"""

NOT_SET_T = Literal[NOT_SET]

KEY_T = Union[str, NOT_SET_T]


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


class RemoteMapping(WrappedDict):
    """A dict-like type which keeps track of a `Path` to which it should be serialized.

    The path can be relative or absolute--it just needs to be kept as one or the other.
    """

    def __init__(self, target: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.target = target

    @property
    def remote_reference(self) -> str:
        if self.target.is_absolute():
            return f"{MARKER}/{self.target}"
        return f"{MARKER}./{self.target}"

    def expand(self) -> dict:
        return self._dict

    def write(
        self,
        serializer: "type[JSONEncoder]" = JSONEncoder,
        location: Optional[Path] = None,
    ) -> None:
        """Serialize the contents of this mapping to its target."""
        target = self.target
        if not target.is_absolute():
            assert (
                location
            ), f"Cannot write to relative path '{target}' without a location specified."
            target = location / target
        with open(target, "w") as f:
            json.dump(self._dict, f, cls=serializer, indent=4)


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

    Keyword arguments:
        location: The path to the file being decoded (to allow expansion of relative path references).
                  Defaults to `None` (attempting to load a `$.` sequence will raise `JSONDecodeError`
                  in this case).

    All other positional and keyword arguments are passed to `JSONDecoder.__init__()`.
    The `object_hook` keyword cannot be set since it is used internally.
    """

    def __init__(self, *args, location: Optional[Path] = None, **kwargs) -> None:
        super().__init__(*args, object_hook=self.object_hook, **kwargs)
        self.location = location
        self._csm = {
            ESCAPED_MARKER: lambda token, **_: token[1:],
            f"{MARKER}.": self.expand_relative,
            f"{MARKER}/": self.expand_absolute,
            MARKER: self.handle_variable,
        }  # Stands for "control sequence mapping".

    def expand_escaped(self, value: JSON_T, key=NOT_SET) -> str:
        """Expand an escaped string."""
        token = value if key is NOT_SET else key
        assert token.startswith(ESCAPED_MARKER)
        return token[1:]

    def expand_absolute(self, value: str, key=NOT_SET) -> RemoteMapping:
        """Load the absolute path given in `value`. The path cannot be in the key.

        It is an error to set `key`. The file pointed to at `value` is assumed to be a
        .v.json-formatted text file.
        """
        assert key is NOT_SET, "Absolute path references are not supported in keys."
        path = Path(value[2:])
        with open(path, "r") as f:
            return RemoteMapping(path, **json.load(f, cls=type(self)))

    def expand_relative(self, value: str, key=NOT_SET) -> RemoteMapping:
        f"""Load the given relative `path`."""
        assert key is NOT_SET, "Relative path references are not supported in keys."
        if not self.location:
            raise JSONDecodeError(
                "This decoder does not support relative path references."
            )
        return self.expand_relative_to(self.location, value, key=key)

    def expand_relative_to(
        self, location: Path, value: JSON_T, key: KEY_T = NOT_SET
    ) -> RemoteMapping:
        """Load the path given in `value` relative to `location`. The path cannot be in the key.

        It is an error to set `key`. The file pointed to at `location / value` is assumed to be
        a .v.json-formatted text file.
        """
        assert key is NOT_SET, "Relative path references are not supported in keys."
        path = Path(value[2:])
        with open(location / path, "r") as f:
            return RemoteMapping(path, **json.load(f, cls=type(self)))

    def expand_escaped(self, value: JSON_T, key: KEY_T = NOT_SET) -> str:
        """Remove the escape character from the `key` if set, or from the `value` if not."""
        if key is NOT_SET:
            return value[1:]
        return key[1:]

    def handle_variable(
        self, value: JSON_T, key: KEY_T = NOT_SET
    ) -> Union[JSON_T, NOT_SET_T]:
        """Store a value under `key` if `key` is set, otherwise handle a reference in `value`.

        In other words:
        - If `key` is set, `value` is stored under `key` so it can later be referenced.
          `key` is then returned.
        - If `key` is not set, expand the variable reference in in `value` and return the result
          of the expansion.

        If key is not set and value starts with `$default`, return NOT_SET.
        """
        if key is NOT_SET:
            if value.startswith(f"{MARKER}{UNSET_CONST_NAME}"):
                return NOT_SET
            return self._env[value]
        self._env[key] = value
        return key

    def expand(self, pair: "tuple[str, JSON_T]") -> "tuple[str, JSON_T]":
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

    @classmethod
    def relative_decoder(
        cls: "type[VJSONDecoder]", location: Path
    ) -> "type[VJSONDecoder]":
        """Dynamically generate a VJSONDecoder `type` which can expand paths relative to `location`.

        This is useful since the class can be provided as the `cls` argument to `json.load()` and
        `json.loads()`. If VJSONDecoder is passed directly, relative file references will not work,
        since instances are not provided with the path to the file being decoded by the `json` module.
        """

        class RelativeVJSONDecoder(cls):
            f"""A `{cls.__name__}` which supports file references relative to '{location}'."""

            def __init__(self, *args, **kwargs):
                super().__init__(*args, location=location, **kwargs)

        return RelativeVJSONDecoder


class VJSONEncoder(JSONEncoder):
    """Serializer counterpart to `VJSONDecoder`.

    See `VJSONDecoder` for further information.
    """

    def __init__(
        self,
        *args,
        location: Optional[Path] = None,
        write_remote_mappings: bool = False,
        expand_remote_mappings: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.location = location
        self.write_remote_mappings = write_remote_mappings
        self.expand_remote_mappings = expand_remote_mappings

    def default(self, o: Any) -> Any:
        if isinstance(o, RemoteMapping):
            if self.write_remote_mappings:
                o.write(type(self), self.location)
            if self.expand_remote_mappings:
                return o.expand()
            return o.remote_reference
        return super().default(o)

    @classmethod
    def make_encoder(
        cls: "type[VJSONEncoder]",
        location: Path,
        write_remote_mappings: bool = False,
        expand_remote_mappings: bool = False,
    ) -> "type[VJSONEncoder]":
        """Dynamically generate a VJSONEncoder `type` which can expand paths relative to `location`.

        This is useful since the class can be provided as the `cls` argument to `json.dump()` and
        `json.dumps()`. If VJSONEncoder is passed directly, relative file references will not work,
        since instances are not provided with the path to the file being encoded by the `json` module.
        """

        class RelativeVJSONEncoder(cls):
            f"""A `{cls.__name__}` which supports file references relative to '{location}'."""

            def __init__(self, *args, **kwargs):
                super().__init__(
                    *args,
                    location=location,
                    write_remote_mappings=write_remote_mappings,
                    expand_remote_mappings=expand_remote_mappings,
                    **kwargs,
                )

        return RelativeVJSONEncoder
