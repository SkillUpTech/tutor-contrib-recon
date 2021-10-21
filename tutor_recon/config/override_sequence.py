"""The OverrideSequence container class definition."""

from pathlib import Path
from typing import Optional

from tutor_recon.util import vjson
from tutor_recon.config.override import (
    OverrideMixin,
)
from tutor_recon.util.constants import DEFAULT_OVERRIDE_SEQUENCE


class OverrideSequence(OverrideMixin):
    """A sequence of override objects which are applied in order."""

    type_id = "override-sequence"

    def __init__(
        self, overrides: "Optional[list[OverrideMixin]]" = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.overrides = overrides if overrides else list()

    @classmethod
    def default(cls, recon_root: Path) -> "OverrideSequence":
        return vjson.loads(DEFAULT_OVERRIDE_SEQUENCE, location=recon_root)

    def to_object(self) -> "dict[str, vjson.VJSON_T]":
        ret = super().to_object()
        ret.update(
            {
                "overrides": [override.to_object() for override in self.overrides],
            }
        )
        return ret

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        for override in self.overrides:
            override.scaffold(tutor_root, recon_root)

    def add_override(self, override: OverrideMixin) -> None:
        self.overrides.append(override)

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Call `override()` on all configs."""
        for config in self.overrides:
            config.override(tutor_root, recon_root)


class OverrideModule(OverrideSequence):
    """A namespaced OverrideSequence."""

    type_id = "module"
