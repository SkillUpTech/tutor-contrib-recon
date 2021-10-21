"""Git-related utilites."""

from pathlib import Path
from subprocess import run
from typing import Tuple


def init_repo(name: str, url: str, push: bool = False) -> None:
    pass


def clone_repo(name: str, url: str, to: Path) -> None:
    pass


def pull_repo(loc: Path) -> None:
    pass


def abort_if_exists(module_name: str) -> None:
    pass


def load_info(module_path: Path) -> "dict[str, str]":
    pass
