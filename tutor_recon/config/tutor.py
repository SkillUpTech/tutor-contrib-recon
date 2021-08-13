"""Retrieve environment information from Tutor."""

from pathlib import Path

import tutor

from tutor_recon.util.vjson import escape, format_unset

def get_defaults() -> dict:
    """Retrieve the default tutor configuration settings, unexpanded."""
    return tutor.config.load_defaults()

def get_possible_keys() -> 'list[str]':
    """Retrieve all known possible Tutor configuration keys."""
    return get_defaults().keys()

def get_current(tutor_root: Path) -> dict:
    """Retrieve all Tutor configuration values which are currently set."""
    return tutor.config.load_current(tutor_root, defaults=get_defaults())

def current_as_vjson(tutor_root: Path) -> dict:
    """Generate a complete dictionary of config values, with set values set, and unset values marked as such."""
    ret = {
        k: format_unset(v) for k, v in get_defaults()
    }
    current_escaped = {
        k: escape(v) for k, v in get_current(tutor_root)
    }
    ret.update(current_escaped)
    return ret
