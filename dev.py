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


def git_push(*args) -> None:
    push_cmd = ["git", "push"]
    push_cmd += args
    run(push_cmd)


def get_version() -> None:
    return run(
        ["poetry", "version", "--short", "--no-ansi", "--no-interaction"],
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_tag(message: str = "") -> str:
    """Create a git tag named with the current version number."""
    tag = f"v{get_version()}"
    cmd = ["git", "tag", "-a", tag]
    if message:
        cmd += ["-m", message]
    run(cmd)
    return tag


@cloup.group()
def dev():
    """Development tools for tutor-contrib-recon."""


@dev.command()
@cloup.option("--message")
@cloup.option(
    "--push/--no-push", default=True, help="Push to the remote after committing."
)
@cloup.option(
    "--black/--no-black",
    default=True,
    help="Run 'black' on all sources prior to committing.",
)
@cloup.option_group(
    "Tagging",
    cloup.option(
        "--bump",
        default="",
        help="One of: major, minor, patch, premajor, preminor, prepatch.",
    ),
    cloup.option(
        "--push-tag/--no-push-tag", default=True, help="Push the tag to the remote."
    ),
    cloup.option(
        "--tag-message",
        default="",
        help="The message to include in the tag if using --bump.",
    ),
)
@cloup.argument("files", nargs=-1)
def commit(
    message: str,
    push: bool,
    black: bool,
    bump: str,
    push_tag: bool,
    tag_message: str,
    files: "list[str]",
) -> None:
    """Check your changes into version control. Also formats your code and pushes it to the configured remote by default."""
    if files:
        files = [str(Path(f).resolve()) for f in files]
    else:
        files = [str(Path(".").resolve())]
    if black:
        run_black()
    if bump:
        bump_version(bump)
        toml_file = str(Path("pyproject.toml").resolve())
        if files and toml_file not in files:
            files.append(toml_file)
    git_add(files)
    if bump and not message:
        message = f"[dev bot] Bump to version {get_version()}."
    git_commit(message)
    if bump:
        tag = git_tag(tag_message)
        if push_tag:
            git_push(tag)
    if push:
        git_push()


if __name__ == "__main__":
    dev()
