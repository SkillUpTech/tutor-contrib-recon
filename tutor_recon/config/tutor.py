"""Retrieve environment information from Tutor."""

from pathlib import Path

import tutor

from tutor_recon.util.vjson import escape, format_unset


def get_defaults() -> dict:
    """Retrieve the default tutor configuration settings, unexpanded."""
    return tutor.config.load_defaults()


def get_possible_keys() -> "list[str]":
    """Retrieve all known possible Tutor configuration keys."""
    return get_defaults().keys()


def get_current(tutor_root: Path) -> dict:
    """Retrieve all Tutor configuration values which are currently set."""
    return tutor.config.load_current(tutor_root, defaults=get_defaults())


def get_complete(tutor_root: Path) -> dict:
    """Retrive the environment as it stands, including defaults and substitutions, from Tutor."""
    return tutor.config.load(tutor_root)


def tutor_scaffold(tutor_root: Path) -> dict:
    """Generate a complete dictionary of config values with no variables set.

    Keys have their existing values "hinted".
    """
    return {k: format_unset(v) for k, v in get_complete(tutor_root).items()}


def update_config(tutor_root: Path, settings: dict) -> None:
    tutor.config.save_config_file(
        tutor_root, tutor.config.merge(settings, get_complete())
    )
