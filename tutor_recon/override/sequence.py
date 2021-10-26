"""The OverrideSequence container class definition."""

from pathlib import Path
from typing import Optional

from tutor_recon.util import vjson
from tutor_recon.override.override import (
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

    @property
    def claims(self) -> None:
        claim_map = dict()
        for override in self.overrides:
            claim_map.update(override.claims)
        return claim_map

    def to_object(self) -> "dict[str, vjson.VJSON_T]":
        ret = super().to_object()
        ret["overrides"] = [o.to_object() for o in self.overrides]
        return ret

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        for override in self.overrides:
            override.scaffold(tutor_root, recon_root)

    def add_override(self, override: OverrideMixin) -> None:
        self.overrides.append(override)

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Call `override()` element-wise on the sequence."""
        for config in self.overrides:
            config.override(tutor_root, recon_root)

    def remove_where(self, **pairs) -> "list[OverrideMixin]":
        """Remove any child override which matches the given attribute pairs.
        
        Returns a list containing any overrides which were removed.
        """
        removed = []
        for index, child in enumerate(self.overrides):
            if child.match(**pairs):
                removed.append(child)
                del self.overrides[index]
            elif isinstance(child, OverrideSequence):
                removed += child.remove_where(**pairs)
        return removed
