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

    Note that deserialized objects (`dict`-likes) may or may not be instances of `dict`, but will always be
    recognized as instances of `typing.MutableMapping`.

    Control sequences are two-character sequences which must occur at the beginning of an encoded string,
        and are defined as follows:

    `$$`: A single `$` character. Valid as either a key or value.
    `$+`: Denotes the beginning of a path to another json-formatted file whose contents are to be substituted in its place.
            The path may be absolute or relative. If relative, the path is implcitly appended to `self.location`.
            It is an error to attempt to load a relative path using a decoder initialized with `location=None`.
    `$#`: When given as a value, optionally followed by any sequence of characters (which is ignored), signifies that
          a keypair should be entirely ignored by the decoder.
    `$t`: Specifies the unique type-identifier of a registered VJSON type to which the containing object should
          be deserialized.

    Two additional control sequences are defined for backwards compatibility:
        - `$.`
        - `$/`
    They designated relative and absolute path references, respectively. They are not needed since the type of path
        can simply be inferred. They will automatically be converted to equivalent `$+` sequences currently,
        but support will be removed prior to the 1.0 release.

    Keyword Arguments:
        location: The path to the parent directory of the file being decoded (to allow expansion of relative path
            references). Defaults to `None`.

    **kwargs:
        Passed to `super().__init__()`. The `object_hook` keyword cannot be set since it is used internally.
    """

    def __init__(self, *, location: Optional[Path] = None, **kwargs) -> None:
        super().__init__(object_hook=self.object_hook, **kwargs)
        self.location = location
        kwargs.pop("location", None)
        self._params = kwargs.copy()
        self._csm = {
            MARKER * 2: self.expand_escaped,
            f"{MARKER}#": self.expand_comment,
            f"{MARKER}t": self.expand_custom_type,
            f"{MARKER}+": self.expand_object_reference,
            f"{MARKER}.": self.expand_relative,
            f"{MARKER}/": self.expand_absolute,
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

    def expand_comment(self, value: JSON_T, key: KEY_T = NOTHING) -> IGNORE_T:
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
            return RemoteMapping(remote_reference=path)
        with open(path, "r") as f:
            data = json.load(f, cls=type(self), location=path.parent, **self.params())
        if isinstance(data, VJSONSerializableMixin):
            return data
        return RemoteMapping(remote_reference=path, **data)

    def expand_object_reference(
        self, value: str, key: KEY_T = NOTHING
    ) -> RemoteMapping:
        """Deserialize the object at the path given in `value`."""
        assert key is NOTHING, "Path references are not supported in keys."
        path = Path(value[2:])
        if path.is_absolute():
            return self.load_custom_or_remote(path)
        if self.location is None:
            raise ValueError(
                f"This {type(self)} does not support relative path references. "
                "Instantiate with the `location` parameter to enable them."
            )
        return self.load_custom_or_remote(self.location / path)

    def expand_absolute(self, value: str, key: KEY_T = NOTHING) -> RemoteMapping:
        """Load the absolute path given in `value`. The path cannot be in the key.

        If the file doesn't exist, it is created and initialized with an empty object.

        It is an error to set `key`. The file pointed to at `value` must contain
        a single JSON object (dict).
        """
        assert key is NOTHING, "Absolute path references are not supported in keys."
        path = Path(value[2:])
        if not path.is_absolute():
            path = Path("/") / path
        return self.expand_object_reference(f"{MARKER}+{path}")

    def expand_relative(self, value: str, key: KEY_T = NOTHING) -> RemoteMapping:
        f"""Load the given relative `path`."""
        assert key is NOTHING, "Path references are not supported in keys."
        path = Path(value[2:])
        if path.is_absolute():
            # Remove leading slash i.e. '$./foo' becomes '$+foo', not '$+/foo'.
            path = path.relative_to(Path("/"))
        return self.expand_object_reference(f"{MARKER}+{path}")

    def expand_relative_to(
        self, location: Path, value: JSON_T, key: KEY_T = NOTHING
    ) -> RemoteMapping:
        """Load the path given in `value` relative to `location`. The path cannot be in the key.

        If the file doesn't exist, it is created and initialized with an empty object.

        It is an error to set `key`. The file pointed to by the value must contain a JSON object.
        """
        assert key is NOTHING, "Path references are not supported in keys."
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
