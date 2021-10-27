"""The OverrideConfig class and subclass definitions."""

import json
from abc import ABCMeta, abstractmethod
from pathlib import Path
from tutor_recon.util.misc import flatten_dict

from tutor_recon.util.vjson.util import (
    recursive_update,
    set_nested,
    walk_dict,
)
from tutor_recon.util import vjson

from tutor_recon.override.tutor import update_config, get_complete
from tutor_recon.override.override import OverrideMixin


class OverrideConfig(OverrideMixin, metaclass=ABCMeta):
    """A settings-like override configuration object."""

    def __init__(self, overrides: vjson.VJSON_T, target: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.overrides = overrides
        self.target = target

    @property
    def claims(self) -> dict:
        return flatten_dict(
            self.overrides,
            prefix=[self.target],
            replace_values=True,
            replacement_value=self,
        )

    @abstractmethod
    def load_from_env(self, tutor_root: Path) -> dict:
        """Load this configuration's settings from the current Tutor environment.

        Ideally all possible keys should be present along with their current or default values.
        """

    @abstractmethod
    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        """Update the environment with the given settings."""

    def to_object(self) -> dict:
        obj = super().to_object()
        obj.update(
            {
                "overrides": self.overrides,
                "target": self.target,
            }
        )
        return obj

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        recursive_update(self.overrides, self.get_complete(tutor_root))

    def get_scaffold(self, tutor_root: Path) -> dict:
        """Return a dict mapping (all) possible keys for this config to `'$default'`."""
        env = self.load_from_env(tutor_root)
        ret = dict()
        for key_list, value in walk_dict(env):
            set_nested(ret, key_list, vjson.format_unset(value))
        return ret

    def get_complete(self, tutor_root: Path) -> "list[dict]":
        """Return the full scaffold of this Config with all overrides applied."""
        scaffold = self.get_scaffold(tutor_root)
        recursive_update(scaffold, self.overrides)
        return scaffold

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Apply `self.overrides` to the environment."""
        self.update_env(tutor_root, self.overrides)


class TutorOverrideConfig(OverrideConfig):
    type_id = "tutor"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def load_from_env(self, tutor_root: Path) -> dict:
        return get_complete(tutor_root).copy()

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        update_config(tutor_root, settings=vjson.expand_references(override_settings))


class JSONOverrideConfig(OverrideConfig):
    type_id = "json"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def load_from_env(self, tutor_root: Path) -> dict:
        with open(tutor_root / self.target, "r") as f:
            return json.load(f)

    def update_env(self, tutor_root: Path, override_settings: dict) -> None:
        env = self.load_from_env(tutor_root)
        recursive_update(env, override_settings)
        with open(tutor_root / self.target, "w") as f:
            json.dump(env, f, indent=4)
