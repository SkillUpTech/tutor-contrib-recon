"""Mixin for objects which can apply overrides to the Tutor environment."""
from abc import ABC, abstractmethod
from pathlib import Path

from tutor_recon.util import vjson


class OverrideMixin(vjson.VJSONSerializableMixin, ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @abstractmethod
    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Apply this override to the tutor environment."""

    @abstractmethod
    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        """Add any defaults and perform any necessary initialization for this object.

        Implementations should be idempotent.
        """
