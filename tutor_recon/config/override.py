"""The OverrideConfig class and subclass definitions."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from tutor_recon.util.misc import (
    recursive_update,
    set_nested,
    walk_dict,
)
from tutor_recon.util.vjson import (
    VJSONEncoder,
    format_unset,
    VJSONDecoder,
)
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

    def with_new_overrides(
        self, overrides: dict, tutor_root: Path, recon_root: Path
    ) -> dict:
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
            json.dump(
                complete,
                f,
                indent=4,
                cls=VJSONEncoder.make_encoder(override_dir, write_remote_mappings=True),
            )


class TutorOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        return get_complete(tutor_root).copy()

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        update_config(tutor_root, settings=override_settings)


class JSONOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        with open(tutor_root / self.env_path, "r") as f:
            return json.load(f)

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        env = self.load_from_env(tutor_root)
        recursive_update(env, override_settings)
        with open(tutor_root / self.env_path, "w") as f:
            json.dump(env, f)