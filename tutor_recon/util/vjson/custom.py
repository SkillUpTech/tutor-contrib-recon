"""Tools for creating custom (de)serializable types."""

from abc import abstractmethod
from pathlib import Path
from typing import Union, TYPE_CHECKING

from .constants import MARKER, JSON_T
from .reference import RemoteMapping

if TYPE_CHECKING:
    # Forward-declare the high-level interface since this module defines VJSON_T.
    # Actual imports are located at the bottom of this file.
    from .functions import dump, load


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target = None

    def __init_subclass__(cls, **kwargs) -> None:
        type_id = getattr(cls, "type_id", None)
        if type_id is not None:
            VJSONSerializableMixin.named_types[type_id] = cls
        return super().__init_subclass__(**kwargs)

    @abstractmethod
    def to_object(self) -> "dict[str, VJSON_T]":
        """Return a dictionary representation of this object.

        The attributes of this dictionary must constitute the complete set of constructor
        keyword parameters needed to recreate this instance (this mixin could be refactored
        to i.e. inherit from `dataclass.dataclass` in the future).

        Implementations must start by calling `super().to_object()` and then
        update the resulting dictionary with their serializable data. This way,
        special attributes added by `VJSONSerializableMixin` is preserved, and the
        type of mapping to use (`RemoteMapping` or `dict`) can be determined dynamically.
        """
        if self._target is not None:
            mapping = RemoteMapping(target=self._target)
        else:
            mapping = dict()
        mapping.update({f"{MARKER}t": self.type_id})
        return mapping

    @classmethod
    def from_object(cls, obj: "dict[str, VJSON_T]") -> "VJSONSerializableMixin":
        """Deserialize the given object and return the new instance of this type."""
        instance = cls(**obj)
        if isinstance(obj, RemoteMapping):
            instance._target = obj.target
        return instance

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
        return load(source=from_, location=from_.parent)


VJSON_T = Union[JSON_T, RemoteMapping, VJSONSerializableMixin]
"""A type which can be represented as a string in the .v.json format."""

from .functions import dump, load
