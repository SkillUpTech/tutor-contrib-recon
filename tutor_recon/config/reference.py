"""Override type which holds a reference to an OverrideSequence."""

from pathlib import Path
from tutor_recon.util import vjson
from tutor_recon.config.override import (
    OverrideMixin,
)


class OverrideReference(OverrideMixin):
    type_id = "reference"

    def __init__(self, override: OverrideMixin, **kwargs) -> None:
        super().__init__(**kwargs)
        self.referenced_override = override

    def to_object(self) -> dict:
        obj = super().to_object()
        obj.update({"override": self.referenced_override.to_object()})
        return obj

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        self.referenced_override.scaffold(tutor_root, recon_root)

    def referenced_override(self, tutor_root: Path, recon_root: Path) -> None:
        self.referenced_override.override(tutor_root, recon_root)
