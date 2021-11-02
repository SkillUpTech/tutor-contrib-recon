"""Utilities for working with command-line output."""

import sys

from typing import IO, Optional

import click

PLUGIN_STYLED = click.style("recon", fg="magenta")
PLUGIN_TAG = f"[{PLUGIN_STYLED}]"


def emit(
    message: str = "",
    file: Optional[IO] = None,
    nl: bool = True,
    err: bool = False,
    color: Optional[bool] = None,
) -> None:
    """Emit the given string, prefixed with the library's name.

    Additional keywords are identical to `click.echo()`.
    """
    return click.echo(
        message=f"{PLUGIN_TAG} {message}", file=file, nl=nl, err=err, color=color
    )


def emit_warning(message: str, nl: bool = True) -> None:
    """Warn the user about something."""
    return emit(message=f"WARNING: {message}", nl=nl, err=True, color="yellow")


def emit_critical(
    message: str, exit: bool = False, nl: bool = True, exit_code: int = 1
) -> None:
    """Show a serious error message and optionally exit."""
    emit(message=f"ERROR: {message}", nl=nl, color="red", err=True)
    if exit:
        sys.exit(exit_code)
