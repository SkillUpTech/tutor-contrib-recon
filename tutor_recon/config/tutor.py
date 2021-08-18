"""Retrieve environment information from Tutor."""

from pathlib import Path

import tutor
from tutor.config import load_no_check, save_config_file, merge 
from tutor.config import load_all as tutor_load_all

from tutor_recon.util.vjson import format_unset

def load_all(tutor_root: Path) -> dict:
    """Retrive a tuple of (defaults, current_settings) from tutor."""
    return tutor_load_all(tutor_root.resolve())


def get_defaults(tutor_root: Path) -> dict:
    """Retrieve the default tutor configuration settings, unexpanded."""
    _, defaults = load_all(tutor_root)
    return defaults


def get_possible_keys() -> "list[str]":
    """Retrieve all known possible Tutor configuration keys."""
    return get_defaults().keys()


def get_current(tutor_root: Path) -> dict:
    """Retrieve all Tutor configuration values which are currently set."""
    current, _ = load_all(tutor_root)
    return current


def get_complete(tutor_root: Path) -> dict:
    """Retrive the environment as it stands, including defaults and substitutions, from Tutor."""
    return load_no_check(tutor_root)


def tutor_scaffold(tutor_root: Path) -> dict:
    """Generate a complete dictionary of config values with no variables set.

    Keys have their existing values "hinted".
    """
    return {k: format_unset(v) for k, v in get_complete(tutor_root).items()}


def update_config(tutor_root: Path, settings: dict) -> None:
    current = get_current(tutor_root)
    merge(settings, current)
    save_config_file(
        tutor_root, current
    )
