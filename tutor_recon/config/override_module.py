"""The OverrideModule class definition."""

from pathlib import Path
from typing import MutableMapping, Optional

from tutor_recon.util import vjson
from .override_sequence import OverrideSequence


class OverrideModule(OverrideSequence):
    """A namespaced OverrideSequence."""

    type_id = "override-module"

    def __init__(self, info: MutableMapping, **kwargs) -> None:
        super().__init__(**kwargs)
        self.info = info

    def to_object(self) -> "dict[str, vjson.VJSON_T]":
        ret = super().to_object()
        ret["info"] = self.info
        return ret

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Call `apply_module_hook()` on each override then apply overrides normally."""
        module_id = self.info["name"]
        for override in self.overrides:
            override.apply_module_hook(
                module_root=recon_root / "modules" / module_id,
                module_id=module_id,
                tutor_root=tutor_root,
                recon_root=recon_root,
            )
        super().override(tutor_root, recon_root)
