"""The MainConfig class definition and associated utility functions."""

import json
from pathlib import Path

from tutor_recon.util import vjson
from tutor_recon.config.override import (
    OverrideMixin,
)

DEFAULT_MAIN_CONFIG = json.dumps(
    {
        "$t": "main",
        "overrides": [
            {
                "$t": "tutor",
                "dest": "config.yml",
                "src": "$./tutor_config.v.json",
            },
            {
                "$t": "json",
                "dest": "env/apps/openedx/config/cms.env.json",
                "src": "$./openedx/cms.env.v.json",
            },
            {
                "$t": "json",
                "dest": "env/apps/openedx/config/lms.env.json",
                "src": "$./openedx/lms.env.v.json",
            },
        ],
    }
)


class MainConfig(vjson.VJSONSerializableMixin):
    """Container object for `OverrideConfig` instances."""

    type_id = "main"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.overrides = []

    @classmethod
    def default(cls, recon_root: Path) -> "MainConfig":
        return vjson.loads(DEFAULT_MAIN_CONFIG, recon_root)

    @classmethod
    def from_object(cls, obj: dict) -> "vjson.VJSONSerializableMixin":
        instance = cls()
        overrides = obj["overrides"]
        instance.overrides += overrides
        return instance

    def to_object(self) -> "dict[str, vjson.VJSON_T]":
        ret = super().to_object()
        ret.update(
            {
                "overrides": [override.to_object() for override in self.overrides],
            }
        )
        return ret

    def add_override(self, override: OverrideMixin) -> None:
        self.overrides.append(override)

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Call `override()` on all configs."""
        for config in self.overrides:
            config.override(tutor_root, recon_root)


def main_config(recon_root: Path) -> MainConfig:
    main_path = recon_root / "main.v.json"
    if main_path.exists():
        return MainConfig.load(recon_root / "main.v.json")
    return MainConfig.default(recon_root)


def scaffold_all(recon_root: str) -> None:
    main_config(recon_root).save(Path(recon_root / "main.v.json"))


def override_all(tutor_root: str, recon_root: str) -> None:
    tutor_root, recon_root = map(Path, (tutor_root, recon_root))
    main_config(recon_root).override(tutor_root, recon_root)
