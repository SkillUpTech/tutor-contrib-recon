"""Path-related utilities."""

from pathlib import Path
from typing import Optional

import click
import cloup


def set_overrides_path(tutor_root: Path, new_path: Path) -> Path:
    """Store a string representation of `new_path` in `tutor_root / '.recon'`.

    Returns:
        The value of `new_path`.
    """
    new_path_str = str(new_path.resolve())
    with open(tutor_root / ".recon", "w") as f:
        f.write(new_path_str)
    return new_path


def overrides_path(tutor_root: Path, env_dir: Optional[Path] = None) -> Path:
    """Get the correct path to the override configuration.

    If `env_dir` is provided, store that path and return it.
    Otherwise, either
        - use the value in the existing `.recon` file if it exists, or
        - create a new `.recon` file, then store and return
          `tutor_root / 'env_overrides'` as the default value.
    """
    tutor_root = Path(tutor_root)
    recon_file = tutor_root / ".recon"
    if env_dir:
        return set_overrides_path(tutor_root, env_dir)
    if recon_file.exists():
        with click.open_file(recon_file, "r") as f:
            custom_path = f.read()
        return Path(custom_path)
    return set_overrides_path(tutor_root, tutor_root / "env_overrides")


def root_dirs(context: cloup.Context) -> "tuple[Path, Path]":
    """Return (tutor_root, recon_root) as determined using the given `Context`."""
    return Path(context.obj.root), overrides_path(context.obj.root)
