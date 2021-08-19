#!/usr/bin/env python3
"""Devtools for tutor-contrib-recon."""

import subprocess
from pathlib import Path

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


def get_git_branch() -> str:
    return run(
        ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


@cloup.group()
def dev():
    """Development tools for tutor-contrib-recon."""


@dev.command()
@cloup.option("-m", "--message", help="The commit message to use.", metavar="MESSAGE")
@cloup.option_group(
    "Remote Updates",
    cloup.option(
        "--push/--no-push", default=True, help="Push to the remote after committing."
    ),
    cloup.option(
        "--set-upstream/--no-set-upstream",
        default=True,
        help="Automatically add the current branch by name to the remote.",
    ),
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
        help="Increment the version number prior to committing.",
        metavar="RULE",
        type=cloup.Choice(
            ["major", "minor", "patch", "premajor", "preminor", "prepatch"]
        ),
    ),
    cloup.option(
        "--tag/--no-tag", default=True, help="Create a tag with the new version."
    ),
    cloup.option(
        "--push-tag/--no-push-tag", default=True, help="Push the tag to the remote."
    ),
    cloup.option(
        "--tag-message",
        default="",
        help="The message to include in the tag if using --bump.",
        metavar="TAG_MESSAGE",
    ),
)
@cloup.argument("files", nargs=-1)
def commit(
    message: str,
    push: bool,
    set_upstream: bool,
    black: bool,
    bump: str,
    tag: bool,
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
        if toml_file not in files:
            files.append(toml_file)
        if not message:
            message = f"[dev bot] Bump to version {get_version()}."
    git_add(files)
    git_commit(message)
    if tag:
        new_tag = git_tag(tag_message)
        if push_tag:
            git_push("origin", new_tag)
    if push:
        push_args = []
        if set_upstream:
            push_args += ["--set-upstream", "origin", get_git_branch()]
        git_push(*push_args)


if __name__ == "__main__":
    dev()
