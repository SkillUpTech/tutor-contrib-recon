#!/usr/bin/env python3
"""Devtools for tutor-contrib-recon."""

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from functools import wraps

import click
import cloup

## CONSTANTS ##

MAIN_BRANCH = "main"
DEV_BRANCH = "dev"
PROGRAM_STYLED = click.style("dev.py", fg="green")
HELP_EXAMPLE = PROGRAM_STYLED + click.style(" COMMAND --help", fg="yellow")
PROJECT_STYLED = click.style("tutor-contrib-recon", fg="magenta")
PROGRAM_DESCRIPTION = f"""
Development tools for {PROJECT_STYLED}.

Use {HELP_EXAMPLE} for help with a particular subcommand."
"""
PROGRAM_TAG = f"[{PROGRAM_STYLED}]"
CONTEXT_SETTINGS = cloup.Context.settings(
    show_default=True,
    formatter_settings=cloup.HelpFormatter.settings(
        max_width=160,
        theme=cloup.HelpTheme(
            heading=cloup.Style(bold=True),
            invoked_command=cloup.Style(fg=cloup.Color.green),
            col1=cloup.Style(fg=cloup.Color.yellow),
        ),
        col2_min_width=99999,  # Force a linear layout.
    ),
)

## OPTION GROUPS ##

version_and_tag_options = cloup.option_group(
    "Version & Tag Options",
    cloup.option(
        "--bump",
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
        "--tag-message",
        help="The message to include in the new tag. Applies only when --tag is used.",
        metavar="MESSAGE",
    ),
    cloup.option(
        "--push-tag/--no-push-tag",
        default=True,
        help="Push the tag to the remote. On by default; applies only when --tag is used.",
    ),
)

commit_options = cloup.option_group(
    "Commit",
    cloup.option("--commit/--no-commit", help="Create a new commit.", default=True),
    cloup.option(
        "-m", "--message", help="The commit message to use.", metavar="MESSAGE"
    ),
    cloup.option(
        "--files",
        "--paths",
        type=list,
        help="The files and/or directories to add prior to committing.",
        default=["."],
        metavar="PATHS",
    ),
)

push_options = cloup.option_group(
    "Push",
    cloup.option(
        "--push/--no-push", default=True, help="Push to the remote repository."
    ),
    cloup.option(
        "--set-upstream/--no-set-upstream",
        default=True,
        help="Automatically add the current branch by name to the remote.",
    ),
)

code_style_options = cloup.option_group(
    "Code Style",
    cloup.option(
        "--black/--no-black",
        default=True,
        help="Run 'black' on all sources prior to committing.",
    ),
)


## OPTION GROUP HANDLERS ##


def handle_release_and_tag(opts: "dict[str, Any]") -> None:
    bump, tag, push_tag, tag_message = map(
        opts.pop, ("bump", "tag", "push_tag", "tag_message")
    )
    current_version = get_version()
    if bump:
        bump_version(bump)
        current_version = get_version()
        git_add(["pyproject.toml"])
        git_commit(f"[dev bot] Bump to v{current_version}.")
    if tag:
        if not tag_message:
            tag_message = f"tutor-contrib-recon v{current_version}"
        new_tag = git_tag(tag_message)
        if push_tag:
            git_push(new_tag)


def handle_push(opts: "dict[str, Any]") -> None:
    push, set_upstream = map(opts.pop, ("push", "set_upstream"))
    if push:
        git_push(set_upstream=set_upstream)


def handle_black(opts: "dict[str, Any]") -> None:
    black = opts.pop("black")
    if black:
        run_black()


def handle_commit(opts: "dict[str, Any]") -> None:
    commit, message, files = map(opts.pop, ("commit", "message", "files"))
    if not files:
        files = ["."]
    if commit:
        git_add(files)
        git_commit(message)


## DECORATORS ##


def assert_all_options_handled(func):
    """Decorate a function which must entirely consume its keyword arguments.

    The keyword arguments are passed via a single named parameter `opts`. Any
    positional arguments are passed on without modification.
    """

    @wraps(func)
    def dec(*args, **kwargs) -> Any:
        func(*args, opts=kwargs)
        assert (
            not kwargs
        ), f"Some keyword arguments were not consumed by {func.__name__}: {kwargs.keys()}"

    return dec


## COMMANDS ##


@cloup.group(context_settings=CONTEXT_SETTINGS, help=PROGRAM_DESCRIPTION)
def dev():
    """The main command group."""


@dev.command()
@commit_options
@push_options
@code_style_options
@version_and_tag_options
@assert_all_options_handled
def publish(opts) -> None:
    """Check your changes into version control. Also formats your code and pushes it to the configured remote by default."""
    handle_black(opts)
    handle_release_and_tag(opts)
    handle_commit(opts)
    handle_push(opts)


@dev.command()
@push_options
@cloup.argument("branch_name", nargs=1, metavar="NAME")
@assert_all_options_handled
def new_feature(opts) -> None:
    """Create a new feature branch based on origin/dev."""
    name = opts.pop("branch_name")
    ensure_on_branch(DEV_BRANCH)
    git_checkout(name, new=True)
    git_fetch("dev")
    git_rebase("dev", remote=True)
    handle_push(opts)


@dev.command()
@version_and_tag_options
@assert_all_options_handled
def merge_feature(opts) -> None:
    """Merge the current feature branch into dev."""
    merge_feature_to_dev()
    handle_release_and_tag(opts)


## UTILITIES ##


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


def run(
    arg_list: "list[str]",
    error_on_fail: bool = True,
    echo: bool = True,
    *args,
    **kwargs,
) -> None:
    """Run the command specified in `arg_list` with `subprocess.run` after first echoing it over stdout.

    *args and **kwargs are passed to `subprocess.run`.
    """
    if echo:
        cmd_str = click.style(" ".join(arg_list), fg="yellow")
        emit(f"Running: {cmd_str}")
    completed_process = subprocess.run(arg_list, *args, **kwargs)
    if error_on_fail and completed_process.returncode:
        raise CommandFailure(
            completed_process.returncode, f"Command {arg_list} failed."
        )
    return completed_process


## MISC HELPER FUNCTIONS ##


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
    git_add(["pyproject.toml"])
    git_commit(f"[dev bot] Bump to v{get_version()}.")


## GIT HELPER FUNCTIONS ##


def git_add(files: "list[str]") -> None:
    run(["git", "add"] + files)


def git_commit(message: str = "") -> None:
    cmd = ["git", "commit"]
    if message:
        cmd += ["-m", message]
    run(cmd)


def git_push(
    id: Optional[str] = None, set_upstream: bool = False, remote_name="origin"
) -> None:
    if id is None:
        id = get_git_branch()
    cmd = ["git", "push"]
    if set_upstream:
        cmd += ["--set-upstream"]
    cmd += [remote_name, id]
    run(cmd)


def git_fetch(branch_name: str, remote_name: str = "origin") -> None:
    run(["git", "fetch", remote_name, branch_name])


def git_rebase(
    branch_name: str, remote: bool = False, remote_name: str = "origin"
) -> None:
    """Rebase the current branch onto `branch_name`.

    `branch_name` is assumed to be a local branch unless `remote` is set to `True`.
    """
    cmd = ["git", "rebase"]
    if remote:
        cmd += [remote_name]
    cmd += [branch_name]
    run(cmd)


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
        ["git", "symbolic-ref", "--short", "HEAD"],
        echo=False,
        capture_output=True,
        text=True,
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
    """Exit with an error if on one of the given branches; return the current branch's name otherwise."""
    current = get_git_branch()
    if current in branch_names:
        error_exit(f"This action cannot be performed from branch {current}.")
    return current


def merge_feature_to_dev():
    """Rebase the current feature branch off of dev then checkout dev and merge the feature branch."""
    git_fetch(DEV_BRANCH)
    feature_branch = ensure_not_on_branches(MAIN_BRANCH, DEV_BRANCH)
    emit(f"Rebasing {feature_branch} onto dev.")
    git_rebase(DEV_BRANCH)
    emit("Checking out dev.")
    git_checkout(DEV_BRANCH)
    emit(
        f"Squashing and merging {feature_branch} into dev. Please describe the change in the text editor that appears."
    )
    git_merge("--squash", feature_branch)
    emit(f"Finished merge.")
    git_add(["."])
    git_commit(f"Squash and merge {feature_branch} into dev.")
    emit(f"Created commit.")
    push_cmd = click.style("git push", fg="yellow")
    delete_cmd = click.style(f"git branch -d {feature_branch}", fg="yellow")
    emit(
        f"Congratulations! You're almost ready to create a PR from {DEV_BRANCH} into {MAIN_BRANCH}."
    )
    emit(f"You will need to run {push_cmd}.")
    emit("Once finished, you're ready to create a pull request via GitHub 🎉🎉")
    emit(f"Use {delete_cmd} to remove the old feature branch locally.")


def release_no_merge():
    """Rebase dev onto main, then replace main with dev.

    NOTE: Planned for future use. Function can be called manually via interactive shell if needed for now.
    """
    git_fetch(MAIN_BRANCH)
    git_rebase(MAIN_BRANCH)
    git_push(f"{DEV_BRANCH}:{MAIN_BRANCH}")


## STARTUP LOGIC ##

if __name__ == "__main__":
    try:
        dev()
    except CommandFailure as e:
        error_exit(e.return_code, e.message)
    except SystemExit:
        # Don't propagate click's automatic SystemExit if running interactively.
        if not getattr(sys, "ps1", sys.flags.interactive):
            raise
