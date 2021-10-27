"""Git-related utilites."""

import json
import os
import re

from contextlib import contextmanager
from pathlib import Path
from subprocess import run
from typing import Optional
from uuid import uuid4

import click

from tutor_recon.override.module import OverrideModule
from tutor_recon.util import vjson

from .cli import emit, emit_critical


@contextmanager
def chdir(to: Path) -> iter:
    """Context manager for entering and exiting a directory."""
    prev = os.getcwd()
    os.chdir(to)
    try:
        yield
    finally:
        os.chdir(prev)


def init_repo(parent_dir: Path, name: str, url: str, push: bool = False) -> None:
    """Create a git repository for a module."""
    module_root = parent_dir / name
    module_root.mkdir(parents=True, exist_ok=True)
    with chdir(module_root):
        with open("README.md", "w") as readme:
            readme.write(f"# {name}\n")
        run(["git", "init"])
        run(["git", "add", "README.md"])
        run(["git", "commit", "-m", "[recon] Create new module repository."])
        run(["git", "branch", "-M", "main"])
        if url:
            run(["git", "remote", "add", "origin", url])
        if push:
            run(["git", "push", "-u", "origin", "main"])


def clone_repo(url: str, to: Path, name: str = "") -> None:
    """Clone a git repository into `to / name` from `url`.

    If `name` is not provided, uses the default name of the repository.
    """
    to.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", url]
    if name:
        cmd.append(name)
    with chdir(to):
        run(cmd)


def pull_repo(loc: Path) -> None:
    """Execute 'git pull' from `loc`."""
    with chdir(loc):
        run(["git", "pull"])


def abort_if_exists(modules_root: Path, module_name: str) -> None:
    """If a module with the given name already exists, alert the user and exit."""
    module_root = modules_root / module_name
    if module_root.exists():
        emit_critical(
            message=f"A module named {module_name} already exists. Did you mean 'update'?",
            exit=True,
        )


def load_info(
    module_dir: Path, nofail=True, defaults: Optional[dict] = None
) -> "dict[str, str]":
    """Load 'module-info.json' from the given path.

    Keyword Arguments:
        nofail: If true, don't fail if the file doesn't exist. Instead, create the file and
            add any provided defaults.
        defaults: Default info to use if the file doesn't exist or is missing attributes.
    """
    info = dict() if defaults is None else defaults
    try:
        with open(module_dir, "r") as f:
            info.update(json.load(fp=f))
    except FileNotFoundError:
        if nofail:
            with open(module_dir, "w") as new_file:
                json.dump(info, fp=new_file)
        else:
            raise
    return info


def add_module(modules_root: Path, git_url: str) -> OverrideModule:
    """Add a module under `modules_root` from the given `git_url`.

    Renames the module according to its `module-info.json` if possible. If the file
    is missing, it is created and default values are added.
    """
    repo_name = uuid4()
    module_dir = modules_root / repo_name
    clone_repo(git_url, to=modules_root, name=repo_name)
    emit(f"Cloned module to {click.style(module_dir, fg='yellow')}.")
    endpoint_name = re.findall(r"([^/]).git", git_url)[0]
    info = load_info(module_dir, defaults=dict(name=endpoint_name, version="unknown"))
    name, version = info["name"], info["version"]
    full_name = f"{name}_{version}"
    abort_if_exists(modules_root, full_name)
    module_dir = module_dir.rename(full_name)
    emit(f"Renamed '{repo_name}' -> '{full_name}'")
    return vjson.load(module_dir / "module.v.json", location=module_dir)
