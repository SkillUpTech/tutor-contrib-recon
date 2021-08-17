"""The MainConfig class definition and associated utility functions."""

import json
from pathlib import Path
from typing import Optional

from tutor_recon.util.misc import recursive_update
from tutor_recon.util.vjson import (
    RemoteMapping,
    VJSONEncoder,
)
from tutor_recon.config.override import (
    OverrideConfig,
    JSONOverrideConfig,
    TutorOverrideConfig,
)


class MainConfig:
    def __init__(self, configs: "dict[str, OverrideConfig]") -> None:
        self._configs = configs

    def load(self, tutor_root: Path, recon_root: Path) -> dict:
        # FIXME this should really dynamically gather the OverrideConfig objects based on the contents of main.v.json.
        return {
            str(path): RemoteMapping(
                config.recon_path, **config.load_from_env(tutor_root)
            )
            for path, config in self._configs.items()
        }

    def save(
        self,
        tutor_root: Path,
        recon_root: Path,
        override_settings: Optional[dict] = None,
    ) -> None:
        override_settings = override_settings if override_settings else dict()
        env = self.load(tutor_root, recon_root)
        recursive_update(env, override_settings)
        main_path = recon_root / "main.v.json"
        with open(main_path, "w") as f:
            json.dump(
                env,
                f,
                cls=VJSONEncoder.make_encoder(recon_root, write_remote_mappings=True),
                indent=4,
            )

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        for config in self._configs.values():
            config.override(tutor_root, recon_root)


JSON_CONFIG_MAP = {
    "env/apps/openedx/config/cms.env.json": "openedx/cms.env.v.json",
    "env/apps/openedx/config/lms.env.json": "openedx/lms.env.v.json",
}


def get_all_configs() -> "list[OverrideConfig]":
    tutor_config = TutorOverrideConfig(
        recon_path=Path("tutor_config.yml"), env_path=Path("config.yml")
    )
    json_configs = [
        JSONOverrideConfig(recon_path=v, env_path=k) for k, v in JSON_CONFIG_MAP.items()
    ]
    return [tutor_config] + json_configs


def main_config() -> MainConfig:
    config_map = {
        "config.yml": TutorOverrideConfig(
            recon_path=Path("tutor_config.yml"), env_path=Path("config.yml")
        )
    }
    config_map.update(
        {
            k: JSONOverrideConfig(recon_path=Path(v), env_path=Path(k))
            for k, v in JSON_CONFIG_MAP.items()
        }
    )
    return MainConfig(config_map)


def get_all_mappings(tutor_root: str, recon_root: str) -> "list[dict]":
    """Get all configurations with overrides applied, mapped by their `env_path`."""
    return main_config().load(tutor_root, recon_root)


def scaffold_all(tutor_root: str, recon_root: str) -> None:
    main_config().save(tutor_root, recon_root)


def override_all(tutor_root: str, recon_root: str) -> None:
    main_config().override(tutor_root, recon_root)
