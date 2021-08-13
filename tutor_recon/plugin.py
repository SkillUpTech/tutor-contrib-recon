import json
import os
from tutor_recon.config.main import scaffold_all
from tutor_recon.config.tutor import tutor_scaffold
from tutor_recon.util.cli import emit
import pkg_resources
from glob import glob
from pathlib import Path

import click
import cloup

from tutor_recon.util.paths import overrides_path
from tutor_recon.__about__ import __version__

templates = pkg_resources.resource_filename("tutor_recon", "templates")

config = {}

hooks = {}


def patches():
    all_patches = {}
    patches_dir = pkg_resources.resource_filename("tutor_recon", "patches")
    for path in glob(os.path.join(patches_dir, "*")):
        with open(path) as patch_file:
            name = os.path.basename(path)
            content = patch_file.read()
            all_patches[name] = content
    return all_patches


@cloup.group(
    help="Allows overriding and rendering settings, files, and templates (in their entirety) from a central location."
)
def recon():
    pass


command = recon


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
    click.echo(overrides_path(tutor_root=tutor_root).resolve())
