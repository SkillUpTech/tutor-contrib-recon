"""Mixin for objects which can aplly overrides to the Tutor environment."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from tutor_recon.util import vjson


class OverrideMixin(vjson.VJSONSerializableMixin):
    def __init__(self, src: vjson.VJSON_T, dest: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    # def __init_subclass__(cls, **kwargs) -> None:
    #     return super().__init_subclass__(**kwargs)

    @abstractmethod
    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Apply this override to the tutor environment."""

    def to_object(self) -> dict:
        obj = super().to_object()
        obj.update(
            {
                "src": self.src,
                "dest": self.dest,
            }
        )
        return obj

    @classmethod
    def from_object(cls, obj: dict) -> "vjson.VJSONSerializableMixin":
        return cls(src=obj["src"], dest=obj["dest"])
