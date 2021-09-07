"""The OverrideConfig class and subclass definitions."""

import json
from abc import abstractmethod
from pathlib import Path

from tutor_recon.util.misc import (
    recursive_update,
    set_nested,
    walk_dict,
)
from tutor_recon.util import vjson

from tutor_recon.config.tutor import update_config, get_complete
from tutor_recon.config.override import OverrideMixin


class OverrideConfig(OverrideMixin):
    """A settings-like override configuration object."""

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
            set_nested(ret, key_list, vjson.format_unset(value))
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
        override_path = recon_root / self.src
        if not override_path.exists():
            return dict()
        return vjson.load(override_path, location=override_path.parent)


class TutorOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        return get_complete(tutor_root).copy()

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        update_config(tutor_root, settings=override_settings)

    @classmethod
    def type_id(cls) -> str:
        return "tutor"


class JSONOverrideConfig(OverrideConfig):
    def load_from_env(self, tutor_root: Path) -> dict:
        with open(tutor_root / self.dest, "r") as f:
            return json.load(f)

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        env = self.load_from_env(tutor_root)
        recursive_update(env, override_settings)
        with open(tutor_root / self.dest, "w") as f:
            json.dump(env, f)

    @classmethod
    def type_id(cls) -> str:
        return "json"
