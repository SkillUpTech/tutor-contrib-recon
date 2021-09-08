"""A custom JSON decoder and associated utilities."""

from abc import abstractclassmethod, abstractmethod
import json
from json import JSONDecoder, JSONEncoder
from collections import MutableMapping
from typing import Literal, Optional, Union
from pathlib import Path

from tutor_recon.util.misc import WrappedDict, brief, set_nested, walk_dict

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


def escape(value: JSON_T = None) -> JSON_T:
    """If the value is a string beginning with '$', replace it with '$$'.

    Recursively descends into child objects.
    """
    if isinstance(value, str) and value.startswith("$"):
        return "$" + value
    if isinstance(value, MutableMapping):
        return {k: escape(v) for k, v in value.items()}
    return value


def format_unset(default: JSON_T = NOTHING, max_default_len=35) -> str:
    """Return '$-', optionally with a parenthesized default value added after a space."""
    if default is not NOTHING:
        default = brief(repr(default), max_len=max_default_len)
        return f"$- ({default})"
    return f"$-"


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
        write_trailing_newline: bool = True,
    ) -> None:
        """Serialize the contents of this mapping to its target."""
        target = self.target
        if not target.is_absolute():
            assert (
                location
            ), f"Cannot write to relative path '{target}' without a location specified."
            target = location / target
        target.parent.mkdir(exist_ok=True, parents=True)
        with open(target, "w") as f:
            json.dump(self._dict, f, cls=serializer, indent=4)
            if write_trailing_newline:
                f.write("\n")


def expand_mappings(mapping: MutableMapping) -> dict:
    """Recursively expand any remote mappings within `mapping`."""
    ret = dict()
    for keys, val in walk_dict(mapping):
        if isinstance(val, RemoteMapping):
            set_nested(ret, keys, val.expand())
        else:
            set_nested(ret, keys, val)
    return ret


class VJSONDecoder(JSONDecoder):
    """A custom JSON decoder which supports references to objects in other files.

    Control sequences are two-character sequences which must occur at the beginning of an encoded string,
        and are defined as follows:

    `$$`: A single `$` character. Valid as either a key or value.
    `$.`: Denotes the beginning of a relative path to anothor .json or .v.json spec whose contents are to be substituted
          in its place. Valid only as a value.
    `$/`: Similar to above, but with an absolute path. Valid only as a value.
    `$-`: When given as a value, optionally followed by any sequence of characters (which is ignored), signifies that
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

    def __init__(self, *args, location: Optional[Path] = None, **kwargs) -> None:
        super().__init__(*args, object_hook=self.object_hook, **kwargs)
        self.location = location
        self._csm = {
            MARKER * 2: self.expand_escaped,
            f"{MARKER}.": self.expand_relative,
            f"{MARKER}/": self.expand_absolute,
            f"{MARKER}-": self.expand_default,
            f"{MARKER}t": self.expand_custom_type,
        }  # Stands for "control sequence mapping".

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
        assert key is NOTHING, "'$-' cannot be expanded in a key."
        assert value.startswith(f"{MARKER}-")
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

    def expand_absolute(self, value: str, key: KEY_T = NOTHING) -> RemoteMapping:
        """Load the absolute path given in `value`. The path cannot be in the key.

        It is an error to set `key`. The file pointed to at `value` is assumed to be a
        .v.json-formatted text file.
        """
        assert key is NOTHING, "Absolute path references are not supported in keys."
        path = Path(value[2:])
        with open(path, "r") as f:
            return RemoteMapping(path, **json.load(f, cls=type(self)))

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

        It is an error to set `key`. The file pointed to at `location / value` is assumed to be
        a .v.json-formatted text file.
        """
        assert key is NOTHING, "Relative path references are not supported in keys."
        relpath = value[3:]
        path = location / relpath
        data = dict()
        if path.exists():
            with open(location / path, "r") as f:
                data = json.load(f, cls=type(self))
        return RemoteMapping(Path(relpath), **data)

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

    @classmethod
    def make_decoder(cls: "type[VJSONDecoder]", location: Path) -> "type[VJSONDecoder]":
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

    def default(self, o: "VJSON_T") -> JSON_T:
        if isinstance(o, RemoteMapping):
            if self.write_remote_mappings:
                o.write(type(self), self.location)
            if self.expand_remote_mappings:
                return o.expand()
            return o.remote_reference
        if isinstance(o, VJSONSerializableMixin):
            return o.to_object()
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


def load(source: Path, location: Path = None, **kwargs) -> MutableMapping:
    """Load the object stored at `source` using a VJSONDecoder."""
    with open(source, "r") as f:
        return json.load(f, cls=VJSONDecoder.make_decoder(location), **kwargs)


def loads(s: str, location: Path = None, **kwargs) -> MutableMapping:
    """Load the given VJSON-formatted string into a dict."""
    return json.loads(s, cls=VJSONDecoder.make_decoder(location), **kwargs)


def dump(
    obj: "MutableMapping[str, VJSON_T]",
    dest: Path,
    location: Path = None,
    write_remote_mappings: bool = True,
    expand_remote_mappings: bool = False,
    write_trailing_newline: bool = True,
    indent: Optional[int] = 4,
    **kwargs,
) -> None:
    """Dump the given object into the file specified by `dest` using a VJSONEncoder."""
    with open(dest, "w") as f:
        json.dump(
            obj,
            f,
            cls=VJSONEncoder.make_encoder(
                location,
                write_remote_mappings=write_remote_mappings,
                expand_remote_mappings=expand_remote_mappings,
            ),
            indent=indent,
            **kwargs,
        )
        if write_trailing_newline:
            f.write("\n")


def dumps(
    obj: "MutableMapping[str, VJSON_T]",
    location: Path = None,
    expand_remote_mappings: bool = False,
    indent: Optional[int] = 4,
    **kwargs,
) -> str:
    """Dump the given object as a VJSON-formatted string."""
    return json.dumps(
        obj,
        cls=VJSONEncoder.make_encoder(
            location,
            write_remote_mappings=False,
            expand_remote_mappings=expand_remote_mappings,
        ),
        indent=indent,
        **kwargs,
    )


class VJSONSerializableMixin:
    """Mixin for types which define `to_object` and `from_object` methods.

    When subclassing, the `type_id` class attribute may be provided as
    a name to use in the serial representation's `"type"` attribute.

    This associates the string with the new type, thus allowing objects to be reconstructed
    "automagically" from their serial format.

    Inheriting from this mixin is currently the only way to create a custom type which is
    automatically (de)serializable.
    """

    named_types = dict()

    def __init_subclass__(cls, **kwargs) -> None:
        type_id = getattr(cls, "type_id", None)
        if type_id is not None:
            VJSONSerializableMixin.named_types[type_id] = cls
            cls.type_id = type_id
        return super().__init_subclass__(**kwargs)

    @abstractmethod
    def to_object(self) -> "dict[str, VJSON_T]":
        """Return a VJSON-friendly representation of this object as a dict.

        Implementations should generally start by calling `super().to_object()` and then
        updating the resulting dictionary with their serializable data. This way,
        type information added by the VJSONSerializableMixin is preserved.
        """
        return {f"{MARKER}t": self.type_id}

    @abstractclassmethod
    def from_object(cls, obj: "dict[str, VJSON_T]") -> "VJSONSerializableMixin":
        """Deserialize the given object and return the new instance of this type."""

    @classmethod
    def by_type_id(cls, type_id: str) -> "VJSONSerializableMixin":
        """Return the class associated with the given type id."""
        return cls.named_types[type_id]

    def save(self, to: Path, **kwargs) -> None:
        """Save this object to a VJSON file at the given path.

        This implicitly saves any child objects which are provided by `self.to_object`
        so it should only be called once when saving hierarchical types
        (on the object at the top of the hierarchy).

        Extra keyword arguments are passed to `vjson.dump()`.
        """
        obj = self.to_object()
        location = to.parent
        location.mkdir(exist_ok=True, parents=True)
        dump(obj, dest=str(to.resolve()), location=location, **kwargs)

    @classmethod
    def load(cls, from_: Path) -> "VJSONSerializableMixin":
        """Load the object in the vjson file at the given path."""
        return load(from_, from_.parent)


VJSON_T = Union[JSON_T, RemoteMapping, VJSONSerializableMixin]
"""A type which can be represented as a string in the .v.json format."""
