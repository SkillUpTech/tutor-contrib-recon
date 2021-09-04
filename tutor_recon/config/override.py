"""Mixin for objects which can aplly overrides to the Tutor environment."""
from abc import ABC, abstractclassmethod, abstractmethod
from pathlib import Path
from typing import Any

from tutor_recon.util import vjson


class OverrideMixin(ABC):
    def __init__(self, src: Any, dest: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    @property
    @abstractclassmethod
    def label(cls) -> str:
        """Return a unique string which identifies the type of this object."""

    @abstractclassmethod
    def default(cls, dest: Path) -> "OverrideMixin":
        """Return the default instance for an override of the given `dest`."""

    @abstractmethod
    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Apply this override to the tutor environment."""

    def to_object(self) -> dict:
        """A VJSON-friendly representation of this object."""
        return {
            "type": self.label,
            "src": self.src,
            "dest": self.dest,
        }

    def save(self, to: Path) -> None:
        """Save this override to the VJSON file at the given path."""
        obj = self.to_object()
        vjson.dump(obj, dest=to, location=to.parent)


def from_object(
    obj: "dict[str, str]", type_map: "dict[str, OverrideMixin]"
) -> "OverrideMixin":
    type_, src, dest = type_map[obj["type"]], obj["src"], obj["dest"]
    return type_(src=src, dest=dest)
