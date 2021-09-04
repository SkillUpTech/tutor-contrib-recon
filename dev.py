#!/usr/bin/env python3
"""Devtools for tutor-contrib-recon."""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import cloup

PROGRAM_STYLED = click.style("dev.py", fg="green")
PROGRAM_TAG = f"[{PROGRAM_STYLED}]"


class CommandFailure(Exception):
    """The command being run encountered an error."""

    def __init__(self, return_code: int = 1, message: str = ""):
        self.return_code = return_code
        self.message = message
        super().__init__(return_code)


def emit(message: str, *args, **kwargs) -> None:
    """Echo the given message tagged with [dev.py].

    *args and **kwargs are passed to `click.echo`.
    """
    click.echo(f"{PROGRAM_TAG} {message}", *args, **kwargs)


def error_exit(return_code: int = 1, message: str = "") -> None:
    emit(click.style(message, fg="red"))
    sys.exit(return_code)


def run(arg_list: "list[str]", error_on_fail: bool = True, *args, **kwargs) -> None:
    """Run the command specified in `arg_list` with `subprocess.run` after first echoing it over stdout.

    *args and **kwargs are passed to `subprocess.run`.
    """
    cmd_str = click.style(" ".join(arg_list), fg="yellow")
    emit(f"Running: {cmd_str}")
    completed_process = subprocess.run(arg_list, *args, **kwargs)
    if error_on_fail and completed_process.returncode:
        raise CommandFailure(
            completed_process.returncode, f"Command {arg_list} failed."
        )
    return completed_process


def run_black() -> None:
    """Run `black` on all sources."""
    run(["black", str(Path(".").resolve())])


def get_version() -> None:
    return run(
        ["poetry", "version", "--short", "--no-ansi", "--no-interaction"],
        capture_output=True,
        text=True,
    ).stdout.strip()


def bump_version(rule: str) -> None:
    """Bump the project version according to `rule` (major, minor, patch, premajor, etc.)."""
    run(["poetry", "version", rule])


def bump_and_commit(rule: str) -> None:
    """Bump the version according to the rule, then add and commit pyproject.toml."""
    emit(f"Bumping the {rule} version.")
    bump_version(rule)
    git_add("pyproject.toml")
    git_commit(f"[dev bot] Bump to version '{get_version()}'.")


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


def git_fetch(branch_name: str, remote_name: str = "origin") -> None:
    run(["git", "fetch", remote_name, branch_name])


def git_rebase(branch_name: str) -> None:
    run(["git", "rebase", branch_name])


def git_tag(message: str = "") -> str:
    """Create a git tag named with the current version number."""
    tag = f"v{get_version()}"
    cmd = ["git", "tag", "-a", tag]
    if message:
        cmd += ["-m", message]
    run(cmd)
    return tag


def git_checkout(branch_name: str, new: bool = False) -> None:
    cmd = ["git", "checkout"]
    if new:
        cmd.append("-b")
    cmd.append(branch_name)
    run(cmd)


def git_branch(*args) -> None:
    cmd = ["git", "branch"]
    cmd += args
    run(cmd)


def git_merge(*args) -> None:
    cmd = ["git", "merge"]
    cmd += args
    run(cmd)


def get_git_branch() -> str:
    return run(
        ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def ensure_on_branch(branch_name: str) -> str:
    """Exit with an error if not on the given branch; return the current branch's name."""
    current = get_git_branch()
    if current != branch_name:
        error_exit(
            f"You must be on the '{branch_name}' branch to run this command. Check it out first, then try again."
        )
    return current


def ensure_not_on_branches(*branch_names: str) -> str:
    """Exit with an error if on one of the given branches; return the current branch's name."""
    current = get_git_branch()
    if current in branch_names:
        error_exit(f"This action cannot be performed from branch {current}.")
    return current


def prep_pr(bump_rule: str = ""):
    """Rebase the current branch off of dev, optionally increment the version, then checkout dev and merge the feature branch."""
    git_fetch("dev")
    feature_branch = ensure_not_on_branches("main", "dev")
    emit(f"Rebasing {feature_branch} onto dev.")
    git_rebase("dev")
    if bump_rule:
        bump_and_commit(bump_rule)
    emit("Checking out dev.")
    git_checkout("dev")
    emit(
        f"Squashing and merging {feature_branch} into dev. Please describe the change in the text editor that appears."
    )
    git_merge("--squash", feature_branch)
    emit(f"Finished merge. Deleting {feature_branch}.")
    git_branch("-d", feature_branch)
    git_push()
    emit(f"Congratulations! You're ready to create a PR from dev into main.")


def release():
    """Rebase dev onto main, then replace main with dev."""
    git_fetch("main")
    git_rebase("main")
    git_push("origin", "dev:main")


@cloup.group()
def dev():
    """Development tools for tutor-contrib-recon."""


@dev.command()
@cloup.option_group(
    "Commit",
    cloup.option("--commit/--no-commit", help="Create a new commit.", default=True),
    cloup.option(
        "-m", "--message", help="The commit message to use.", metavar="MESSAGE"
    ),
)
@cloup.option_group(
    "Push",
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
    "Release",
    cloup.option(
        "--bump",
        default="",
        help="Increment the version number prior to committing.",
        metavar="RULE",
        type=cloup.Choice(
            [
                "major",
                "minor",
                "patch",
                "premajor",
                "preminor",
                "prepatch",
                "prerelease",
            ]
        ),
    ),
    cloup.option(
        "--tag/--no-tag",
        default=False,
        help="Create a new tag with (updated) version. Off by default.",
    ),
    cloup.option(
        "--push-tag/--no-push-tag",
        default=True,
        help="Push the tag to the remote. On by default; applies only when --tag is used.",
    ),
    cloup.option(
        "--tag-message",
        default="",
        help="The message to include in the new tag. Applies only when --tag is used.",
        metavar="TAG_MESSAGE",
    ),
)
@cloup.argument("files", nargs=-1)
def publish(
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
            message = f"[dev bot] Bump to version '{get_version()}'."
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


@dev.command()
@cloup.argument("name", nargs=1)
def newfeature(name) -> None:
    """Create a new feature branch."""
    ensure_on_branch("dev")
    git_checkout(name, new=True)


@dev.command()
@cloup.argument(
    "bump_rule",
    metavar="RULE",
    type=cloup.Choice(
        ["major", "minor", "patch", "premajor", "preminor", "prepatch", "prerelease"]
    ),
)
def prep_feature_pr() -> None:
    """Prepare the current feature branch for a PR by running black and rebasing onto dev."""
    ensure_not_on_branches("main", "dev")
    prep_pr("")


if __name__ == "__main__":
    try:
        dev()
    except CommandFailure as e:
        error_exit(e.return_code, e.message)
    except SystemExit:
        if not getattr(sys, "ps1", sys.flags.interactive):
            raise  # Don't propagate if running interactively.
