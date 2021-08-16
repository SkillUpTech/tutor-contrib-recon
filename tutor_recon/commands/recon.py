"""The Recon CLI definitions."""

import json
from pathlib import Path

import click
import cloup

from tutor_recon.config.main import get_all_mappings, override_all, scaffold_all
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import overrides_path


@cloup.group(
    help="Allows overriding and rendering settings, files, and templates (in their entirety) from a central location."
)
def recon():
    pass


@recon.command(help="Initialize recon.")
@cloup.option(
    "--env-dir",
    help="The path to where your environment override files should (or already do) reside.",
    type=cloup.Path(file_okay=False, path_type=Path),
    default=None,
)
@cloup.option(
    "--reset-location",
    help="Reset the environment overrides directory location to default (has no effect if the directory is already in the default location).",
    is_flag=True,
)
@cloup.pass_obj
def init(context: cloup.Context, env_dir=None, reset_location=False):
    tutor_root = Path(context.root)
    if reset_location:
        overrides_path(tutor_root=tutor_root).unlink(missing_ok=True)
        recon_root = overrides_path(tutor_root=tutor_root)
        emit(f"Set the new environment overrides location to {recon_root}.")
    else:
        recon_root = overrides_path(tutor_root=tutor_root, env_dir=env_dir).resolve()
    scaffold_all(tutor_root, recon_root)
    emit(
        f"You're all set! Your environment overrides can be configured at '{recon_root}'."
    )


@recon.command(help="Echo the location of the config overrides directory over stdout.")
@cloup.pass_obj
def printroot(context: cloup.Context):
    tutor_root = Path(context.root)
    click.echo(overrides_path(tutor_root).resolve())


@recon.command(help="Apply all override settings to the rendered environment.")
@cloup.pass_obj
def save(context: cloup.Context):
    tutor_root = Path(context.root)
    recon_root = overrides_path(tutor_root).resolve()
    override_all(tutor_root, recon_root)


@recon.command(help="Echo all settings, with overrides applied, over stdout in JSON format.")
@cloup.pass_obj
def list(context: cloup.Context):
    tutor_root = Path(context.root)
    recon_root = overrides_path(tutor_root).resolve()
    click.echo(json.dumps(get_all_mappings(tutor_root, recon_root), indent=4))
