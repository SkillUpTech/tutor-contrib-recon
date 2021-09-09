"""The Recon CLI definitions."""

from pathlib import Path
from tutor_recon.config.templates import TemplateOverride

import click
import cloup

from tutor_recon.config.main import (
    main_config,
    override_all,
    scaffold_all,
)
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import overrides_path, root_dirs
from tutor_recon.util import vjson
from tutor_recon.commands.tutor import tutor_config_save

CONFIG_SAVE_STYLED = click.style("tutor config save", fg="blue")
RECON_SAVE_STYLED = click.style("tutor recon save", fg="magenta")


def run_tutor_config_save(context: cloup.Context) -> None:
    emit(f"Running {CONFIG_SAVE_STYLED}.")
    context.invoke(tutor_config_save)


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
    "--tutor/--no-tutor",
    is_flag=True,
    default=True,
    help="Run/don't run 'tutor config save' prior to applying overrides.",
)
@cloup.pass_context
def init(context: cloup.Context, env_dir, tutor):
    tutor_root = Path(context.obj.root)
    recon_root = overrides_path(tutor_root=tutor_root, env_dir=env_dir).resolve()
    if tutor:
        run_tutor_config_save(context)
    scaffold_all(tutor_root, recon_root)
    recon_root_str = click.style(str(recon_root), fg="magenta")
    emit(
        f"You're all set! Your environment overrides can be configured at {recon_root_str} 👍"
    )


@recon.command(help="Echo the location of the config overrides directory over stdout.")
@cloup.pass_context
def printroot(context: cloup.Context):
    _, recon_root = root_dirs(context)
    click.echo(recon_root.resolve())


@recon.command(help="Apply all override settings to the rendered environment.")
@cloup.option(
    "--tutor/--no-tutor",
    is_flag=True,
    default=True,
    help="Run/don't run 'tutor config save' prior to applying overrides.",
)
@cloup.pass_context
def save(context: cloup.Context, tutor):
    tutor_root, recon_root = root_dirs(context)
    if tutor:
        run_tutor_config_save(context)
    emit("Applying overrides.")
    override_all(tutor_root, recon_root)
    emit("Done.")


@recon.command(help="Scaffold an override of a tutor template in its entirety.")
@cloup.argument("path")
@cloup.pass_context
def replace_template(context: cloup.Context, path: str):
    tutor_root, recon_root = root_dirs(context)
    main = main_config(recon_root)
    override = TemplateOverride.for_template(path)
    main.add_override(override)
    override.scaffold(tutor_root, recon_root)
    main.save(recon_root / "main.v.json")
    path_styled = click.style(str(path), fg="blue")
    override_styled = click.style(str(recon_root / override.src), fg="magenta")
    emit(f"Scaffolded {path_styled} at {override_styled} 👍")
    emit(
        f"Change the file to your heart's content, then it will be rendered when you run {RECON_SAVE_STYLED}."
    )


@recon.command(help="Print the current recon configuration as JSON.")
@cloup.pass_context
def list(context: cloup.Context):
    _, recon_root = root_dirs(context)
    main = main_config(recon_root)
    config_str = vjson.dumps(main, expand_remote_mappings=True)
    print(config_str)
