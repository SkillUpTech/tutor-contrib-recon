"""The Recon CLI definitions."""

from pathlib import Path

import click
import cloup


from tutor_recon.override.main import main_config
from tutor_recon.override.template import TemplateOverride
from tutor_recon.util.cli import emit
from tutor_recon.util.constants import (
    RECON_SAVE_STYLED,
)
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Scaffold an override of a tutor template in its entirety.")
@cloup.argument("path", metavar="PATH_RELATIVE_TO_ENV")
@cloup.pass_context
def replace_template(context: cloup.Context, path: str):
    tutor_root, recon_root = root_dirs(context)
    main = main_config(recon_root)
    override = TemplateOverride.for_template(Path(path))
    main.add_override(override)
    override.scaffold(tutor_root, recon_root)
    main.save(recon_root / "main.v.json")
    path_styled = click.style(str(path), fg="blue")
    override_styled = click.style(str(recon_root / override.src), fg="magenta")
    emit(f"Scaffolded {path_styled} at {override_styled} 👍")
    emit(
        f"Change the file to your heart's content, then it will be rendered when you run {RECON_SAVE_STYLED}."
    )


command = replace_template
