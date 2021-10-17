"""The VJSONDecoder definition."""

import json
from json import JSONDecoder
from typing import Optional
from pathlib import Path
from typing import Union

from .constants import (
    IGNORE_T,
    MARKER,
    IGNORE,
    CUSTOM_TYPE,
    CUSTOM_TYPE_T,
    JSON_T,
    KEY_T,
    NOTHING,
)
from .custom import VJSON_T, VJSONSerializableMixin
from .reference import RemoteMapping


class VJSONDecoder(JSONDecoder):
    """A custom JSON decoder which supports references to objects in other files.

    Control sequences are two-character sequences which must occur at the beginning of an encoded string,
        and are defined as follows:

    `$$`: A single `$` character. Valid as either a key or value.
    `$.`: Denotes the beginning of a relative path to anothor .json or .v.json spec whose contents are to be substituted
          in its place. The spec must have a single object at its root. Valid only as a value.
    `$/`: Similar to above, but with an absolute path. Valid only as a value.
    `$#`: When given as a value, optionally followed by any sequence of characters (which is ignored), signifies that
          a keypair should be entirely ignored by the decoder.
    `$t`: Specifies the unique type-identifier of a registered VJSON type to which the containing object should
          be deserialized.

    The class can be instantiated with or without support for the relative path control sequence.

    Keyword arguments:
        location: The path to the file being decoded (to allow expansion of relative path references).
                  Defaults to `None` (attempting to load a `$.` sequence will raise `ValueError`
                  in this case).

    All other positional and keyword arguments are passed to `JSONDecoder.__init__()`.
    The `object_hook` keyword cannot be set since it is used internally.
    """

    def __init__(self, location: Optional[Path] = None, **kwargs) -> None:
        super().__init__(object_hook=self.object_hook, **kwargs)
        self.location = location
        kwargs.pop('location', None)
        self._params = kwargs.copy()
        self._csm = {
            MARKER * 2: self.expand_escaped,
            f"{MARKER}.": self.expand_relative,
            f"{MARKER}/": self.expand_absolute,
            f"{MARKER}#": self.expand_default,
            f"{MARKER}t": self.expand_custom_type,
        }  # Stands for "control sequence mapping".

    def params(self) -> dict:
        """Return a dictionary of all keyword arguments used to instantiate this object apart from `location`."""
        return self._params.copy()

    def object_hook(self, obj: dict) -> dict:
        gen_expanded = (self.expand(pair) for pair in obj.items())
        ret = {k: v for k, v in gen_expanded if v is not IGNORE}
        custom_type = ret.pop(CUSTOM_TYPE, None)
        if custom_type:
            return custom_type.from_object(ret)
        return ret

    def expand_custom_type(
        self, value: JSON_T, key: KEY_T = NOTHING
    ) -> "tuple[CUSTOM_TYPE_T, VJSONSerializableMixin]":
        assert key == f"{MARKER}t"
        return CUSTOM_TYPE, VJSONSerializableMixin.by_type_id(value)

    def expand_default(self, value: JSON_T, key: KEY_T = NOTHING) -> IGNORE_T:
        """Return `IGNORE`."""
        assert key is NOTHING, "'$#' cannot be expanded in a key."
        assert value.startswith(f"{MARKER}#")
        return IGNORE

    def expand_escaped(
        self, value: JSON_T, key: KEY_T = NOTHING
    ) -> "Union[VJSON_T, tuple[KEY_T, VJSON_T]]":
        """Expand an escaped string. Works for either values or keys with values.

        If both are given, expands the key and returns a tuple of the expanded `key` and unchanged `value`.
        """
        if key is NOTHING:
            return value[1:]
        return key[1:], value

    def load_custom_or_remote(self, path: Path) -> VJSON_T:
        """Load the file at `path` as either a custom object or a `RemoteMapping`.

        If the file doesn't exist, it is created and initialized with an empty
        object.

        The file must contain a single JSON object.
        """
        if not path.exists():
            path.parent.mkdir(exist_ok=True, parents=True)
            with open(path, "w") as f:
                json.dump(dict(), fp=f)
            return RemoteMapping(target=path)
        with open(path, "r") as f:
            data = json.load(f, cls=type(self), location=path.parent, **self.params())
        if isinstance(data, VJSONSerializableMixin):
            return data
        return RemoteMapping(target=path, **data)

    def expand_absolute(self, value: str, key: KEY_T = NOTHING) -> RemoteMapping:
        """Load the absolute path given in `value`. The path cannot be in the key.

        If the file doesn't exist, it is created and initialized with an empty object.

        It is an error to set `key`. The file pointed to at `value` is must contain
        a single JSON object.
        """
        assert key is NOTHING, "Absolute path references are not supported in keys."
        path = Path(value[2:])
        return self.load_custom_or_remote(path)

    def expand_relative(self, value: str, key: KEY_T = NOTHING) -> RemoteMapping:
        f"""Load the given relative `path`."""
        assert key is NOTHING, "Relative path references are not supported in keys."
        if not self.location:
            raise ValueError("This decoder does not support relative path references.")
        return self.expand_relative_to(self.location, value, key=key)

    def expand_relative_to(
        self, location: Path, value: JSON_T, key: KEY_T = NOTHING
    ) -> RemoteMapping:
        """Load the path given in `value` relative to `location`. The path cannot be in the key.

        If the file doesn't exist, it is created and initialized with an empty object.

        It is an error to set `key`. The file pointed to by the value must contain a JSON object.
        """
        assert key is NOTHING, "Relative path references are not supported in keys."
        relpath = value[3:]
        path = location / relpath
        return self.load_custom_or_remote(path)

    def expand(self, pair: "tuple[str, JSON_T]") -> "tuple[str, JSON_T]":
        """Expand the (key, value) pair as appropriate.

        First checks the key for a control sequence, then the value.

        Control sequence expansion methods should return only a value if only the `value`
        parameter is provided. Likewise, they should return a tuple of both the expanded
        key and the original value if provided with both the `key` and `value` parameters.
        """
        k, v = pair
        k2 = k[:2]
        if k2 in self._csm:
            k, v = self._csm[k2](v, key=k)
        if isinstance(v, str):
            v2 = v[:2]
            if v2 in self._csm:
                v = self._csm[v2](v)
        elif isinstance(v, dict):
            v = self.object_hook(v)
        return k, v
