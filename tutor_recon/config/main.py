"""The MainConfig class definition and associated utility functions."""

import json
from pathlib import Path

from tutor_recon.util import vjson
from tutor_recon.config.templates import TemplateOverride
from tutor_recon.config.configs import (
    JSONOverrideConfig,
    TutorOverrideConfig,
)
from tutor_recon.config.override import (
    OverrideMixin,
    from_object,
)

JSON_CONFIG_MAP = {
    "env/apps/openedx/config/cms.env.json": "openedx/cms.env.v.json",
    "env/apps/openedx/config/lms.env.json": "openedx/lms.env.v.json",
}

OVERRIDE_TYPE_MAP = {
    "tutor": TutorOverrideConfig,
    "json": JSONOverrideConfig,
    "template": TemplateOverride,
}

DEFAULT_OVERRIDES = [
    ('tutor', 'config.yml'),
    ('json', "env/apps/openedx/config/cms.env.json"),
    ('json', "env/apps/openedx/config/lms.env.json"),
]

DEFAULT_MAIN_CONFIG = {
    "overrides": [
        {
            "type": "tutor",
            "dest": "config.yml",
            "src": vjson.RemoteMapping(Path("tutor_config.v.json"))
        },
        {
            "type": "json",
            "dest": "env/apps/openedx/config/cms.env.json",
            "src": vjson.RemoteMapping(Path("openedx/cms.env.v.json"))
        },
        {
            "type": "json",
            "dest": "env/apps/openedx/config/lms.env.json",
            "src": vjson.RemoteMapping(Path("openedx/lms.env.v.json"))
        },
    ],
}


class MainConfig():
    """Container object for `OverrideConfig` instances."""

    def __init__(self) -> None:
        self._overrides = []

    def load(self, recon_root: Path) -> None:
        """Load the main overrides from file."""
        main_path = recon_root / "main.v.json"
        if main_path.exists():
            override_objs = vjson.load(main_path, location=recon_root)["overrides"]
            for obj in override_objs:
                self._overrides.append(from_object(obj, OVERRIDE_TYPE_MAP))
        else:
            main_path.parent.mkdir(exist_ok=True, parents=True)
            with open(main_path, "w") as f:
                json.dump(DEFAULT_MAIN_CONFIG, fp=f)
            self.load(recon_root)

    def add_override(self, override: OverrideMixin) -> None:
        self._overrides.append(override)

    def as_obj(self) -> "dict[str, OverrideMixin]":
        return {
            "overrides": [
                override.to_object(OVERRIDE_TYPE_MAP) for override in self._overrides
            ],
        }

    def save(
        self,
        recon_root: Path,
    ) -> None:
        """Serialize all override data into main.v.json."""
        main_path = recon_root / "main.v.json"
        vjson.dump(self.as_obj(), dest=main_path, location=recon_root)

    def apply(self, tutor_root: Path, recon_root: Path) -> None:
        """Call `override()` on all configs."""
        for config in self._overrides.values():
            config.override(tutor_root, recon_root)


def get_all_configs() -> "list[OverrideMixin]":
    tutor_config = TutorOverrideConfig(
        src=Path("tutor_config.yml"), dest=Path("config.yml")
    )
    json_configs = [
        JSONOverrideConfig(src=v, dest=k) for k, v in JSON_CONFIG_MAP.items()
    ]
    return [tutor_config] + json_configs


def main_config(recon_root: Path) -> MainConfig:
    main = MainConfig()
    main.load(recon_root)
    return main


def scaffold_all(recon_root: str) -> None:
    main_config(recon_root).save(Path(recon_root))


def override_all(tutor_root: str, recon_root: str) -> None:
    tutor_root, recon_root = map(Path, (tutor_root, recon_root))
    main_config(recon_root).apply(tutor_root, recon_root)
