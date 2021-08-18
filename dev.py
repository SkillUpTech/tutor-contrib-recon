#!/usr/bin/env python3
"""Devtools for tutor-contrib-recon."""

import subprocess
from pathlib import Path
from typing import Optional

import click
import cloup

PROGRAM_STYLED = click.style("dev.py", fg="green")
PROGRAM_TAG = f"[{PROGRAM_STYLED}]"


def emit(message: str, *args, **kwargs) -> None:
    """Echo the given message tagged with [dev.py].

    *args and **kwargs are passed to `click.echo`.
    """
    click.echo(f"{PROGRAM_TAG} {message}", *args, **kwargs)


def run(arg_list: "list[str]", *args, **kwargs) -> None:
    """Run the command specified in `arg_list` with `subprocess.run` after first echoing it over stdout.

    *args and **kwargs are passed to `subprocess.run`.
    """
    cmd_str = click.style(" ".join(arg_list), fg="yellow")
    emit(f"Running: {cmd_str}")
    return subprocess.run(arg_list, *args, **kwargs)


def run_black() -> None:
    """Run `black` on all sources."""
    run(["black", str(Path(".").resolve())])


def bump_version(rule: str) -> None:
    """Bump the project version according to `rule` (major, minor, patch, premajor, etc.)."""
    run(["poetry", "version", rule])


def git_add(files: "list[str]") -> None:
    run(["git", "add"] + files)


def git_commit(message: str = "") -> None:
    cmd = ["git", "commit"]
    if message:
        cmd += ["-m", message]
    run(cmd)


def git_push(push_tags=False) -> None:
    push_cmd = ["git", "push"]
    if push_tags:
        push_cmd.append("--tags")
    run(push_cmd)


def get_version() -> None:
    return run(
        ["poetry", "version", "--short", "--no-ansi", "--no-interaction"],
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_tag() -> None:
    """Create a git tag named with the current version number."""
    run(["git", "tag", "-a", f"v{get_version()}"])


@cloup.group()
def dev():
    """Development tools for tutor-contrib-recon."""


@dev.command()
@cloup.option("--message")
@cloup.option("--push/--no-push", default=True)
@cloup.option("--push-tags/--no-push-tags", default=True)
@cloup.option("--black/--no-black", default=True)
@cloup.option("--bump", default=None)
@cloup.argument("files", nargs=-1)
def commit(
    message: str,
    push: bool,
    push_tags: bool,
    black: bool,
    bump: Optional[str],
    files: "list[str]",
) -> None:
    """Check your changes into version control. Also formats your code and pushes it to the configured remote by default."""
    if black:
        run_black()
    if bump:
        bump_version(bump)
        if not message:
            message = f"[dev bot] Bump to version {get_version()}."
        git_tag()
    if not files:
        files = [str(Path(".").resolve())]
    else:
        if bump and ("pyproject.toml" not in files):
            files.append("pyproject.toml")
    git_add(files)
    git_commit(message)
    if push:
        git_push(push_tags)


if __name__ == "__main__":
    dev()
