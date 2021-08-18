"""Utilities for working with command-line output."""

from typing import Any, IO, Optional
import click

PLUGIN_STYLED = click.style("recon", fg="magenta")
PLUGIN_TAG = f"[{PLUGIN_STYLED}]"


def emit(
    message: Optional[Any] = "",
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
