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

    def apply_module_hook(
        self, module_root: Path, module_id: str, tutor_root: Path, recon_root: Path
    ) -> None:
        """Hook called when this override is applied from a module.

        The hook may optionally be implemented to mutate the object as needed, for instance
        to adjust a path at runtime.

        Arguments:
            module_root: The path to the module's root directory.
            module_id: The unique name of the module.
            tutor_root: The local `env` directory.
            recon_root: The local `env_overrides` directory.
        """
        return None
