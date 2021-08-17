"""Tools for working with the main configuration override."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from tutor_recon.util.misc import recursive_update, set_nested, walk_dict
from tutor_recon.util.paths import overrides_path
from typing import Optional

from tutor_recon.util.vjson import RemoteMapping, VJSONEncoder, format_unset, VJSONDecoder
from tutor_recon.config.tutor import update_config, get_complete


class OverrideConfig(ABC):
    """An override configuration object."""

    def __init__(
        self,
        recon_path: Path,
        env_path: Path,
    ) -> None:
        """
        Arguments:
            recon_path: The Path, relative to the recon root, where this configuration's overrides are stored.
            env_path: The Path, relative to the Tutor root, to the final destination of this file.
            serialize: Convert a dictionary of settings into a string representation.
            deserialize: Convert a string into a dictionary of settings.
        """
        self.recon_path = recon_path
        self.env_path = env_path

    @abstractmethod
    def load_from_env(self, tutor_root: Path) -> dict:
        """Load this configuration's settings from the current Tutor environment.

        Ideally all possible keys should be present along with their current or default values.
        """

    @abstractmethod
    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        """Update the environment with the given settings."""

    def get_scaffold(self, tutor_root: Path) -> dict:
        """Return a dict mapping (all) possible keys for this config to `'$default'`."""
        env = self.load_from_env(tutor_root)
        ret = dict()
        for key_list, value in walk_dict(env):
            set_nested(ret, key_list, format_unset(value))
        return ret

    def get_complete(self, tutor_root: Path, recon_root: Path) -> "list[dict]":
        """Return the full scaffold of this Config with all overrides applied."""
        scaffold = self.get_scaffold(tutor_root)
        overrides = self.load_override_config(recon_root)
        recursive_update(scaffold, overrides)
        return scaffold

    def with_new_overrides(self, overrides: dict, tutor_root: Path, recon_root: Path) -> dict:
        """Get the complete configuration dict with the given new overrides also applied."""
        complete = self.get_complete(tutor_root, recon_root)
        recursive_update(complete, overrides)
        return complete

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Apply the override settings to the environment.
        
        To also apply new overrides, first call `write_override_file` with the new settings,
        the call this method.
        """
        self.update_env(tutor_root, self.load_override_config(recon_root))

    def load_override_config(self, recon_root: Path) -> dict:
        """Load the explicitly set override values from the relevant recon override file."""
        override_path = recon_root / self.recon_path
        if not override_path.exists():
            return dict()
        with open(override_path, "r") as f:
            return json.load(f, cls=VJSONDecoder.relative_decoder(override_path.parent))

    def save_override_config(
        self, tutor_root: Path, recon_root: Path, settings: Optional[dict] = None
    ) -> None:
        """Write the .v.json file of this config's scaffold updated with the values in `settings`.

        Non-destructive in the sense that existing override values, if any, will not be lost (unless
        overwritten by a value from the `settings` parameter). To force the file to be overwritten,
        just delete it first and this method will regenerate it.
        """
        if settings is None:
            settings = dict()
        complete = self.with_new_overrides(settings, tutor_root, recon_root)
        override_path = recon_root / self.recon_path
        override_dir = override_path.parent
        override_dir.mkdir(exist_ok=True, parents=True)
        with open(override_path, "w") as f:
            json.dump(complete, f, indent=4, cls=VJSONEncoder.relative_encoder(override_dir))


class TutorOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        return get_complete(tutor_root).copy()

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        env = self.load_from_env(tutor_root)
        recursive_update(env, override_settings)
        update_config(tutor_root, settings=env)


class JSONOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        with open(tutor_root / self.env_path, "r") as f:
            return json.load(f)

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        env = self.load_from_env(tutor_root)
        recursive_update(env, override_settings)
        with open(tutor_root / self.env_path, "w") as f:
            json.dump(env, f)

class MainConfig(OverrideConfig):
    def __init__(self, recon_path: Path, configs: "dict[str, OverrideConfig]") -> None:
        super().__init__(recon_path, None)
        self._configs = configs

    def load_from_env(self, tutor_root: Path) -> dict:
        return {
            config.env_path: RemoteMapping(config.load_from_env(tutor_root)) for config in self._configs.values()
        }

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        for k, v in self._configs.items():
            v.update_env(tutor_root, override_settings.get(k, dict()))


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
        "tutor_config.yml": TutorOverrideConfig(recon_path=Path("tutor_config.yml"), env_path=Path("config.yml"))
    }
    config_map.update({k: JSONOverrideConfig(recon_path=v, env_path=k) for k, v in JSON_CONFIG_MAP.items()})
    return MainConfig("main.v.json", config_map)

def get_all_mappings(tutor_root: str, recon_root: str) -> "list[dict]":
    """Get all configurations with overrides applied, mapped by their `env_path`."""
    return {str(conf.env_path): conf.get_complete(tutor_root, recon_root) for conf in get_all_configs()}
    # return main_config().get_complete(tutor_root, recon_root)


def scaffold_all(tutor_root: str, recon_root: str) -> None:
    # main_config().save_override_config(tutor_root, recon_root)
    for conf in get_all_configs():
        conf.save_override_config(tutor_root, recon_root)


def override_all(tutor_root: str, recon_root: str) -> None:
    # main_config().override(tutor_root, recon_root)
    for conf in get_all_configs():
        conf.override(tutor_root, recon_root)
