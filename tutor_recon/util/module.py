"""Git-related utilites."""

import json
import os

from contextlib import contextmanager
from pathlib import Path
from subprocess import run

from .cli import emit_critical


@contextmanager
def chdir(to: Path) -> iter:
    prev = os.getcwd()
    os.chdir(to)
    try:
        yield
    finally:
        os.chdir(prev)


def init_repo(parent_dir: Path, name: str, url: str, push: bool = False) -> None:
    module_root = parent_dir / name
    module_root.mkdir(parents=True, exist_ok=True)
    with chdir(module_root):
        run(["git", "init"])
        if url:
            run(["git", "remote", "add", "origin", url])
        if push:
            run(["git", "push", "--set-upstream", "origin", "master"])


def clone_repo(name: str, url: str, to: Path) -> None:
    module_root = to / name
    module_root.mkdir(parents=True, exist_ok=True)
    with chdir(module_root):
        run(["git", "clone", url])


def pull_repo(loc: Path) -> None:
    with chdir(loc):
        run(["git", "pull"])


def abort_if_exists(modules_root: Path, module_name: str) -> None:
    module_root = modules_root / module_name
    if module_root.exists():
        emit_critical(
            message=f"A module named {module_name} already exists. Aborting", exit=True
        )


def load_info(module_path: Path) -> "dict[str, str]":
    with open(module_path, "r") as f:
        return json.load(fp=f)
